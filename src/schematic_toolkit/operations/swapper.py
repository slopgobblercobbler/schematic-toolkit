"""Palette swapper operation for substituting block types in schematics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from schematic_toolkit.formats import load_schematic, save_schematic
from schematic_toolkit.models.schematic import Schematic


def parse_swap_spec(spec: str) -> Dict[str, str]:
    """Parse a swap specification string.

    Format examples:
        "stone=deepslate"
        "minecraft:stone=minecraft:deepslate,oak_planks=spruce_planks"
        "minecraft:oak_stairs[facing=north]=minecraft:spruce_stairs[facing=south]"
    """
    mapping: Dict[str, str] = {}
    tokens = spec.split(",")
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if "=" not in token:
            raise ValueError(f"Invalid swap mapping '{token}'. Expected 'from_block=to_block'")
        src, dst = token.split("=", 1)
        src = src.strip()
        dst = dst.strip()
        if not src or not dst:
            raise ValueError(f"Invalid swap mapping '{token}': source or destination is empty")
        mapping[src] = dst
    return mapping


def load_swap_recipe(recipe_path: Union[str, Path]) -> Dict[str, str]:
    """Load a JSON dictionary mapping source blocks to target blocks."""
    path = Path(recipe_path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Recipe file must contain a JSON object mapping old blocks to new blocks")
    return {str(k): str(v) for k, v in data.items()}


def swap_palette(
    schematic: Schematic,
    mapping: Dict[str, str],
    preserve_properties: bool = True,
) -> int:
    """Substitute block types in the schematic.

    Args:
        schematic: Schematic instance.
        mapping: Dictionary mapping source block expressions to target block expressions.
        preserve_properties: Whether to preserve original block states.

    Returns:
        Number of placed blocks altered.
    """
    return schematic.swap_palette(mapping, preserve_properties=preserve_properties)


def swap_schematic_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]],
    mapping: Dict[str, str],
    in_place: bool = False,
    preserve_properties: bool = True,
) -> Tuple[Schematic, int, Path]:
    """Load, swap palette, and save schematic.

    Args:
        input_path: Source schematic file path.
        output_path: Destination path, or None if in_place is True.
        mapping: Substitution dictionary.
        in_place: If True, overwrite input_path.
        preserve_properties: If True, keep properties like facing/waterlogged.

    Returns:
        Tuple of (schematic, blocks_changed_count, destination_path)
    """
    in_p = Path(input_path).resolve()
    schematic = load_schematic(in_p)

    blocks_changed = swap_palette(schematic, mapping, preserve_properties=preserve_properties)

    if in_place:
        dest_p = in_p
    elif output_path:
        dest_p = Path(output_path).resolve()
    else:
        # Default suffix
        dest_p = in_p.with_stem(f"{in_p.stem}_swapped")

    save_schematic(schematic, dest_p)
    return (schematic, blocks_changed, dest_p)
