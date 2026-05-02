from mcschematic import MCSchematic, Version
import os


def export_schem(blocks, filename):

    schem = MCSchematic()

    name = os.path.basename(filename).replace(".obj", "")

    min_x = min(b["x"] for b in blocks)
    min_y = min(b["y"] for b in blocks)
    min_z = min(b["z"] for b in blocks)

    for b in blocks:

        x = b["x"] - min_x
        y = b["y"] - min_y
        z = b["z"] - min_z

        mat = b.get("mc_block", "stone")

        schem.setBlock((x, y, z), f"minecraft:{mat}")

    schem.save(".", name, version=Version.JE_1_20)

    print("[EXPORT] OK ->", name + ".schem")