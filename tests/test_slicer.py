"""Tests for structure slice extractor."""

from __future__ import annotations

from pathlib import Path

from schematic_toolkit.formats import load_schematic
from schematic_toolkit.models.schematic import Schematic
from schematic_toolkit.operations.slicer import (
    parse_range_spec,
    slice_schematic_file,
    slice_schematic_y,
)


def test_parse_range_spec() -> None:
    assert parse_range_spec("10:20") == (10, 20)
    assert parse_range_spec("10..20") == (10, 20)
    assert parse_range_spec("10-20") == (10, 20)
    assert parse_range_spec("15") == (15, 15)
    assert parse_range_spec("20:10") == (10, 20)


def test_slice_schematic_y_floor(sample_schematic: Schematic) -> None:
    # Layer 0 is stone floor
    sliced = slice_schematic_y(sample_schematic, min_y=0, max_y=0)
    primary = sliced.primary_region

    assert primary.width == 3
    assert primary.height == 1
    assert primary.length == 3
    assert sliced.total_blocks(include_air=False) == 9

    materials = sliced.material_counts(include_air=False)
    assert materials == {"minecraft:stone": 9}


def test_slice_schematic_y_upper(sample_schematic: Schematic) -> None:
    # Layers 1 to 2
    sliced = slice_schematic_y(sample_schematic, min_y=1, max_y=2, recenter=True)
    primary = sliced.primary_region

    assert primary.width == 3
    assert primary.height == 2
    assert primary.length == 3
    assert primary.offset_x == 0
    assert primary.offset_y == 0
    assert primary.offset_z == 0

    # Stairs block was at Y=1 in original, in slice it should be at Y=0!
    stairs = primary.get_block(1, 0, 1)
    assert stairs.name == "minecraft:oak_stairs"
    assert stairs.properties["facing"] == "north"


def test_slice_schematic_file(sample_litematic_file: Path, temp_dir: Path) -> None:
    out_file = temp_dir / "cottage_slice.litematic"
    sliced_schem, dest_p = slice_schematic_file(
        input_path=sample_litematic_file,
        output_path=out_file,
        min_y=0,
        max_y=1,
    )
    assert dest_p == out_file
    assert out_file.exists()

    reloaded = load_schematic(out_file)
    assert reloaded.primary_region.height == 2
    assert reloaded.total_blocks(include_air=False) == 15  # 9 stone + 6 layer 1
