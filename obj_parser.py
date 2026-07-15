import os

def load_obj(filepath):
    """
    Load a Wavefront OBJ file.
    Returns a dict with keys:
        vertices: list of (x, y, z) tuples
        texcoords: list of (u, v) tuples
        normals: list of (nx, ny, nz) tuples
        faces: list of dict with keys "verts": tuple of vertex indices (0-based),
               "vt": tuple of texcoord indices or None,
               "vn": tuple of normal indices or None,
               "material": material name string
        materials: set of material names used
        material_textures: dict mapping material name -> texture file path (or None)
    """
    vertices = []
    texcoords = []
    normals = []
    faces = []
    materials = set()
    material_textures = {}

    current_material = None

    # Determine directory of obj file for resolving relative paths
    obj_dir = os.path.dirname(os.path.abspath(filepath))

    def parse_face_vertex(v):
        # v is a string like "1", "1/1", "1//1", "1/1/1"
        parts = v.split('/')
        v_idx = int(parts[0]) - 1 if parts[0] else None
        vt_idx = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else None
        vn_idx = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else None
        return (v_idx, vt_idx, vn_idx)

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if not parts:
                continue

            if parts[0] == 'v':  # vertex
                vertices.append(tuple(map(float, parts[1:4])))
            elif parts[0] == 'vt':  # texture coordinate
                texcoords.append(tuple(map(float, parts[1:3])))
            elif parts[0] == 'vn':  # normal
                normals.append(tuple(map(float, parts[1:4])))
            elif parts[0] == 'f':  # face
                # Expect at least 3 vertices
                verts = []
                vts = []
                vns = []
                for comp in parts[1:]:
                    v_idx, vt_idx, vn_idx = parse_face_vertex(comp)
                    verts.append(v_idx)
                    vts.append(vt_idx)
                    vns.append(vn_idx)
                # Triangulate by fan (first vertex)
                if len(verts) >= 3:
                    base_v, base_vt, base_vn = verts[0], vts[0], vns[0]
                    for i in range(1, len(verts)-1):
                        faces.append({
                            "verts": (base_v, verts[i], verts[i+1]),
                            "vt": (base_vt, vts[i], vts[i+1]) if any(v is not None for v in (base_vt, vts[i], vts[i+1])) else None,
                            "vn": (base_vn, vns[i], vns[i+1]) if any(v is not None for v in (base_vn, vns[i], vns[i+1])) else None,
                            "material": current_material
                        })
                # If less than 3 vertices, ignore
            elif parts[0] == 'usemtl':
                current_material = parts[1]
                materials.add(current_material)
            elif parts[0] == 'mtllib':
                mtl_file = parts[1]
                mtl_path = os.path.join(obj_dir, mtl_file)
                if os.path.isfile(mtl_path):
                    parse_mtl(mtl_path, material_textures)
            # ignore other lines

    return {
        'vertices': vertices,
        'texcoords': texcoords,
        'normals': normals,
        'faces': faces,
        'materials': materials,
        'material_textures': material_textures
    }

def parse_feature(v):
    parts = v.split('/')
    v_idx = int(parts[0]) - 1 if parts[0] else None
    vt_idx = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else None
    vn_idx = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else None
    return (v_idx, vt_idx, vn_idx)

def parse_mtl(mtl_path, material_textures):
    """
    Parse an MTL file to extract texture maps (map_Kd) for each material.
    Updates material_textures dict in-place.
    """
    current_material = None
    with open(mtl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if not parts:
                continue
            if parts[0] == 'newmtl':
                current_material = parts[1]
                # Ensure entry exists
                if current_material not in material_textures:
                    material_textures[current_material] = None
            elif parts[0] == 'map_Kd' and current_material is not None:
                # texture filename (may have options like -bm etc.)
                # Assume last token is the filename
                tex_name = parts[-1]
                # Build absolute path
                tex_path = os.path.join(os.path.dirname(os.path.abspath(mtl_path)), tex_name)
                material_textures[current_material] = tex_path
            # ignore other properties