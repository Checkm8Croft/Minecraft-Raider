import math
from PySide6.QtGui import QImage

TILE_SIZE = 64  # size of each sub-texture in pixels

def voxelize(obj_data, scale=4, tile_map=None):
    """
    Voxelize the object.

    Args:
        obj_data: dict from obj_parser with keys:
            vertices: list of (x,y,z)
            texcoords: list of (u,v)
            normals: list of (nx,ny,nz)
            faces: list of dict with keys:
                verts: tuple of vertex indices
                vt: tuple of texcoord indices or None
                vn: tuple of normal indices or None
                material: material name string
            materials: set of material names
            material_textures: dict mapping material name -> texture file path
        scale: scaling factor for voxel size
        tile_map: dict mapping (material, tile_row, tile_col) -> block name.
                  If None, falls back to using material as block name.

    Returns:
        list of blocks, each dict with keys: x, y, z, material (block name)
    """
    vertices = obj_data["vertices"]
    texcoords = obj_data["texcoords"]
    faces = obj_data["faces"]
    material_textures = obj_data.get("material_textures", {})

    blocks = []
    placed = set()

    def add_block(x, y, z, block_name):
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

    # Cache for texture images
    if not hasattr(voxelize, '_texture_cache'):
        voxelize._texture_cache = {}

    for face in faces:
        verts = face.get("verts", [])
        if len(verts) < 3:
            continue

        material = face.get("material", "stone")
        texture_path = material_textures.get(material)
        texture_image = None
        texture_width = texture_height = 1
        if texture_path:
            if texture_path not in voxelize._texture_cache:
                img = QImage(texture_path)
                voxelize._texture_cache[texture_path] = img if not img.isNull() else None
            texture_image = voxelize._texture_cache[texture_path]
            if texture_image is not None:
                texture_width = texture_image.width()
                texture_height = texture_image.height()

        # Determine block for this face (single block per face based on average UV)
        block_name = "stone"  # default
        vt_tuple = face.get("vt")
        if tile_map is not None and texture_image is not None and vt_tuple is not None:
            # Gather UVs for each vertex in the face
            us = []
            vs = []
            for vi in verts:
                # vi is vertex index
                vt_index = vt_tuple[verts.index(vi)]  # position in vt tuple
                if vt_index is not None and vt_index < len(texcoords):
                    vt = texcoords[vt_index]
                    if vt is not None:
                        u, v = vt
                        us.append(u)
                        vs.append(v)
            if us and vs:
                u_avg = sum(us) / len(us)
                v_avg = sum(vs) / len(vs)
                # Clamp to [0,1]
                u_avg = max(0.0, min(1.0, u_avg))
                v_avg = max(0.0, min(1.0, v_avg))
                # Flip V to match image coordinate space (V=0 is top)
                v_avg = 1.0 - v_avg
                # Compute tile coordinates
                num_tiles_x = texture_width // TILE_SIZE
                num_tiles_y = texture_height // TILE_SIZE
                if num_tiles_x > 0 and num_tiles_y > 0:
                    tile_col = min(int(u_avg * num_tiles_x), num_tiles_x - 1)
                    tile_row = min(int(v_avg * num_tiles_y), num_tiles_y - 1)
                    block_name = tile_map.get((material, tile_row, tile_col), "stone")
                else:
                    # No tiles fit; fall back to (0,0)
                    block_name = tile_map.get((material, 0, 0), "stone")
            else:
                block_name = tile_map.get((material, 0, 0), "stone")
        else:
            # Fallback to material-only mapping (tile (0,0))
            if tile_map is not None:
                block_name = tile_map.get((material, 0, 0), "stone")
            else:
                block_name = material

        # Get scaled vertices for voxelisation
        scaled_verts = []
        for vi in verts:
            v = vertices[vi]
            scaled_verts.append((v[0]*scale, v[1]*scale, v[2]*scale))

        # Triangulate fan and voxelise
        v0 = scaled_verts[0]
        for i in range(1, len(scaled_verts)-1):
            v1 = scaled_verts[i]
            v2 = scaled_verts[i+1]

            steps = 4
            for a in range(steps + 1):
                for b in range(steps + 1 - a):
                    t1 = a / steps
                    t2 = b / steps
                    t3 = 1 - t1 - t2

                    x = v0[0]*t3 + v1[0]*t1 + v2[0]*t2
                    y = v0[1]*t3 + v1[1]*t1 + v2[1]*t2
                    z = v0[2]*t3 + v1[2]*t1 + v2[2]*t2

                    px = int(round(x))
                    py = int(round(y))
                    pz = int(round(z))

                    add_block(px, py, pz, block_name)

    return blocks