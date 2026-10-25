"""Additional targeted unit tests to maximize test coverage."""

from __future__ import annotations

import io
from pathlib import Path
import pytest
from click.testing import CliRunner

from schematic_toolkit.cli import main
from schematic_toolkit.exporters.ascii_art import render_schematic_ascii
from schematic_toolkit.exporters.markdown import export_markdown
from schematic_toolkit.formats import (
    LitematicHandler,
    SpongeSchematicHandler,
    VanillaStructureHandler,
    detect_format_from_data,
    load_schematic,
    save_schematic,
)
from schematic_toolkit.materials.calculator import calculate_materials
from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.region import Region
from schematic_toolkit.models.schematic import Schematic
from schematic_toolkit.nbt import (
    NBTFormatError,
    TAG_Byte,
    TAG_Byte_Array,
    TAG_Compound,
    TAG_Double,
    TAG_End,
    TAG_Float,
    TAG_Int,
    TAG_Int_Array,
    TAG_List,
    TAG_Long,
    TAG_Long_Array,
    TAG_Short,
    TAG_String,
    TagId,
    native_to_tag,
    read_nbt,
    write_nbt,
)
from schematic_toolkit.operations.slicer import parse_range_spec
from schematic_toolkit.operations.swapper import parse_swap_spec


def test_block_state_helpers() -> None:
    b = BlockState("oak_stairs", {"facing": "south"})
    assert b.name == "minecraft:oak_stairs"
    assert b.namespace == "minecraft"
    assert b.base_name == "oak_stairs"
    assert b.display_name == "Oak Stairs"
    assert not b.is_air

    # with_name
    b2 = b.with_name("spruce_stairs")
    assert b2.name == "minecraft:spruce_stairs"
    assert b2.properties["facing"] == "south"

    b3 = b.with_name("stone", keep_properties=False)
    assert b3.name == "minecraft:stone"
    assert b3.properties == {}

    # with_properties
    b4 = b.with_properties(waterlogged="true")
    assert b4.properties["waterlogged"] == "true"
    assert b4.properties["facing"] == "south"

    # Air variants
    assert BlockState("minecraft:cave_air").is_air
    assert BlockState("void_air").is_air


def test_region_helpers_and_errors() -> None:
    with pytest.raises(ValueError):
        Region("Invalid", -1, 1, 1)

    r = Region("Box", 2, 2, 2)
    assert r.volume == 8

    # out of bounds
    with pytest.raises(IndexError):
        r.get_block(5, 0, 0)
    with pytest.raises(IndexError):
        r.get_coords(99)

    # get_coords roundtrip
    for idx in range(8):
        x, y, z = r.get_coords(idx)
        assert r.get_index(x, y, z) == idx

    # clone
    r.set_block(0, 0, 0, BlockState("stone"))
    clone_r = r.clone()
    assert clone_r.get_block(0, 0, 0).name == "minecraft:stone"

    # subvolume invalid bounds
    with pytest.raises(ValueError):
        r.extract_subvolume(1, 0, 0, 0, 0, 0)


def test_schematic_bounding_box(sample_schematic: Schematic) -> None:
    sub = sample_schematic.extract_bounding_box(
        min_x=0, max_x=1, min_y=0, max_y=1, min_z=0, max_z=1, recenter=True
    )
    assert sub.primary_region.width == 2
    assert sub.primary_region.height == 2
    assert sub.primary_region.length == 2
    assert repr(sample_schematic).startswith("Schematic(")


def test_markdown_multi_region_export() -> None:
    r1 = Region("R1", 2, 2, 2)
    r2 = Region("R2", 3, 3, 3)
    schem = Schematic("Multi", regions={"R1": r1, "R2": r2})
    md = export_markdown(schem, include_diagram=False)
    assert "## Regions" in md
    assert "`R1`" in md
    assert "`R2`" in md


def test_ascii_schematic_render(sample_schematic: Schematic) -> None:
    art = render_schematic_ascii(sample_schematic, layer_y=0)
    assert "Layer Y=0" in art


def test_format_detection() -> None:
    assert detect_format_from_data("cottage.litematic") == "litematic"
    assert detect_format_from_data("cottage.schem") == "sponge"
    assert detect_format_from_data("cottage.nbt") == "vanilla_nbt"
    assert detect_format_from_data("unknown.bin") == "litematic"


def test_cli_error_paths(temp_dir: Path) -> None:
    runner = CliRunner()

    # Info with non-existent file
    res = runner.invoke(main, ["info", str(temp_dir / "missing.schem")])
    assert res.exit_code != 0

    # Materials with missing file
    res = runner.invoke(main, ["materials", str(temp_dir / "missing.schem")])
    assert res.exit_code != 0

    # Swap without arguments
    res = runner.invoke(main, ["swap", str(temp_dir / "missing.schem")])
    assert res.exit_code != 0

    # Slice without y-range
    res = runner.invoke(main, ["slice", str(temp_dir / "missing.schem")])
    assert res.exit_code != 0

    # Slice with invalid range
    with pytest.raises(ValueError):
        parse_range_spec("invalid_range")

    # Swap with invalid mapping
    with pytest.raises(ValueError):
        parse_swap_spec("stone_without_equals")
    with pytest.raises(ValueError):
        parse_swap_spec("stone=")


def test_cli_info_multi_region(temp_dir: Path) -> None:
    r1 = Region("R1", 2, 2, 2)
    r2 = Region("R2", 3, 3, 3)
    schem = Schematic("Multi", regions={"R1": r1, "R2": r2})
    file_p = temp_dir / "multi.litematic"
    save_schematic(schem, file_p)

    runner = CliRunner()
    res = runner.invoke(main, ["info", str(file_p)])
    assert res.exit_code == 0
    assert "Regions Breakdown" in res.output
    assert "R1" in res.output
    assert "R2" in res.output


def test_tags_operations() -> None:
    tag_list = TAG_List(TagId.INT, [TAG_Int(1), TAG_Int(2), TAG_Int(3)])
    del tag_list[1]
    assert len(tag_list) == 2
    assert tag_list[1].value == 3

    comp = TAG_Compound({"a": TAG_Int(1), "b": TAG_String("s")})
    del comp["a"]
    assert "a" not in comp
    assert len(comp) == 1

    # End tag
    end1 = TAG_End()
    end2 = TAG_End()
    assert end1 == end2
    assert end1.value is None

    # Floats / doubles comparisons
    assert TAG_Float(1.0) == 1.0
    assert TAG_Double(2.0) == 2.0
    assert TAG_Byte(5) == 5
    assert TAG_Short(5) == 5
    assert TAG_Int(5) == 5
    assert TAG_Long(5) == 5
    assert TAG_String("hi") == "hi"

    # Int array mutate
    ia = TAG_Int_Array([10, 20])
    del ia[0]
    assert len(ia) == 1
    assert ia[0] == 20
    ia.insert(0, 5)
    assert ia[0] == 5

    # Long array mutate
    la = TAG_Long_Array([100, 200])
    del la[0]
    assert len(la) == 1
    assert la[0] == 200
    la.insert(0, 50)
    assert la[0] == 50
