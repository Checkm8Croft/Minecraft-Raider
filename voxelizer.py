import math


def get_normal(v0, v1, v2):
    ax, ay, az = v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]
    bx, by, bz = v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]

    nx = ay*bz - az*by
    ny = az*bx - ax*bz
    nz = ax*by - ay*bx

    l = math.sqrt(nx*nx + ny*ny + nz*nz)
    if l == 0:
        return (0, 0, 0)

    return (nx/l, ny/l, nz/l)


def classify_face(n):
    nx, ny, nz = n

    if ny > 0.7:
        return "floor"
    if ny < -0.7:
        return "ceiling"
    if abs(nx) > 0.7 or abs(nz) > 0.7:
        return "wall"
    return "slope"


def sample(v0, v1, v2, res=2):
    out = []

    for i in range(res+1):
        for j in range(res+1-i):

            t1 = i/res
            t2 = j/res
            t3 = 1 - t1 - t2

            x = v0[0]*t3 + v1[0]*t1 + v2[0]*t2
            y = v0[1]*t3 + v1[1]*t1 + v2[1]*t2
            z = v0[2]*t3 + v1[2]*t1 + v2[2]*t2

            out.append((int(round(x)), int(round(y)), int(round(z))))

    return out


def voxelize(obj, scale=4):
    verts = obj["vertices"]
    faces = obj["faces"]

    blocks = []
    used = set()

    def add(x, y, z, mat, t):
        p = (x, y, z)
        if p in used:
            return
        used.add(p)

        blocks.append({
            "x": x,
            "y": y,
            "z": z,
            "material": mat,
            "type": t
        })

    for f in faces:

        idx = f["verts"]
        mat = f.get("material", "unknown")

        if len(idx) < 3:
            continue

        try:
            v0, v1, v2 = [verts[i] for i in idx[:3]]
        except:
            continue

        n = get_normal(v0, v1, v2)
        t = classify_face(n)

        v0 = (v0[0]*scale, v0[1]*scale, v0[2]*scale)
        v1 = (v1[0]*scale, v1[1]*scale, v1[2]*scale)
        v2 = (v2[0]*scale, v2[1]*scale, v2[2]*scale)

        for x, y, z in sample(v0, v1, v2):
            add(x, y, z, mat, t)

    return blocks