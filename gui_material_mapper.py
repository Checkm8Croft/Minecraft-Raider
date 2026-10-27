
import os
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QComboBox,
        QScrollArea,
        QGridLayout,
        QMessageBox,
        QFileDialog,
        QGroupBox,
        QLineEdit,
    )
    from PySide6.QtGui import QPixmap, QImage
    from PySide6.QtCore import Qt

    PySide6Available = True

except Exception as e:
    print("PySide6 is not available:", e)
    PySide6Available = False


def _get_minecraft_blocks(version="1.19.2"):
    """Return Minecraft block identifiers without the minecraft: prefix."""
    try:
        import minecraft_data
        import json

        base_path = os.path.join(
            os.path.dirname(minecraft_data.__file__),
            "data",
            "data",
            "pc",
        )
        version_path = os.path.join(base_path, version, "blocks.json")

        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as f:
                blocks_data = json.load(f)

            block_names = set()

            if isinstance(blocks_data, list):
                for block in blocks_data:
                    if isinstance(block, dict):
                        name = (
                            block.get("name")
                            or block.get("id")
                            or block.get("blockName")
                        )

                        if isinstance(name, str) and name:
                            if name.startswith("minecraft:"):
                                name = name[len("minecraft:"):]

                            block_names.add(name)

            elif isinstance(blocks_data, dict):
                for name in blocks_data:
                    if isinstance(name, str) and not name.startswith("_"):
                        if name.startswith("minecraft:"):
                            name = name[len("minecraft:"):]

                        block_names.add(name)

            if block_names:
                return sorted(block_names)

            raise ValueError("No block names found in blocks.json")

        raise FileNotFoundError(
            f"Blocks file not found for Minecraft {version}"
        )

    except Exception as e:
        print(f"Failed to load minecraft-data for {version}: {e}")

        return [
            "stone",
            "dirt",
            "grass_block",
            "oak_log",
            "cobblestone",
            "spruce_log",
            "birch_log",
            "jungle_log",
            "acacia_log",
            "dark_oak_log",
            "stone_bricks",
            "granite",
            "diorite",
            "andesite",
            "polished_granite",
            "polished_diorite",
            "polished_andesite",
            "mossy_cobblestone",
        ]


MINECRAFT_BLOCKS = _get_minecraft_blocks()

TILE_SIZE = 64


def run_material_mapper_gui(
    materials: set,
    material_textures: dict,
    input_path: str = "",
):
    """
    Open the material mapper and output-file selector.

    Returns:
        (tile_map, output_path) on confirmation.
        (None, None) if the user cancels.
    """
    if not PySide6Available:
        return _fallback_console_mapper(
            materials,
            material_textures,
            input_path,
        )

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    # Default output name is based on the selected OBJ.
    if input_path:
        default_output = os.path.splitext(
            os.path.abspath(input_path)
        )[0] + ".schem"
    else:
        default_output = os.path.abspath("output.schem")

    win = QWidget()
    win.setWindowTitle("Material Tile to Minecraft Block Mapper")

    layout = QVBoxLayout(win)

    layout.addWidget(
        QLabel(
            "Select a Minecraft block for each texture tile (64x64)."
        )
    )

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)

    scroll_content = QWidget()
    outer_layout = QVBoxLayout(scroll_content)

    scroll.setWidget(scroll_content)
    layout.addWidget(scroll, 1)

    combos = {}
    result = {}

    for mat in sorted(materials):
        tex_path = material_textures.get(mat)

        group = QGroupBox(f"Material: {mat}")
        group_layout = QVBoxLayout(group)

        thumb_label = QLabel()
        thumb_label.setFixedSize(200, 200)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setStyleSheet("border: 1px solid gray;")

        if tex_path and os.path.isfile(tex_path):
            pixmap = QPixmap(tex_path)

            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    200,
                    200,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                thumb_label.setPixmap(pixmap)
            else:
                thumb_label.setText("Failed to load texture")
        else:
            thumb_label.setText("No texture")

        group_layout.addWidget(thumb_label)

        cols = 1
        rows = 1

        if tex_path and os.path.isfile(tex_path):
            img = QImage(tex_path)

            if not img.isNull():
                cols = max(1, img.width() // TILE_SIZE)
                rows = max(1, img.height() // TILE_SIZE)

        grid = QGridLayout()
        grid.addWidget(QLabel("<b>Tile (row, col)</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Block</b>"), 0, 1)

        for r in range(rows):
            for c in range(cols):
                label = QLabel(f"({r},{c})")

                combo = QComboBox()
                combo.setEditable(True)
                combo.addItems(MINECRAFT_BLOCKS)
                combo.setCurrentText("stone")

                grid.addWidget(label, r + 1, c * 2)
                grid.addWidget(combo, r + 1, c * 2 + 1)

                combos[(mat, r, c)] = combo

        group_layout.addLayout(grid)
        outer_layout.addWidget(group)

    # Output section, below the texture mapping.
    output_group = QGroupBox("Schematic output")
    output_layout = QVBoxLayout(output_group)

    output_layout.addWidget(
        QLabel("Choose where the .schem file will be saved:")
    )

    output_row = QHBoxLayout()

    output_edit = QLineEdit(default_output)
    output_edit.setPlaceholderText("Output file path (.schem)")
    output_row.addWidget(output_edit, 1)

    browse_button = QPushButton("Browse...")
    output_row.addWidget(browse_button)

    output_layout.addLayout(output_row)
    layout.addWidget(output_group)

    def browse_output():
        current_path = output_edit.text().strip() or default_output

        selected_path, _ = QFileDialog.getSaveFileName(
            win,
            "Save Minecraft schematic",
            current_path,
            "Minecraft Schematic (*.schem)",
        )

        if selected_path:
            if not selected_path.lower().endswith(".schem"):
                selected_path += ".schem"

            output_edit.setText(selected_path)

    browse_button.clicked.connect(browse_output)

    # Confirmation buttons.
    btn_layout = QHBoxLayout()

    btn_ok = QPushButton("OK")
    btn_cancel = QPushButton("Cancel")

    btn_layout.addStretch()
    btn_layout.addWidget(btn_ok)
    btn_layout.addWidget(btn_cancel)

    layout.addLayout(btn_layout)

    win.resize(900, 750)

    state = {"confirmed": False}

    def on_ok():
        output_path = output_edit.text().strip()

        if not output_path:
            QMessageBox.warning(
                win,
                "Missing output path",
                "Choose a destination for the schematic file.",
            )
            return

        if not output_path.lower().endswith(".schem"):
            output_path += ".schem"

        output_path = os.path.abspath(
            os.path.expanduser(output_path)
        )

        for (mat, r, c), combo in combos.items():
            block = combo.currentText().strip()
            result[(mat, r, c)] = block or "stone"

        state["confirmed"] = True
        state["output_path"] = output_path
        win.close()

    def on_cancel():
        win.close()

    btn_ok.clicked.connect(on_ok)
    btn_cancel.clicked.connect(on_cancel)

    win.show()
    app.exec()

    if not state["confirmed"]:
        print("[CANCELLED] Material mapping or output selection cancelled.")
        return None, None

    output_path = state["output_path"]

    print("[OUTPUT] Schematic will be saved to:", output_path)

    return result, output_path


def _fallback_console_mapper(
    materials: set,
    material_textures: dict,
    input_path: str = "",
):
    """Console fallback if PySide6 is unavailable."""
    print("PySide6 not available. Using console mapping.")

    mapping = {}

    for mat in sorted(materials):
        tex = material_textures.get(mat)
        tex_info = f" (texture: {tex})" if tex else " (no texture)"

        ans = input(
            f"Material '{mat}'{tex_info} "
            "(empty for stone): "
        ).strip()

        mapping[(mat, 0, 0)] = ans or "stone"

    if input_path:
        default_output = os.path.splitext(
            os.path.abspath(input_path)
        )[0] + ".schem"
    else:
        default_output = os.path.abspath("output.schem")

    output_path = input(
        f"Output .schem path [{default_output}]: "
    ).strip()

    output_path = output_path or default_output

    if not output_path.lower().endswith(".schem"):
        output_path += ".schem"

    return mapping, os.path.abspath(output_path)


if __name__ == "__main__":
    test_materials = {"material1", "material2"}
    test_textures = {"material1": None, "material2": None}

    mapping, output_path = run_material_mapper_gui(
        test_materials,
        test_textures,
    )

    print("Mapping result:", mapping)
    print("Output path:", output_path)
