"""Litematica (.litematic) schematic format reader and writer."""

from __future__ import annotations

import time
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
    TAG_Long,
    TAG_Long_Array,
    TAG_String,
    TagId,
    calc_bits_per_block,
    pack_litematica_blocks,
    read_nbt,
    unpack_litematica_blocks,
    write_nbt,
)


class LitematicHandler(FormatHandler):
    """Handler for Litematica (.litematic) format."""

    format_name = "litematic"
    extensions = (".litematic",)

    def read(self, source: Union[str, Path, bytes, BinaryIO]) -> Schematic:
        _, root = read_nbt(source)

        data_version = int(root.get_value("MinecraftDataVersion", 3463))
        version = int(root.get_value("Version", 6))

        # Metadata
        meta_tag = root.get_tag("Metadata")
        name = "Unnamed"
        author = ""
        description = ""
        metadata: Dict[str, Union[str, int]] = {"format_version": version}

        if isinstance(meta_tag, TAG_Compound):
            name = str(meta_tag.get_value("Name", "Unnamed"))
            author = str(meta_tag.get_value("Author", ""))
            description = str(meta_tag.get_value("Description", ""))
            for k, v in meta_tag.items():
                if k not in ("Name", "Author", "Description"):
                    metadata[k] = v.to_native()

        regions_compound = root.get_tag("Regions")
        regions: Dict[str, Region] = {}

        if isinstance(regions_compound, TAG_Compound):
            for reg_name, reg_tag in regions_compound.items():
                if not isinstance(reg_tag, TAG_Compound):
                    continue

                pos_tag = reg_tag.get_tag("Position")
                pos_x = int(pos_tag.get_value("x", 0)) if isinstance(pos_tag, TAG_Compound) else 0
                pos_y = int(pos_tag.get_value("y", 0)) if isinstance(pos_tag, TAG_Compound) else 0
                pos_z = int(pos_tag.get_value("z", 0)) if isinstance(pos_tag, TAG_Compound) else 0

                size_tag = reg_tag.get_tag("Size")
                raw_sx = int(size_tag.get_value("x", 1)) if isinstance(size_tag, TAG_Compound) else 1
                raw_sy = int(size_tag.get_value("y", 1)) if isinstance(size_tag, TAG_Compound) else 1
                raw_sz = int(size_tag.get_value("z", 1)) if isinstance(size_tag, TAG_Compound) else 1

                # Sizes in Litematica can be negative (indicating origin on opposite corner)
                width = abs(raw_sx)
                height = abs(raw_sy)
                length = abs(raw_sz)

                # Parse Palette
                palette_list_tag = reg_tag.get_tag("BlockStatePalette")
                palette: List[BlockState] = []
                if isinstance(palette_list_tag, TAG_List):
                    for elem in palette_list_tag:
                        if isinstance(elem, TAG_Compound):
                            b_name = str(elem.get_value("Name", "minecraft:air"))
                            props_tag = elem.get_tag("Properties")
                            props: Dict[str, str] = {}
                            if isinstance(props_tag, TAG_Compound):
                                for pk, pv in props_tag.items():
                                    props[pk] = str(pv.value)
                            palette.append(BlockState(name=b_name, properties=props))

                if not palette:
                    palette = [BlockState.air()]

                # Unpack BlockStates
                total_blocks = width * height * length
                bits_per_block = calc_bits_per_block(len(palette))

                block_states_tag = reg_tag.get_tag("BlockStates")
                if isinstance(block_states_tag, TAG_Long_Array):
                    unpacked_indices = unpack_litematica_blocks(
                        block_states_tag.value,
                        bits_per_block,
                        total_blocks,
                    )
                else:
                    unpacked_indices = [0] * total_blocks

                region = Region(
                    name=reg_name,
                    width=width,
                    height=height,
                    length=length,
                    offset_x=pos_x,
                    offset_y=pos_y,
                    offset_z=pos_z,
                    palette=palette,
                    blocks=unpacked_indices,
                )
                regions[reg_name] = region

        return Schematic(
            name=name,
            author=author,
            description=description,
            data_version=data_version,
            regions=regions,
            metadata=metadata,
            source_format="litematic",
        )

    def write(self, schematic: Schematic, target: Union[str, Path, BinaryIO]) -> None:
        root = TAG_Compound()
        root["MinecraftDataVersion"] = TAG_Int(schematic.data_version)
        root["Version"] = TAG_Int(schematic.metadata.get("format_version", 6))

        # Enclosing size calculation
        max_w = max((r.width for r in schematic.regions.values()), default=1)
        max_h = max((r.height for r in schematic.regions.values()), default=1)
        max_l = max((r.length for r in schematic.regions.values()), default=1)

        now_ms = int(time.time() * 1000)
        meta = TAG_Compound({
            "Name": TAG_String(schematic.name),
            "Author": TAG_String(schematic.author),
            "Description": TAG_String(schematic.description),
            "RegionCount": TAG_Int(len(schematic.regions)),
            "TimeCreated": TAG_Long(schematic.metadata.get("TimeCreated", now_ms)),
            "TimeModified": TAG_Long(now_ms),
            "TotalBlocks": TAG_Int(schematic.total_blocks(include_air=False)),
            "TotalVolume": TAG_Int(schematic.total_volume),
            "EnclosingSize": TAG_Compound({
                "x": TAG_Int(max_w),
                "y": TAG_Int(max_h),
                "z": TAG_Int(max_l),
            }),
        })
        root["Metadata"] = meta

        # Regions compound
        regions_tag = TAG_Compound()
        for r_name, region in schematic.regions.items():
            r_compound = TAG_Compound()
            r_compound["Position"] = TAG_Compound({
                "x": TAG_Int(region.offset_x),
                "y": TAG_Int(region.offset_y),
                "z": TAG_Int(region.offset_z),
            })
            r_compound["Size"] = TAG_Compound({
                "x": TAG_Int(region.width),
                "y": TAG_Int(region.height),
                "z": TAG_Int(region.length),
            })

            # Palette
            palette_list = TAG_List(TagId.COMPOUND)
            for state in region.palette:
                elem = TAG_Compound({"Name": TAG_String(state.name)})
                if state.properties:
                    props_compound = TAG_Compound({
                        k: TAG_String(v) for k, v in state.properties.items()
                    })
                    elem["Properties"] = props_compound
                palette_list.append(elem)
            r_compound["BlockStatePalette"] = palette_list

            # Packed BlockStates
            bits = calc_bits_per_block(len(region.palette))
            packed_longs = pack_litematica_blocks(region.blocks, bits)
            r_compound["BlockStates"] = TAG_Long_Array(packed_longs)

            # Optional empty lists for compatibility
            r_compound["Entities"] = TAG_List(TagId.COMPOUND)
            r_compound["PendingBlockTicks"] = TAG_List(TagId.COMPOUND)
            r_compound["TileEntities"] = TAG_List(TagId.COMPOUND)

            regions_tag[r_name] = r_compound

        root["Regions"] = regions_tag

        write_nbt(root, target, root_name="", compress=True)
