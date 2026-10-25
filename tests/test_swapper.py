"""Tests for palette swapper operations."""

from __future__ import annotations

import json
from pathlib import Path

from schematic_toolkit.formats import load_schematic, save_schematic
from schematic_toolkit.models.schematic import Schematic
from schematic_toolkit.operations.swapper import (
    load_swap_recipe,
    parse_swap_spec,
    swap_palette,
    swap_schematic_file,
)


def test_parse_swap_spec() -> None:
    spec = "stone=deepslate, oak_planks=spruce_planks"
    mapping = parse_swap_spec(spec)
    assert mapping["stone"] == "deepslate"
    assert mapping["oak_planks"] == "spruce_planks"


def test_swap_palette_simple(sample_schematic: Schematic) -> None:
    mapping = {"minecraft:stone": "minecraft:deepslate"}
    changed = swap_palette(sample_schematic, mapping)
    assert changed == 9

    materials = sample_schematic.material_counts(include_air=False)
    assert "minecraft:stone" not in materials
    assert materials["minecraft:deepslate"] == 9


def test_swap_palette_preserve_properties(sample_schematic: Schematic) -> None:
    # oak_stairs has facing=north, half=bottom
    mapping = {"oak_stairs": "spruce_stairs"}
    changed = swap_palette(sample_schematic, mapping, preserve_properties=True)
    assert changed == 1

    stairs = sample_schematic.primary_region.get_block(1, 1, 1)
    assert stairs.name == "minecraft:spruce_stairs"
    assert stairs.properties["facing"] == "north"
    assert stairs.properties["half"] == "bottom"


def test_swap_schematic_file_in_place(sample_litematic_file: Path) -> None:
    mapping = {"minecraft:stone": "minecraft:blackstone"}
    schem, changed, dest_p = swap_schematic_file(
        input_path=sample_litematic_file,
        output_path=None,
        mapping=mapping,
        in_place=True,
    )
    assert dest_p == sample_litematic_file
    assert changed == 9

    reloaded = load_schematic(sample_litematic_file)
    assert reloaded.material_counts(include_air=False)["minecraft:blackstone"] == 9


def test_swap_with_recipe_json(temp_dir: Path, sample_schematic: Schematic) -> None:
    recipe_file = temp_dir / "recipe.json"
    recipe_data = {
        "minecraft:stone": "minecraft:polished_andesite",
        "minecraft:torch": "minecraft:soul_torch",
    }
    with open(recipe_file, "w") as f:
        json.dump(recipe_data, f)

    mapping = load_swap_recipe(recipe_file)
    assert len(mapping) == 2

    changed = swap_palette(sample_schematic, mapping)
    assert changed == 10  # 9 stone + 1 torch

    counts = sample_schematic.material_counts()
    assert counts["minecraft:polished_andesite"] == 9
    assert counts["minecraft:soul_torch"] == 1
