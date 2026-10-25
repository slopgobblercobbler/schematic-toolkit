"""Vanilla Minecraft Structure Block (.nbt) format reader and writer."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Dict, List, Union

from schematic_toolkit.formats.base import FormatHandler
from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.region import Region
from schematic_toolkit.models.schematic import Schematic
from schematic_toolkit.nbt import (
    TAG_Compound,
    TAG_Int,
    TAG_List,
    TAG_String,
    TagId,
    read_nbt,
    write_nbt,
)


class VanillaStructureHandler(FormatHandler):
    """Handler for vanilla Minecraft structure block (.nbt) format."""

    format_name = "vanilla_nbt"
    extensions = (".nbt",)

    def read(self, source: Union[str, Path, bytes, BinaryIO]) -> Schematic:
        _, root = read_nbt(source)

        data_version = int(root.get_value("DataVersion", 3463))

        # Size: [x, y, z]
        size_tag = root.get_tag("size")
        width, height, length = 1, 1, 1
        if isinstance(size_tag, TAG_List) and len(size_tag) >= 3:
            width = max(1, int(size_tag[0].value))
            height = max(1, int(size_tag[1].value))
            length = max(1, int(size_tag[2].value))

        # Palette: List of { Name: str, Properties?: Compound }
        palette_tag = root.get_tag("palette")
        palette: List[BlockState] = []
        if isinstance(palette_tag, TAG_List):
            for elem in palette_tag:
                if isinstance(elem, TAG_Compound):
                    b_name = str(elem.get_value("Name", "minecraft:air"))
                    props_tag = elem.get_tag("Properties")
                    props: Dict[str, str] = {}
                    if isinstance(props_tag, TAG_Compound):
                        for pk, pv in props_tag.items():
                            props[pk] = str(pv.value)
                    palette.append(BlockState(name=b_name, properties=props))

        # If palette is empty, initialize default air
        if not palette:
            palette = [BlockState.air()]

        # Find or add air index for unmentioned blocks
        air_state = BlockState.air()
        if air_state in palette:
            air_idx = palette.index(air_state)
        else:
            palette.append(air_state)
            air_idx = len(palette) - 1

        total_blocks = width * height * length
        block_grid = [air_idx] * total_blocks

        # Blocks list: [ { pos: [x, y, z], state: int } ]
        blocks_tag = root.get_tag("blocks")
        if isinstance(blocks_tag, TAG_List):
            for b_elem in blocks_tag:
                if not isinstance(b_elem, TAG_Compound):
                    continue
                pos_list = b_elem.get_tag("pos")
                state_tag = b_elem.get_tag("state")
                if isinstance(pos_list, TAG_List) and len(pos_list) >= 3 and state_tag is not None:
                    bx = int(pos_list[0].value)
                    by = int(pos_list[1].value)
                    bz = int(pos_list[2].value)
                    state = int(state_tag.value)
                    if 0 <= bx < width and 0 <= by < height and 0 <= bz < length:
                        idx = (by * length + bz) * width + bx
                        block_grid[idx] = state

        region = Region(
            name="structure",
            width=width,
            height=height,
            length=length,
            palette=palette,
            blocks=block_grid,
        )

        return Schematic(
            name="structure",
            data_version=data_version,
            regions={"structure": region},
            source_format="vanilla_nbt",
        )

    def write(self, schematic: Schematic, target: Union[str, Path, BinaryIO]) -> None:
        primary = schematic.primary_region

        root = TAG_Compound()
        root["DataVersion"] = TAG_Int(schematic.data_version)

        # size: [X, Y, Z]
        size_list = TAG_List(TagId.INT, [
            TAG_Int(primary.width),
            TAG_Int(primary.height),
            TAG_Int(primary.length),
        ])
        root["size"] = size_list

        # palette: List of Compound
        palette_list = TAG_List(TagId.COMPOUND)
        for state in primary.palette:
            elem = TAG_Compound({"Name": TAG_String(state.name)})
            if state.properties:
                elem["Properties"] = TAG_Compound({
                    k: TAG_String(v) for k, v in state.properties.items()
                })
            palette_list.append(elem)
        root["palette"] = palette_list

        # blocks: List of non-air placed blocks
        blocks_list = TAG_List(TagId.COMPOUND)
        for y in range(primary.height):
            for z in range(primary.length):
                for x in range(primary.width):
                    block_state = primary.get_block(x, y, z)
                    if not block_state.is_air:
                        state_idx = primary.ensure_palette_entry(block_state)
                        b_comp = TAG_Compound({
                            "pos": TAG_List(TagId.INT, [TAG_Int(x), TAG_Int(y), TAG_Int(z)]),
                            "state": TAG_Int(state_idx),
                        })
                        blocks_list.append(b_comp)

        root["blocks"] = blocks_list
        root["entities"] = TAG_List(TagId.COMPOUND)

        write_nbt(root, target, root_name="", compress=True)
