import os
from pathlib import Path


def load_obj(filepath):
    """
    Load a Wavefront OBJ file.

    Returns:
        vertices
        texcoords
        normals
        faces
        materials
        material_textures
    """
    vertices = []
    texcoords = []
    normals = []
    faces = []
    materials = set()
    material_textures = {}

    current_material = None
    current_object = None

    obj_path = Path(filepath).expanduser().resolve()
    obj_dir = obj_path.parent

    def parse_face_vertex(v):
        parts = v.split('/')

        v_idx = int(parts[0]) - 1 if parts[0] else None
        vt_idx = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else None
        vn_idx = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else None

        return v_idx, vt_idx, vn_idx

    with obj_path.open('r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if not parts:
                continue
            if parts[0] == 'o':
                current_object = ' '.join(parts[1:])
                continue

            if parts[0] == 'v':
                vertices.append(tuple(map(float, parts[1:4])))

            elif parts[0] == 'vt':
                texcoords.append(tuple(map(float, parts[1:3])))

            elif parts[0] == 'vn':
                normals.append(tuple(map(float, parts[1:4])))

            elif parts[0] == 'f':
                verts = []
                vts = []
                vns = []

                for comp in parts[1:]:
                    v_idx, vt_idx, vn_idx = parse_face_vertex(comp)
                    verts.append(v_idx)
                    vts.append(vt_idx)
                    vns.append(vn_idx)

                if len(verts) >= 3:
                    base_v = verts[0]
                    base_vt = vts[0]
                    base_vn = vns[0]

                    for i in range(1, len(verts) - 1):
                        face_vt = (base_vt, vts[i], vts[i + 1])
                        face_vn = (base_vn, vns[i], vns[i + 1])

                        faces.append({
                            "verts": (base_v, verts[i], verts[i + 1]),
                            "vt": face_vt if any(v is not None for v in face_vt) else None,
                            "vn": face_vn if any(v is not None for v in face_vn) else None,
                            "material": current_material,
                            "object": current_object
                        })

            elif parts[0] == 'usemtl':
                current_material = ' '.join(parts[1:])
                materials.add(current_material)


            elif parts[0] == 'mtllib':
                # Preserve filenames containing spaces.
                mtl_filename = line[len('mtllib'):].strip()

                # Remove optional surrounding quotes.
                if (
                    len(mtl_filename) >= 2
                    and mtl_filename[0] == '"'
                    and mtl_filename[-1] == '"'
                ):
                    mtl_filename = mtl_filename[1:-1]

                mtl_path = os.path.join(obj_dir, mtl_filename)

                print("\n[MTL DEBUG] Searching:", mtl_path)
                print("[MTL DEBUG] Exists:", os.path.isfile(mtl_path))

                if os.path.isfile(mtl_path):
                    parse_mtl(mtl_path, material_textures)
                else:
                    print("[MTL ERROR] MTL file not found!")

    return {
        'vertices': vertices,
        'texcoords': texcoords,
        'normals': normals,
        'faces': faces,
        'materials': materials,
        'material_textures': material_textures
    }



def parse_mtl(mtl_path, material_textures):
    """
    Parse an MTL file and resolve texture paths
    relative to the MTL file directory.
    """
    from pathlib import Path
    import shlex

    mtl_path = Path(mtl_path).expanduser().resolve()
    mtl_dir = mtl_path.parent

    current_material = None

    with mtl_path.open('r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            try:
                parts = shlex.split(line)
            except ValueError:
                continue

            if not parts:
                continue

            if parts[0] == 'newmtl':
                current_material = ' '.join(parts[1:])
                material_textures[current_material] = None

            elif parts[0] == 'map_Kd' and current_material is not None:
                tex_name = parts[-1]

                tex_path = (mtl_dir / tex_name).resolve()

                print("\n[TEXTURE DEBUG]")
                print("Material:", current_material)
                print("MTL:", mtl_path)
                print("Texture:", tex_path)
                print("Exists:", tex_path.is_file())

                material_textures[current_material] = str(tex_path)
