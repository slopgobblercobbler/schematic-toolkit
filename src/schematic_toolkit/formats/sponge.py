"""Sponge Schematic (.schem) format reader and writer (v1, v2, v3)."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Dict, List, Union

from schematic_toolkit.formats.base import FormatHandler
from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.region import Region
from schematic_toolkit.models.schematic import Schematic
from schematic_toolkit.nbt import (
    TAG_Byte_Array,
    TAG_Compound,
    TAG_Int,
    TAG_Int_Array,
    TAG_Short,
    TAG_String,
    read_nbt,
    read_varint_stream,
    write_nbt,
    write_varint_stream,
)


class SpongeSchematicHandler(FormatHandler):
    """Handler for Sponge Schematic (.schem) format (v1, v2, and v3)."""

    format_name = "sponge"
    extensions = (".schem",)

    def read(self, source: Union[str, Path, bytes, BinaryIO]) -> Schematic:
        _, root = read_nbt(source)

        version = int(root.get_value("Version", 2))
        data_version = int(root.get_value("DataVersion", 3463))

        width = int(root.get_value("Width", 1))
        height = int(root.get_value("Height", 1))
        length = int(root.get_value("Length", 1))

        # Relative offset
        offset_tag = root.get_tag("Offset")
        offset_x, offset_y, offset_z = 0, 0, 0
        if isinstance(offset_tag, TAG_Int_Array) and len(offset_tag) >= 3:
            offset_x, offset_y, offset_z = int(offset_tag[0]), int(offset_tag[1]), int(offset_tag[2])

        # Metadata
        name = "Unnamed"
        author = ""
        description = ""
        meta_tag = root.get_tag("Metadata")
        metadata: Dict[str, Union[str, int]] = {"format_version": version}
        if isinstance(meta_tag, TAG_Compound):
            name = str(meta_tag.get_value("Name", "Unnamed"))
            author = str(meta_tag.get_value("Author", ""))
            description = str(meta_tag.get_value("Description", ""))
            for k, v in meta_tag.items():
                if k not in ("Name", "Author", "Description"):
                    metadata[k] = v.to_native()

        # Palette is "BlockPalette" in v3, "Palette" in v1 & v2
        palette_compound = root.get_tag("BlockPalette") or root.get_tag("Palette")
        palette_map: Dict[int, BlockState] = {}
        max_idx = 0

        if isinstance(palette_compound, TAG_Compound):
            for state_str, idx_tag in palette_compound.items():
                idx = int(idx_tag.value)
                palette_map[idx] = BlockState.from_string(state_str)
                if idx > max_idx:
                    max_idx = idx

        # Reconstruct sequential palette array
        palette: List[BlockState] = [BlockState.air()] * (max_idx + 1)
        for idx, state in palette_map.items():
            palette[idx] = state

        if not palette:
            palette = [BlockState.air()]

        # Read BlockData
        total_blocks = width * height * length
        block_data_tag = root.get_tag("BlockData")
        if isinstance(block_data_tag, TAG_Byte_Array):
            block_indices = read_varint_stream(bytes(block_data_tag.value), total_blocks)
        else:
            block_indices = [0] * total_blocks

        region = Region(
            name=name,
            width=width,
            height=height,
            length=length,
            offset_x=offset_x,
            offset_y=offset_y,
            offset_z=offset_z,
            palette=palette,
            blocks=block_indices,
        )

        schem = Schematic(
            name=name,
            author=author,
            description=description,
            data_version=data_version,
            regions={name: region},
            metadata=metadata,
            source_format="sponge",
        )
        return schem

    def write(self, schematic: Schematic, target: Union[str, Path, BinaryIO]) -> None:
        primary = schematic.primary_region

        root = TAG_Compound()
        root["Version"] = TAG_Int(schematic.metadata.get("format_version", 2))
        root["DataVersion"] = TAG_Int(schematic.data_version)

        root["Width"] = TAG_Short(primary.width)
        root["Height"] = TAG_Short(primary.height)
        root["Length"] = TAG_Short(primary.length)
        root["Offset"] = TAG_Int_Array([primary.offset_x, primary.offset_y, primary.offset_z])

        # Metadata
        meta = TAG_Compound({
            "Name": TAG_String(schematic.name),
            "Author": TAG_String(schematic.author),
            "Description": TAG_String(schematic.description),
        })
        root["Metadata"] = meta

        # Palette
        palette_compound = TAG_Compound()
        for idx, state in enumerate(primary.palette):
            palette_compound[state.to_string()] = TAG_Int(idx)

        root["Palette"] = palette_compound
        root["PaletteMax"] = TAG_Int(len(primary.palette))

        # Encode VarInt BlockData
        varint_bytes = write_varint_stream(primary.blocks)
        root["BlockData"] = TAG_Byte_Array(varint_bytes)

        write_nbt(root, target, root_name="Schematic", compress=True)
