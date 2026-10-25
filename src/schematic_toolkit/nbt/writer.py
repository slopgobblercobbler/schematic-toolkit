"""NBT binary stream writer / serializer.

Supports writing uncompressed or Gzip compressed NBT binary files and streams.
"""

from __future__ import annotations

import gzip
import io
import struct
from pathlib import Path
from typing import BinaryIO, Union

from schematic_toolkit.nbt.tags import (
    TAG,
    TAG_Byte,
    TAG_Byte_Array,
    TAG_Compound,
    TAG_Double,
    TAG_Float,
    TAG_Int,
    TAG_Int_Array,
    TAG_List,
    TAG_Long,
    TAG_Long_Array,
    TAG_Short,
    TAG_String,
    TagId,
)


class NBTWriter:
    """Serializes NBT tags to a binary stream."""

    def __init__(self, stream: BinaryIO) -> None:
        self.stream = stream

    def write_byte(self, val: int) -> None:
        self.stream.write(struct.pack(">b", int(val)))

    def write_ubyte(self, val: int) -> None:
        self.stream.write(struct.pack(">B", int(val)))

    def write_short(self, val: int) -> None:
        self.stream.write(struct.pack(">h", int(val)))

    def write_ushort(self, val: int) -> None:
        self.stream.write(struct.pack(">H", int(val)))

    def write_int(self, val: int) -> None:
        self.stream.write(struct.pack(">i", int(val)))

    def write_long(self, val: int) -> None:
        self.stream.write(struct.pack(">q", int(val)))

    def write_float(self, val: float) -> None:
        self.stream.write(struct.pack(">f", float(val)))

    def write_double(self, val: float) -> None:
        self.stream.write(struct.pack(">d", float(val)))

    def write_string(self, text: str) -> None:
        encoded = text.encode("utf-8")
        self.write_ushort(len(encoded))
        self.stream.write(encoded)

    def write_tag_payload(self, tag: TAG) -> None:
        if isinstance(tag, TAG_Byte):
            self.write_byte(tag.value)
        elif isinstance(tag, TAG_Short):
            self.write_short(tag.value)
        elif isinstance(tag, TAG_Int):
            self.write_int(tag.value)
        elif isinstance(tag, TAG_Long):
            self.write_long(tag.value)
        elif isinstance(tag, TAG_Float):
            self.write_float(tag.value)
        elif isinstance(tag, TAG_Double):
            self.write_double(tag.value)
        elif isinstance(tag, TAG_Byte_Array):
            self.write_int(len(tag.value))
            self.stream.write(bytes(tag.value))
        elif isinstance(tag, TAG_String):
            self.write_string(tag.value)
        elif isinstance(tag, TAG_List):
            self.write_ubyte(tag.element_type)
            self.write_int(len(tag))
            for item in tag:
                self.write_tag_payload(item)
        elif isinstance(tag, TAG_Compound):
            for name, sub_tag in tag.items():
                self.write_ubyte(sub_tag.tag_id)
                self.write_string(name)
                self.write_tag_payload(sub_tag)
            self.write_ubyte(TagId.END)
        elif isinstance(tag, TAG_Int_Array):
            self.write_int(len(tag))
            if len(tag) > 0:
                self.stream.write(struct.pack(f">{len(tag)}i", *tag))
        elif isinstance(tag, TAG_Long_Array):
            self.write_int(len(tag))
            if len(tag) > 0:
                self.stream.write(struct.pack(f">{len(tag)}q", *tag))
        else:
            raise TypeError(f"Unknown tag type for payload writing: {type(tag)}")

    def write_root(self, root_tag: TAG, root_name: str = "") -> None:
        """Write root tag with tag_id, name, and payload."""
        self.write_ubyte(root_tag.tag_id)
        self.write_string(root_name)
        self.write_tag_payload(root_tag)


def write_nbt(
    root_tag: TAG,
    target: Union[str, Path, BinaryIO],
    root_name: str = "",
    compress: bool = True,
) -> None:
    """Serialize an NBT tag hierarchy and write to file or stream.

    Args:
        root_tag: The root TAG (usually TAG_Compound)
        target: File path or writable binary stream
        root_name: Optional name for root compound
        compress: Whether to gzip compress the output (standard for Minecraft files)
    """
    buf = io.BytesIO()
    writer = NBTWriter(buf)
    writer.write_root(root_tag, root_name)
    raw_data = buf.getvalue()

    output_data = gzip.compress(raw_data) if compress else raw_data

    if isinstance(target, (str, Path)):
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(output_data)
    elif hasattr(target, "write"):
        target.write(output_data)
    else:
        raise TypeError(f"Unsupported target type: {type(target)}")
