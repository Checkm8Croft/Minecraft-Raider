import math
from PySide6.QtGui import QImage

TILE_SIZE = 64  # size of each sub‑texture in pixels

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

        # Get VT and VN tuples
        vt_tuple = face.get("vt")
        vn_tuple = face.get("vn")

        # Helper to get VT for a vertex index in face
        def get_vt(face_idx):
            if vt_tuple is None:
                return None
            vt_index = vt_tuple[face_idx]
            if vt_index is None:
                return None
            return texcoords[vt_index]

        # Triangulate fan
        v0_idx = verts[0]
        v0 = vertices[v0_idx]
        v0 = (v0[0]*scale, v0[1]*scale, v0[2]*scale)
        vt0 = get_vt(0)

        for i in range(1, len(verts)-1):
            v1_idx = verts[i]
            v2_idx = verts[i+1]
            v1 = vertices[v1_idx]
            v2 = vertices[v2_idx]
            v1 = (v1[0]*scale, v1[1]*scale, v1[2]*scale)
            v2 = (v2[0]*scale, v2[1]*scale, v2[2]*scale)
            vt1 = get_vt(i)
            vt2 = get_vt(i+1)

            # Determine block for this triangle
            block_name = "stone"  # default
            if tile_map is not None:
                if texture_image is not None and vt0 is not None and vt1 is not None and vt2 is not None:
                    # Average UV of triangle
                    u = (vt0[0] + vt1[0] + vt2[0]) / 3.0
                    v = (vt0[1] + vt1[1] + vt2[1]) / 3.0
                    # Clamp to [0,1]
                    u = max(0.0, min(1.0, u))
                    v = max(0.0, min(1.0, v))
                    # Tile coordinates
                    tu = int(u * texture_width // TILE_SIZE)
                    tv = int(v * texture_height // TILE_SIZE)
                    block_name = tile_map.get((material, tu, tv), "stone")
                else:
                    # Fallback to material-only mapping (tile (0,0))
                    block_name = tile_map.get((material, 0, 0), "stone")
            else:
                # No tile_map provided, use material as block name (original behavior)
                block_name = material

            # Voxelize the triangle with density
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