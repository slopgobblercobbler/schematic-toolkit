"""ASCII cross-section diagrams and layer visualization."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.region import Region
from schematic_toolkit.models.schematic import Schematic

# Preset recognizable characters for common Minecraft blocks
DEFAULT_CHAR_MAP: Dict[str, str] = {
    "minecraft:air": ".",
    "minecraft:cave_air": ".",
    "minecraft:void_air": ".",
    "minecraft:stone": "#",
    "minecraft:cobblestone": "c",
    "minecraft:deepslate": "D",
    "minecraft:cobbled_deepslate": "d",
    "minecraft:dirt": "d",
    "minecraft:grass_block": "G",
    "minecraft:oak_planks": "W",
    "minecraft:spruce_planks": "w",
    "minecraft:birch_planks": "b",
    "minecraft:oak_log": "O",
    "minecraft:oak_leaves": "*",
    "minecraft:glass": "+",
    "minecraft:water": "~",
    "minecraft:flowing_water": "~",
    "minecraft:lava": "%",
    "minecraft:flowing_lava": "%",
    "minecraft:torch": "i",
    "minecraft:redstone_wire": "r",
    "minecraft:redstone_torch": "!",
    "minecraft:chest": "C",
    "minecraft:furnace": "F",
    "minecraft:hopper": "V",
    "minecraft:piston": "P",
    "minecraft:sticky_piston": "p",
    "minecraft:iron_block": "I",
    "minecraft:gold_block": "$",
    "minecraft:diamond_block": "X",
    "minecraft:obsidian": "B",
    "minecraft:tnt": "T",
}

AVAILABLE_SYMBOLS = "1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@&^/\\|"


def build_char_mapping(palette: List[BlockState]) -> Dict[str, str]:
    """Build a collision-free character mapping for all blocks in a palette."""
    char_map: Dict[str, str] = {}
    used_chars = set()

    # Pass 1: Assign from defaults if available
    for state in palette:
        if state.name in DEFAULT_CHAR_MAP:
            char = DEFAULT_CHAR_MAP[state.name]
            if char not in used_chars or state.is_air:
                char_map[state.name] = char
                if not state.is_air:
                    used_chars.add(char)

    # Pass 2: Assign remaining from available symbols
    symbol_idx = 0
    for state in palette:
        if state.name not in char_map:
            # Pick first unused character
            while symbol_idx < len(AVAILABLE_SYMBOLS) and AVAILABLE_SYMBOLS[symbol_idx] in used_chars:
                symbol_idx += 1
            if symbol_idx < len(AVAILABLE_SYMBOLS):
                char = AVAILABLE_SYMBOLS[symbol_idx]
                used_chars.add(char)
                char_map[state.name] = char
                symbol_idx += 1
            else:
                char_map[state.name] = "?"

    return char_map


def render_ascii_layer_y(
    region: Region,
    y: int,
    show_legend: bool = True,
    char_map: Optional[Dict[str, str]] = None,
) -> str:
    """Render a horizontal cross-section at height Y (top-down view).

    X axis runs left-to-right (0 to width - 1).
    Z axis runs top-to-bottom (0 to length - 1).
    """
    if not (0 <= y < region.height):
        raise IndexError(f"Layer Y={y} out of bounds (region height is {region.height}, valid 0..{region.height - 1})")

    if char_map is None:
        char_map = build_char_mapping(region.palette)

    lines: List[str] = []
    lines.append(f"=== Cross-Section: Region '{region.name}' at Layer Y={y} (Size: {region.width}x{region.length}) ===")
    lines.append("")

    # Top coordinate header (X axis)
    header_tens = "    "
    header_ones = "    "
    for x in range(region.width):
        header_tens += str(x // 10) if x >= 10 else " "
        header_ones += str(x % 10)
    lines.append(header_tens)
    lines.append(header_ones)
    lines.append("   +" + "-" * region.width + "+")

    # Grid rows (Z axis)
    blocks_in_layer = set()
    for z in range(region.length):
        row_chars = []
        for x in range(region.width):
            block = region.get_block(x, y, z)
            blocks_in_layer.add(block.name)
            char = char_map.get(block.name, "?")
            row_chars.append(char)
        lines.append(f"{z:2d} |{''.join(row_chars)}| {z}")

    lines.append("   +" + "-" * region.width + "+")
    lines.append(header_ones)
    lines.append("")

    # Legend
    if show_legend:
        lines.append("--- Legend ---")
        sorted_blocks = sorted(blocks_in_layer, key=lambda b: (b in ("minecraft:air", "air"), b))
        for b_name in sorted_blocks:
            char = char_map.get(b_name, "?")
            base = b_name.split(":", 1)[1] if ":" in b_name else b_name
            disp = base.replace("_", " ").title()
            lines.append(f"  [{char}]  {disp} ({b_name})")
        lines.append("")

    return "\n".join(lines)


def render_schematic_ascii(
    schematic: Schematic,
    layer_y: Optional[int] = None,
    show_legend: bool = True,
) -> str:
    """Render an ASCII representation of the schematic."""
    primary = schematic.primary_region
    target_y = layer_y if layer_y is not None else 0
    return render_ascii_layer_y(primary, target_y, show_legend=show_legend)
