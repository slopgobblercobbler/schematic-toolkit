"""NBT binary stream reader / deserializer.

Supports Gzip, Zlib, and raw uncompressed binary NBT files and streams.
Handles all Minecraft Java edition data structures.
"""

from __future__ import annotations

import gzip
import io
import struct
import zlib
from pathlib import Path
from typing import BinaryIO, Tuple, Union

from schematic_toolkit.nbt.tags import (
    TAG,
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
)


class NBTFormatError(ValueError):
    """Raised when parsing corrupted or non-standard NBT data."""
    pass


class NBTReader:
    """Deserializes binary NBT data from a file-like byte stream."""

    def __init__(self, stream: BinaryIO) -> None:
        self.stream = stream

    def read_byte(self) -> int:
        b = self.stream.read(1)
        if len(b) < 1:
            raise EOFError("Unexpected EOF reading byte")
        return struct.unpack(">b", b)[0]

    def read_ubyte(self) -> int:
        b = self.stream.read(1)
        if len(b) < 1:
            raise EOFError("Unexpected EOF reading unsigned byte")
        return struct.unpack(">B", b)[0]

    def read_short(self) -> int:
        b = self.stream.read(2)
        if len(b) < 2:
            raise EOFError("Unexpected EOF reading short")
        return struct.unpack(">h", b)[0]

    def read_ushort(self) -> int:
        b = self.stream.read(2)
        if len(b) < 2:
            raise EOFError("Unexpected EOF reading unsigned short")
        return struct.unpack(">H", b)[0]

    def read_int(self) -> int:
        b = self.stream.read(4)
        if len(b) < 4:
            raise EOFError("Unexpected EOF reading int")
        return struct.unpack(">i", b)[0]

    def read_long(self) -> int:
        b = self.stream.read(8)
        if len(b) < 8:
            raise EOFError("Unexpected EOF reading long")
        return struct.unpack(">q", b)[0]

    def read_float(self) -> float:
        b = self.stream.read(4)
        if len(b) < 4:
            raise EOFError("Unexpected EOF reading float")
        return struct.unpack(">f", b)[0]

    def read_double(self) -> float:
        b = self.stream.read(8)
        if len(b) < 8:
            raise EOFError("Unexpected EOF reading double")
        return struct.unpack(">d", b)[0]

    def read_string(self) -> str:
        length = self.read_ushort()
        if length == 0:
            return ""
        data = self.stream.read(length)
        if len(data) < length:
            raise EOFError("Unexpected EOF reading string bytes")
        return data.decode("utf-8", errors="replace")

    def read_tag_payload(self, tag_id: int) -> TAG:
        if tag_id == TagId.END:
            return TAG_End()
        elif tag_id == TagId.BYTE:
            return TAG_Byte(self.read_byte())
        elif tag_id == TagId.SHORT:
            return TAG_Short(self.read_short())
        elif tag_id == TagId.INT:
            return TAG_Int(self.read_int())
        elif tag_id == TagId.LONG:
            return TAG_Long(self.read_long())
        elif tag_id == TagId.FLOAT:
            return TAG_Float(self.read_float())
        elif tag_id == TagId.DOUBLE:
            return TAG_Double(self.read_double())
        elif tag_id == TagId.BYTE_ARRAY:
            length = self.read_int()
            if length < 0:
                raise NBTFormatError(f"Negative byte array length: {length}")
            data = self.stream.read(length)
            if len(data) < length:
                raise EOFError("Unexpected EOF reading byte array")
            return TAG_Byte_Array(data)
        elif tag_id == TagId.STRING:
            return TAG_String(self.read_string())
        elif tag_id == TagId.LIST:
            elem_type = self.read_ubyte()
            length = self.read_int()
            if length < 0:
                raise NBTFormatError(f"Negative list length: {length}")
            tag_list = TAG_List(elem_type)
            if length == 0:
                return tag_list
            for _ in range(length):
                elem = self.read_tag_payload(elem_type)
                tag_list.append(elem)
            return tag_list
        elif tag_id == TagId.COMPOUND:
            compound = TAG_Compound()
            while True:
                sub_tag_id = self.read_ubyte()
                if sub_tag_id == TagId.END:
                    break
                name = self.read_string()
                payload = self.read_tag_payload(sub_tag_id)
                compound[name] = payload
            return compound
        elif tag_id == TagId.INT_ARRAY:
            length = self.read_int()
            if length < 0:
                raise NBTFormatError(f"Negative int array length: {length}")
            raw = self.stream.read(length * 4)
            if len(raw) < length * 4:
                raise EOFError("Unexpected EOF reading int array")
            unpacked = struct.unpack(f">{length}i", raw)
            return TAG_Int_Array(unpacked)
        elif tag_id == TagId.LONG_ARRAY:
            length = self.read_int()
            if length < 0:
                raise NBTFormatError(f"Negative long array length: {length}")
            raw = self.stream.read(length * 8)
            if len(raw) < length * 8:
                raise EOFError("Unexpected EOF reading long array")
            unpacked = struct.unpack(f">{length}q", raw)
            return TAG_Long_Array(unpacked)
        else:
            raise NBTFormatError(f"Unknown NBT Tag ID: {tag_id}")

    def read_root(self) -> Tuple[str, TAG]:
        """Read the root tag, returning (root_name, tag)."""
        tag_id = self.read_ubyte()
        if tag_id == TagId.END:
            return ("", TAG_End())
        name = self.read_string()
        payload = self.read_tag_payload(tag_id)
        return (name, payload)


def decompress_nbt(raw_bytes: bytes) -> bytes:
    """Decompress raw bytes if Gzip or Zlib compressed, or return as is."""
    if len(raw_bytes) >= 2 and raw_bytes[:2] == b"\x1f\x8b":
        return gzip.decompress(raw_bytes)
    if len(raw_bytes) >= 2 and raw_bytes[0] == 0x78 and (raw_bytes[1] in (0x01, 0x9C, 0xDA, 0x5E)):
        try:
            return zlib.decompress(raw_bytes)
        except zlib.error:
            pass
    return raw_bytes


def read_nbt(source: Union[str, Path, bytes, BinaryIO]) -> Tuple[str, TAG_Compound]:
    """Read an NBT file or buffer.

    Returns:
        Tuple of (root_name, root_compound)
    """
    if isinstance(source, (str, Path)):
        with open(source, "rb") as f:
            raw = f.read()
    elif isinstance(source, bytes):
        raw = source
    elif hasattr(source, "read"):
        raw = source.read()
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    decompressed = decompress_nbt(raw)
    reader = NBTReader(io.BytesIO(decompressed))
    name, tag = reader.read_root()
    if not isinstance(tag, TAG_Compound):
        # Some special NBT roots might just be wrapped or non-compound
        compound = TAG_Compound()
        compound[name or "data"] = tag
        return (name, compound)
    return (name, tag)
