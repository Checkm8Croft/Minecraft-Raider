
import os
from mcschematic import MCSchematic, Version

MAX_DIMENSION = 256
MAX_VOLUME = MAX_DIMENSION ** 3


def export_schem(blocks, filename):
    if not blocks:
        print("[ERROR] No blocks to export.")
        return

    for block in blocks:
        for axis in ("x", "y", "z"):
            value = block.get(axis)

            if not isinstance(value, int):
                print(f"[ERROR] Invalid coordinate {axis}: {value!r}")
                return

    min_x = min(b["x"] for b in blocks)
    min_y = min(b["y"] for b in blocks)
    min_z = min(b["z"] for b in blocks)

    max_x = max(b["x"] for b in blocks)
    max_y = max(b["y"] for b in blocks)
    max_z = max(b["z"] for b in blocks)

    size_x = max_x - min_x + 1
    size_y = max_y - min_y + 1
    size_z = max_z - min_z + 1

    total_volume = size_x * size_y * size_z

    print(
        f"[MEMORY DEBUG] Dimensions: "
        f"{size_x} x {size_y} x {size_z}"
    )
    print(f"[MEMORY DEBUG] Total Volume: {total_volume:,} cells")
    print(f"[MEMORY DEBUG] Actual Blocks: {len(blocks):,}")

    if (
        size_x > MAX_DIMENSION
        or size_y > MAX_DIMENSION
        or size_z > MAX_DIMENSION
        or total_volume > MAX_VOLUME
    ):
        print("[ERROR] Schematic exceeds the safe size limit.")
        print("[ERROR] Export cancelled to prevent MemoryError.")
        return

    # Use the destination selected in the GUI.
    output_path = os.path.abspath(
        os.path.expanduser(filename)
    )
    output_dir = os.path.dirname(output_path)
    clean_name = os.path.splitext(
        os.path.basename(output_path)
    )[0]

    os.makedirs(output_dir, exist_ok=True)

    schem = MCSchematic()
    placed = 0

    for block in blocks:
        x = block["x"] - min_x
        y = block["y"] - min_y
        z = block["z"] - min_z

        material = str(block.get("material", "stone")).strip()

        if not material:
            material = "stone"

        if ":" not in material:
            material = f"minecraft:{material}"

        schem.setBlock((x, y, z), material)
        placed += 1

    schem.save(
        output_dir,
        clean_name,
        version=Version.JE_1_20,
    )

    saved_path = os.path.join(output_dir, clean_name + ".schem")

    print("\n[OK] Export OK")
    print("Blocks:", placed)
    print("File:", saved_path)


if __name__ == "__main__":
    print("Run main.py to launch the application.")
