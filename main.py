
import sys
from collections import Counter

from PySide6.QtWidgets import QApplication, QFileDialog

from obj_parser import load_obj
from voxelizer import voxelize
from schem_exporter import export_schem
import gui_material_mapper


def main():
    app = QApplication.instance()
    owns_app = app is None

    if owns_app:
        app = QApplication(sys.argv[:1])

    path, _ = QFileDialog.getOpenFileName(
        None,
        "Select a Tomb Raider OBJ model",
        "",
        "OBJ files (*.obj);;All files (*)"
    )

    if not path:
        print("[CANCELLED] No OBJ file selected.")
        return

    print("[LOAD]", path)

    obj = load_obj(path)

    # Get mapping from (material, tile_row, tile_col)
    # to Minecraft blocks via GUI.
    print("[MAPPING] Opening GUI to map material tiles to Minecraft blocks...")

    tile_map = gui_material_mapper.run_material_mapper_gui(
        obj["materials"],
        obj.get("material_textures", {})
    )

    if tile_map is None:
        print("[CANCELLED] Material mapping cancelled.")
        return

    print(
        "[MAPPING] Result (first few entries):",
        dict(list(tile_map.items())[:5])
    )

    blocks = voxelize(obj, scale=4, tile_map=tile_map)

    print("\n=== MATERIALS OBJ (original) ===")
    print(obj["materials"])

    print("\n=== BLOCK MATERIALS (mapped) ===")
    print(Counter(b["material"] for b in blocks))

    print("\n=== MC BLOCKS ===")
    print(Counter(b["material"] for b in blocks))

    export_schem(blocks, path)


if __name__ == "__main__":
    main()
