"""Pytest fixtures for schematic-toolkit tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from schematic_toolkit.formats import save_schematic
from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.region import Region
from schematic_toolkit.models.schematic import Schematic


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Temporary working directory for test files."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def sample_schematic() -> Schematic:
    """Create a sample 3x3x3 schematic with known blocks and properties."""
    # Palette
    air = BlockState.air()
    stone = BlockState("minecraft:stone")
    oak_planks = BlockState("minecraft:oak_planks")
    oak_stairs = BlockState("minecraft:oak_stairs", {"facing": "north", "half": "bottom"})
    torch = BlockState("minecraft:torch")
    ender_pearl_block = BlockState("minecraft:oak_sign")  # 16-stack
    bed_block = BlockState("minecraft:red_bed")  # 1-stack

    palette = [air, stone, oak_planks, oak_stairs, torch, ender_pearl_block, bed_block]
    width, height, length = 3, 3, 3
    total = width * height * length
    blocks = [0] * total

    # Layer 0 (Y=0): Stone floor (9 stone blocks)
    for z in range(3):
        for x in range(3):
            idx = (0 * 3 + z) * 3 + x
            blocks[idx] = 1  # stone

    # Layer 1 (Y=1): Oak planks corners, stairs, torch, sign, bed
    blocks[(1 * 3 + 0) * 3 + 0] = 2  # oak planks
    blocks[(1 * 3 + 0) * 3 + 2] = 2  # oak planks
    blocks[(1 * 3 + 1) * 3 + 1] = 3  # oak stairs
    blocks[(1 * 3 + 2) * 3 + 1] = 4  # torch
    blocks[(1 * 3 + 2) * 3 + 2] = 5  # oak sign (16 stack)
    blocks[(1 * 3 + 1) * 3 + 0] = 6  # red bed (1 stack)

    # Layer 2 (Y=2): Top roof (planks)
    blocks[(2 * 3 + 1) * 3 + 1] = 2  # oak planks

    region = Region(
        name="Main",
        width=width,
        height=height,
        length=length,
        offset_x=10,
        offset_y=64,
        offset_z=20,
        palette=palette,
        blocks=blocks,
    )

    schem = Schematic(
        name="CozyCottage",
        author="Notch",
        description="A cozy test cottage",
        data_version=3463,
        regions={"Main": region},
    )
    return schem


@pytest.fixture
def sample_litematic_file(sample_schematic: Schematic, temp_dir: Path) -> Path:
    target = temp_dir / "cottage.litematic"
    save_schematic(sample_schematic, target, format_name="litematic")
    return target


@pytest.fixture
def sample_schem_file(sample_schematic: Schematic, temp_dir: Path) -> Path:
    target = temp_dir / "cottage.schem"
    save_schematic(sample_schematic, target, format_name="sponge")
    return target


@pytest.fixture
def sample_nbt_file(sample_schematic: Schematic, temp_dir: Path) -> Path:
    target = temp_dir / "cottage.nbt"
    save_schematic(sample_schematic, target, format_name="vanilla_nbt")
    return target
