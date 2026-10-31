
import sys
from collections import Counter

from PySide6.QtWidgets import QApplication, QFileDialog
from numpy import rint

from obj_parser import load_obj
from voxelizer import voxelize
from schem_exporter import export_schem
import gui_material_mapper


def main():
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv[:1])

    path, _ = QFileDialog.getOpenFileName(
        None,
        "Select a Tomb Raider OBJ model",
        "",
        "OBJ files (*.obj);;All files (*)",
    )

    if not path:
        print("[CANCELLED] No OBJ file selected.")
        return

    print("[LOAD]", path)

    obj = load_obj(path)
    print("\n=== TEST OBJ OBJECTS ===")
    print(set(face.get("object") for face in obj["faces"]))

    print("[MAPPING] Opening material mapper and output selection...")

    tile_map, output_path = (
        gui_material_mapper.run_material_mapper_gui(
            obj["materials"],
            obj.get("material_textures", {}),
            input_path=path,
        )
    )

    if tile_map is None or output_path is None:
        print("[CANCELLED] Conversion cancelled.")
        return

    print(
        "[MAPPING] Result (first few entries):",
        dict(list(tile_map.items())[:5]),
    )

    blocks = voxelize(obj, scale=4, tile_map=tile_map)

    print("\n=== MATERIALS OBJ (original) ===")
    print(obj["materials"])

    print("\n=== BLOCK MATERIALS (mapped) ===")
    print(Counter(b["material"] for b in blocks))

    print("\n=== MC BLOCKS ===")
    print(Counter(b["material"] for b in blocks))

    export_schem(blocks, output_path)


if __name__ == "__main__":
    main()
