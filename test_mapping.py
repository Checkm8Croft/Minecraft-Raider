import sys
from collections import Counter

from obj_parser import load_obj
from voxelizer import voxelize
from schem_exporter import export_schem

def test_mapping():
    path = sys.argv[1] if len(sys.argv) > 1 else "Venice.obj"
    print("[LOAD]", path)
    obj = load_obj(path)
    # Build a tile_map: set specific tiles to distinct blocks
    tile_map = {}
    # Choose a material present
    mats = list(obj["materials"])
    if not mats:
        print("No materials found")
        return
    mat = mats[0]
    print(f"Using material {mat}")
    # Set (0,1) -> bricks, (1,0) -> acacia_wood
    tile_map[(mat, 0, 1)] = "bricks"
    tile_map[(mat, 1, 0)] = "acacia_wood"
    # All other tiles default to stone via fallback in voxelizer (if not found)
    print("[MAPPING] Tile map:", tile_map)
    blocks = voxelize(obj, scale=4, tile_map=tile_map)
    cnt = Counter(b["material"] for b in blocks)
    print("\n=== BLOCK COUNTS ===")
    for k, v in cnt.most_common(10):
        print(f"{k}: {v}")
    # Also compute unique positions for bricks and acacia_wood to see if they are where expected?
    # For simplicity just output counts.
    export_schem(blocks, path)

if __name__ == "__main__":
    test_mapping()