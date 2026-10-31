
import math
from PySide6.QtGui import QImage

TILE_SIZE = 64

# Dimensione massima consentita per ciascun asse dello schematic.
# Evita coordinate enormi e MemoryError durante l'esportazione.
MAX_DIMENSION = 256


def voxelize(obj_data, scale=4, tile_map=None):
    """
    Converts OBJ geometry into Minecraft blocks.

    Coordinates are translated to the origin and scaled down
    automatically when the model would exceed MAX_DIMENSION.

    Args:
        obj_data: dict containing vertices, texcoords, faces
                   and optionally material_textures.
        scale: preferred scaling factor.
        tile_map: optional mapping from material/tile to block.

    Returns:
        List of dictionaries containing x, y, z and material.
    """
    vertices = obj_data.get("vertices", [])
    texcoords = obj_data.get("texcoords", [])
    faces = obj_data.get("faces", [])
    material_textures = obj_data.get("material_textures", {})

    if not vertices or not faces:
        print("[ERROR] OBJ contains no vertices or faces.")
        return []

    if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale must be a finite number greater than zero")

    # Validate vertex coordinates before calculating the bounding box.
    valid_vertices = []
    for vertex in vertices:
        if vertex is None or len(vertex) < 3:
            continue

        try:
            x, y, z = float(vertex[0]), float(vertex[1]), float(vertex[2])
        except (TypeError, ValueError):
            continue

        if math.isfinite(x) and math.isfinite(y) and math.isfinite(z):
            valid_vertices.append((x, y, z))
        else:
            valid_vertices.append(None)

    if not valid_vertices or all(v is None for v in valid_vertices):
        print("[ERROR] OBJ contains no valid finite vertex coordinates.")
        return []

    # Keep the original vertex indices intact.
    valid_coordinates = [v for v in valid_vertices if v is not None]

    min_x = min(v[0] for v in valid_coordinates)
    min_y = min(v[1] for v in valid_coordinates)
    min_z = min(v[2] for v in valid_coordinates)

    max_x = max(v[0] for v in valid_coordinates)
    max_y = max(v[1] for v in valid_coordinates)
    max_z = max(v[2] for v in valid_coordinates)

    extent_x = max_x - min_x
    extent_y = max_y - min_y
    extent_z = max_z - min_z
    max_extent = max(extent_x, extent_y, extent_z)

    # Preserve the requested scale unless the model would be too large.
    if max_extent > 0:
        effective_scale = min(
            float(scale),
            (MAX_DIMENSION - 1) / max_extent
        )
    else:
        effective_scale = float(scale)

    print(f"[VOXELIZER] Original size: "
          f"{extent_x:.3f} x {extent_y:.3f} x {extent_z:.3f}")
    print(f"[VOXELIZER] Requested scale: {scale}")
    print(f"[VOXELIZER] Effective scale: {effective_scale:.8f}")

    # Translate and scale every vertex consistently.
    scaled_vertices = []
    for vertex in valid_vertices:
        if vertex is None:
            scaled_vertices.append(None)
            continue

        x, y, z = vertex
        scaled_vertices.append((
            (x - min_x) * effective_scale,
            (y - min_y) * effective_scale,
            (z - min_z) * effective_scale
        ))

    blocks = []
    placed = set()

    def add_block(x, y, z, block_name):
        # Final safety limit for individual coordinates.
        if not (
            0 <= x < MAX_DIMENSION
            and 0 <= y < MAX_DIMENSION
            and 0 <= z < MAX_DIMENSION
        ):
            return

        pos = (x, y, z)
        if pos in placed:
            return

        placed.add(pos)
        blocks.append({
            "x": x,
            "y": y,
            "z": z,
            "material": block_name
        })

    # Cache loaded texture images.
    if not hasattr(voxelize, "_texture_cache"):
        voxelize._texture_cache = {}

    for face in faces:
        verts = face.get("verts", [])
        if len(verts) < 3:
            continue

        # Skip malformed faces instead of crashing.
        if any(
            not isinstance(vi, int)
            or vi < 0
            or vi >= len(scaled_vertices)
            or scaled_vertices[vi] is None
            for vi in verts
        ):
            continue

        material = face.get("material", "stone")
        texture_path = material_textures.get(material)
        texture_image = None
        texture_width = 1
        texture_height = 1

        if texture_path:
            if texture_path not in voxelize._texture_cache:
                img = QImage(texture_path)
                voxelize._texture_cache[texture_path] = (
                    img if not img.isNull() else None
                )

            texture_image = voxelize._texture_cache[texture_path]

            if texture_image is not None:
                texture_width = texture_image.width()
                texture_height = texture_image.height()

        # Determine one block material for this face.
        block_name = "stone"
        vt_tuple = face.get("vt")

        if (
            tile_map is not None
            and texture_image is not None
            and vt_tuple is not None
        ):
            us = []
            vs = []

            for index, vi in enumerate(verts):
                if index >= len(vt_tuple):
                    continue

                vt_index = vt_tuple[index]

                if (
                    vt_index is not None
                    and isinstance(vt_index, int)
                    and 0 <= vt_index < len(texcoords)
                ):
                    vt = texcoords[vt_index]

                    if vt is not None and len(vt) >= 2:
                        try:
                            u, v = float(vt[0]), float(vt[1])
                        except (TypeError, ValueError):
                            continue

                        if math.isfinite(u) and math.isfinite(v):
                            us.append(u)
                            vs.append(v)

            if us and vs:
                u_avg = max(0.0, min(1.0, sum(us) / len(us)))
                v_avg = max(0.0, min(1.0, sum(vs) / len(vs)))
                v_avg = 1.0 - v_avg

                num_tiles_x = texture_width // TILE_SIZE
                num_tiles_y = texture_height // TILE_SIZE

                if num_tiles_x > 0 and num_tiles_y > 0:
                    tile_col = min(
                        int(u_avg * num_tiles_x), num_tiles_x - 1
                    )
                    tile_row = min(
                        int(v_avg * num_tiles_y), num_tiles_y - 1
                    )
                    block_name = tile_map.get(
                        (material, tile_row, tile_col), "stone"
                    )
                else:
                    block_name = tile_map.get(
                        (material, 0, 0), "stone"
                    )
            else:
                block_name = tile_map.get(
                    (material, 0, 0), "stone"
                )
        elif tile_map is not None:
            block_name = tile_map.get(
                (material, 0, 0), "stone"
            )
        else:
            block_name = material

        # Use normalized vertices for voxelization.
        face_vertices = [scaled_vertices[vi] for vi in verts]
        v0 = face_vertices[0]

        # Triangulate polygons as a triangle fan.
        for i in range(1, len(face_vertices) - 1):
            v1 = face_vertices[i]
            v2 = face_vertices[i + 1]

            edge1 = math.dist(v0, v1)
            edge2 = math.dist(v1, v2)
            edge3 = math.dist(v2, v0)

            max_edge = max(edge1, edge2, edge3)

            steps = max(4, math.ceil(max_edge * 2))
            
            for a in range(steps + 1):
                for b in range(steps + 1 - a):
                    t1 = a / steps
                    t2 = b / steps
                    t3 = 1.0 - t1 - t2

                    x = v0[0] * t3 + v1[0] * t1 + v2[0] * t2
                    y = v0[1] * t3 + v1[1] * t1 + v2[1] * t2
                    z = v0[2] * t3 + v1[2] * t1 + v2[2] * t2

                    px = int(round(x))
                    py = int(round(y))
                    pz = int(round(z))

                    add_block(px, py, pz, block_name)

    print(f"[VOXELIZER] Generated blocks: {len(blocks):,}")
    return blocks
