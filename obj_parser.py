def load_obj(file_path):
    vertices = []
    faces = []
    materials = set()

    current_material = "unknown"

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # MATERIAL CHANGE
            if line.startswith("usemtl"):
                current_material = line.split(maxsplit=1)[1]
                materials.add(current_material)

            # VERTEX (robusto, niente crash su formati strani)
            elif line.startswith("v "):
                parts = line.split()
                if len(parts) < 4:
                    continue

                try:
                    x, y, z = map(float, parts[1:4])
                    vertices.append((x, y, z))
                except:
                    continue

            # FACE (supporta f 1/2/3, f 1//3 ecc.)
            elif line.startswith("f "):
                parts = line.split()[1:]
                idxs = []

                for p in parts:
                    try:
                        idxs.append(int(p.split("/")[0]) - 1)
                    except:
                        continue

                if len(idxs) >= 3:
                    faces.append({
                        "verts": idxs,
                        "material": current_material
                    })

    return {
        "vertices": vertices,
        "faces": faces,
        "materials": list(materials)
    }