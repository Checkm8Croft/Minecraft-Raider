from mcschematic import MCSchematic, Version
import os

def export_schem(blocks, filename):

    if not blocks:
        print("[ERROR] No blocks")
        return

    schem = MCSchematic()

    clean_name = os.path.basename(filename).replace(".obj", "")

    min_x = min(b["x"] for b in blocks)
    min_y = min(b["y"] for b in blocks)
    min_z = min(b["z"] for b in blocks)

    placed = 0

    for b in blocks:
        x = b["x"] - min_x
        y = b["y"] - min_y
        z = b["z"] - min_z

        schem.setBlock((x, y, z), "minecraft:stone")
        placed += 1

    schem.save(".", clean_name, version=Version.JE_1_20)

    print("\n✔ Export OK")
    print("Blocks:", placed)
    print("File:", clean_name + ".schem")