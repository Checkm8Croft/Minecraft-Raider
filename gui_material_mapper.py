import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import json

try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QComboBox, QScrollArea, QGridLayout, QSpacerItem, QSizePolicy,
        QMessageBox, QFileDialog, QGroupBox
    )
    from PySide6.QtGui import QPixmap, QImage
    from PySide6.QtCore import Qt, QSize
except Exception as e:
    # PySide6 not installed; fallback to simple console input
    print("PySide6 not available, falling back to console input for material mapping:", e)
    PySide6Available = False
else:
    PySide6Available = True

# Function to get Minecraft blocks from minecraft-data package
def _get_minecraft_blocks(version="1.19.2"):
    """Return a list of Minecraft block identifiers (without 'minecraft:' prefix)."""
    try:
        # Import here to handle missing package gracefully
        import minecraft_data
        # Construct path to blocks.json for the specified version
        # Structure: minecraft_data/data/data/pc/{version}/blocks.json
        base_path = os.path.join(os.path.dirname(minecraft_data.__file__), 'data', 'data', 'pc')
        version_path = os.path.join(base_path, version, 'blocks.json')

        if os.path.exists(version_path):
            with open(version_path, 'r', encoding='utf-8') as f:
                blocks_data = json.load(f)

            # Extract block names
            block_names = set()
            # The blocks.json structure appears to be an array of objects or a dict
            if isinstance(blocks_data, list):
                for block in blocks_data:
                    if isinstance(block, dict):
                        # Try different possible keys for block name
                        name = block.get('name') or block.get('id') or block.get('blockName')
                        if name and isinstance(name, str):
                            # Remove minecraft: prefix if present
                            if name.startswith('minecraft:'):
                                name = name[10:]
                            block_names.add(name)
            elif isinstance(blocks_data, dict):
                # If it's a dictionary, keys might be block names
                for key in blocks_data.keys():
                    if isinstance(key, str) and not key.startswith('_'):
                        # Clean up the key
                        name = key
                        if name.startswith('minecraft:'):
                            name = name[10:]
                        block_names.add(name)

            if block_names:
                return sorted(block_names)
            else:
                raise ValueError("No block names found in blocks.json")
        else:
            raise FileNotFoundError(f"Blocks file not found for version {version}")
    except Exception as e:
        print(f"Failed to load minecraft-data for version {version}: {e}")
        # Fallback to a basic list so GUI still works
        return ["stone", "dirt", "grass_block", "oak_log", "cobblestone",
                "spruce_log", "birch_log", "jungle_log", "acacia_log",
                "dark_oak_log", "stone_bricks", "granite", "diorite",
                "andesite", "polished_granite", "polished_diorite",
                "polished_andesite", "cobblestone", "mossy_cobblestone"]

# Get the block list
MINECRAFT_BLOCKS = _get_minecraft_blocks()

TILE_SIZE = 64  # assume each sub-texture is 64x64 pixels


def run_material_mapper_gui(materials: set, material_textures: dict) -> dict:
    """
    Launches a PySide6 GUI to map each tile of each material's texture to a Minecraft block.
    Returns dict mapping (material, tile_row, tile_col) -> block name.
    If PySide6 is not available, falls back to console input (material-only mapping).
    """
    if not PySide6Available:
        return _fallback_console_mapper(materials, material_textures)

    app = QApplication.instance() or QApplication([])
    win = QWidget()
    win.setWindowTitle("Material Tile to Minecraft Block Mapper")
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Select a Minecraft block for each texture tile (64x64)."))
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_content = QWidget()
    outer_layout = QVBoxLayout()
    scroll_content.setLayout(outer_layout)
    scroll.setWidget(scroll_content)
    layout.addWidget(scroll)

    # Store combo boxes: dict[(material, row, col)] -> QComboBox
    combos = {}
    # Result mapping
    result = {}

    row = 0
    for mat in sorted(materials):
        tex_path = material_textures.get(mat)
        group = QGroupBox(f"Material: {mat}")
        group_layout = QVBoxLayout()
        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(200, 200)
        thumb_label.setStyleSheet("border: 1px solid gray;")
        if tex_path and os.path.isfile(tex_path):
            pixmap = QPixmap(tex_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb_label.setPixmap(pixmap)
            else:
                thumb_label.setText("Failed\nto load")
        else:
            thumb_label.setText("No texture")
        group_layout.addWidget(thumb_label)

        # Determine tile grid
        cols = rows = 0
        if tex_path and os.path.isfile(tex_path):
            img = QImage(tex_path)
            if not img.isNull():
                width = img.width()
                height = img.height()
                cols = width // TILE_SIZE
                rows = height // TILE_SIZE
                if cols == 0 or rows == 0:
                    cols = rows = 1  # fallback to single tile
            else:
                cols = rows = 1
        else:
            cols = rows = 1

        # Create grid of combo boxes
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
                grid.addWidget(label, r+1, c*2)
                grid.addWidget(combo, r+1, c*2+1)
                combos[(mat, r, c)] = combo
        group_layout.addLayout(grid)
        group.setLayout(group_layout)
        outer_layout.addWidget(group)
        row += 1

    # Buttons
    btn_layout = QHBoxLayout()
    btn_ok = QPushButton("OK")
    btn_cancel = QPushButton("Cancel")
    btn_layout.addWidget(btn_ok)
    btn_layout.addWidget(btn_cancel)
    layout.addLayout(btn_layout)

    win.setLayout(layout)
    win.resize(900, 700)
    win.show()

    def on_ok():
        for (mat, r, c), combo in combos.items():
            block = combo.currentText().strip()
            if block:
                result[(mat, r, c)] = block
            else:
                result[(mat, r, c)] = "stone"
        win.close()
        app.quit()

    def on_cancel():
        # Default mapping: stone for all tiles
        for (mat, r, c) in combos.keys():
            result[(mat, r, c)] = "stone"
        win.close()
        app.quit()

    btn_ok.clicked.connect(on_ok)
    btn_cancel.clicked.connect(on_cancel)

    # Handle window close (X) as cancel
    def on_close(event):
        # Treat as cancel: keep default mapping
        win.close()
        app.quit()
    win.closeEvent = on_close

    app.exec()
    return result


def _fallback_console_mapper(materials: set, material_textures: dict) -> dict:
    """Simple console-based fallback when PySide6 not available."""
    print("PySide6 not available. Using console mapping.")
    print("Available materials:", ", ".join(sorted(materials)))
    print("Enter Minecraft block name for each material (empty for default 'stone'):")
    mapping = {}
    for mat in sorted(materials):
        tex = material_textures.get(mat)
        tex_info = f" (texture: {tex})" if tex else " (no texture)"
        ans = input(f"Material '{mat}'{tex_info}: ").strip()
        if ans:
            mapping[mat] = ans
        else:
            mapping[mat] = "stone"
    # Convert to tile map with single tile (0,0)
    tile_map = {}
    for mat, block in mapping.items():
        tile_map[(mat, 0, 0)] = block
    return tile_map


if __name__ == "__main__":
    # For testing: dummy data
    test_materials = {"material1", "material2"}
    test_textures = {"material1": None, "material2": None}
    mapping = run_material_mapper_gui(test_materials, test_textures)
    print("Mapping result:", mapping)