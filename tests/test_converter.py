"""Tests for format converter operations."""

from __future__ import annotations

from pathlib import Path

from schematic_toolkit.formats import load_schematic
from schematic_toolkit.operations.converter import convert_schematic_file


def test_convert_litematic_to_schem(sample_litematic_file: Path, temp_dir: Path) -> None:
    schem_out = temp_dir / "converted.schem"
    _, dest = convert_schematic_file(sample_litematic_file, schem_out)
    assert dest == schem_out
    assert schem_out.exists()

    reloaded = load_schematic(schem_out)
    assert reloaded.source_format == "sponge"
    assert reloaded.primary_region.width == 3
    assert reloaded.primary_region.height == 3
    assert reloaded.primary_region.length == 3
    assert reloaded.total_blocks(include_air=False) == 16


def test_convert_schem_to_nbt(sample_schem_file: Path, temp_dir: Path) -> None:
    nbt_out = temp_dir / "converted.nbt"
    _, dest = convert_schematic_file(sample_schem_file, nbt_out)
    assert dest == nbt_out
    assert nbt_out.exists()

    reloaded = load_schematic(nbt_out)
    assert reloaded.source_format == "vanilla_nbt"
    assert reloaded.primary_region.width == 3
    assert reloaded.total_blocks(include_air=False) == 16


def test_convert_nbt_to_litematic(sample_nbt_file: Path, temp_dir: Path) -> None:
    litematic_out = temp_dir / "converted.litematic"
    _, dest = convert_schematic_file(sample_nbt_file, litematic_out)
    assert dest == litematic_out
    assert litematic_out.exists()

    reloaded = load_schematic(litematic_out)
    assert reloaded.source_format == "litematic"
    assert reloaded.primary_region.width == 3
    assert reloaded.total_blocks(include_air=False) == 16
