import sys
from collections import Counter

from obj_parser import load_obj
from voxelizer import voxelize
from material_mapper import map_material
from schem_exporter import export_schem


def main():

    path = sys.argv[1]
    print("[LOAD]", path)

    obj = load_obj(path)

    blocks = voxelize(obj)

    # APPLY MTL → MC
    for b in blocks:
        b["mc_block"] = map_material(b["material"])

    print("\n=== MATERIALS OBJ ===")
    print(obj["materials"])

    print("\n=== BLOCK MATERIALS ===")
    print(Counter(b["material"] for b in blocks))

    print("\n=== MC BLOCKS ===")
    print(Counter(b["mc_block"] for b in blocks))

    export_schem(blocks, path)


if __name__ == "__main__":
    main()