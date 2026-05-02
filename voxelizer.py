import math

def voxelize(obj_data, scale=4):
    vertices = obj_data["vertices"]
    faces = obj_data["faces"]

    blocks = []
    placed = set()

    def add_block(x, y, z):
        pos = (x, y, z)
        if pos in placed:
            return
        placed.add(pos)

        blocks.append({
            "x": x,
            "y": y,
            "z": z,
            "material": "stone"
        })

    for face in faces:

        idxs = face.get("verts", [])
        if len(idxs) < 3:
            continue

        # 🔥 IMPORTANTE: usa TUTTI i vertici (non solo 3)
        verts = []
        for i in idxs:
            try:
                v = vertices[i]
                verts.append((v[0]*scale, v[1]*scale, v[2]*scale))
            except:
                continue

        if len(verts) < 3:
            continue

        # triangolazione fan (fix fondamentale)
        v0 = verts[0]

        for i in range(1, len(verts) - 1):
            v1 = verts[i]
            v2 = verts[i + 1]

            # densità migliore
            steps = 4

            for a in range(steps + 1):
                for b in range(steps + 1 - a):

                    t1 = a / steps
                    t2 = b / steps
                    t3 = 1 - t1 - t2

                    x = v0[0]*t3 + v1[0]*t1 + v2[0]*t2
                    y = v0[1]*t3 + v1[1]*t1 + v2[1]*t2
                    z = v0[2]*t3 + v1[2]*t1 + v2[2]*t2

                    # 🔥 SNAP DOPO (NON prima)
                    add_block(
                        int(round(x)),
                        int(round(y)),
                        int(round(z))
                    )

    return blocks