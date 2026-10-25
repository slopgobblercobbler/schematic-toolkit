"""Tests for reading and writing .litematic, .schem, and .nbt formats."""

from __future__ import annotations

from pathlib import Path

from schematic_toolkit.formats import (
    LitematicHandler,
    SpongeSchematicHandler,
    VanillaStructureHandler,
    load_schematic,
    save_schematic,
)
from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.schematic import Schematic


def test_litematic_roundtrip(sample_schematic: Schematic, temp_dir: Path) -> None:
    file_path = temp_dir / "test.litematic"
    save_schematic(sample_schematic, file_path)
    assert file_path.exists()

    loaded = load_schematic(file_path)
    assert loaded.name == sample_schematic.name
    assert loaded.author == sample_schematic.author
    assert loaded.primary_region.width == 3
    assert loaded.primary_region.height == 3
    assert loaded.primary_region.length == 3

    # Check block properties preserved
    stairs_block = loaded.primary_region.get_block(1, 1, 1)
    assert stairs_block.name == "minecraft:oak_stairs"
    assert stairs_block.properties.get("facing") == "north"
    assert stairs_block.properties.get("half") == "bottom"


def test_sponge_schem_roundtrip(sample_schematic: Schematic, temp_dir: Path) -> None:
    file_path = temp_dir / "test.schem"
    save_schematic(sample_schematic, file_path)
    assert file_path.exists()

    loaded = load_schematic(file_path)
    assert loaded.primary_region.width == 3
    assert loaded.primary_region.height == 3
    assert loaded.primary_region.length == 3

    # Check stairs preserved
    stairs = loaded.primary_region.get_block(1, 1, 1)
    assert stairs.name == "minecraft:oak_stairs"
    assert stairs.properties["facing"] == "north"

    # Check torch preserved
    torch = loaded.primary_region.get_block(1, 1, 2)
    assert torch.name == "minecraft:torch"


def test_vanilla_nbt_roundtrip(sample_schematic: Schematic, temp_dir: Path) -> None:
    file_path = temp_dir / "test.nbt"
    save_schematic(sample_schematic, file_path)
    assert file_path.exists()

    loaded = load_schematic(file_path)
    assert loaded.primary_region.width == 3
    assert loaded.primary_region.height == 3
    assert loaded.primary_region.length == 3

    # Check stone floor at Y=0
    for z in range(3):
        for x in range(3):
            b = loaded.primary_region.get_block(x, 0, z)
            assert b.name == "minecraft:stone"

    # Check stairs at (1, 1, 1)
    stairs = loaded.primary_region.get_block(1, 1, 1)
    assert stairs.name == "minecraft:oak_stairs"
    assert stairs.properties["facing"] == "north"


def test_litematic_multi_region(temp_dir: Path) -> None:
    from schematic_toolkit.models.region import Region

    r1 = Region("R1", 2, 2, 2, offset_x=0, offset_y=0, offset_z=0)
    r1.set_block(0, 0, 0, BlockState("minecraft:iron_block"))

    r2 = Region("R2", 3, 3, 3, offset_x=10, offset_y=20, offset_z=30)
    r2.set_block(0, 0, 0, BlockState("minecraft:gold_block"))

    schem = Schematic("MultiReg", regions={"R1": r1, "R2": r2})

    target = temp_dir / "multi.litematic"
    save_schematic(schem, target)

    loaded = load_schematic(target)
    assert len(loaded.regions) == 2
    assert "R1" in loaded.regions
    assert "R2" in loaded.regions
    assert loaded.regions["R1"].get_block(0, 0, 0).name == "minecraft:iron_block"
    assert loaded.regions["R2"].get_block(0, 0, 0).name == "minecraft:gold_block"
    assert loaded.regions["R2"].offset_y == 20
