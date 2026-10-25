"""Bitstream packing and unpacking routines.

Implements:
1. Litematica cross-boundary 64-bit continuous bit stream packing/unpacking
2. Minecraft VarInt stream encoding and decoding (for Sponge schematics)
"""

from __future__ import annotations

import io
from typing import BinaryIO, List, Sequence


def calc_bits_per_block(palette_size: int) -> int:
    """Calculate the number of bits per block index used by Litematica.

    Litematica enforces a minimum of 2 bits per block, and ceil(log2(palette_size)).
    """
    if palette_size <= 1:
        return 2
    bits = (palette_size - 1).bit_length()
    return max(2, bits)


def unpack_litematica_blocks(
    long_array: Sequence[int],
    bits_per_block: int,
    num_blocks: int,
) -> List[int]:
    """Unpack a continuous bit stream from an array of 64-bit longs.

    In Litematica, values are packed back-to-back and can cross 64-bit long boundaries.

    Args:
        long_array: Sequence of signed or unsigned 64-bit integers.
        bits_per_block: Bit width of each entry (>= 1).
        num_blocks: Expected number of decoded block indices.

    Returns:
        List of decoded block palette indices.
    """
    if num_blocks <= 0:
        return []
    if bits_per_block <= 0:
        return [0] * num_blocks

    # Convert all longs to unsigned 64-bit values
    u_longs = [x & 0xFFFFFFFFFFFFFFFF for x in long_array]
    num_longs = len(u_longs)
    mask = (1 << bits_per_block) - 1

    indices = [0] * num_blocks
    for idx in range(num_blocks):
        start_bit = idx * bits_per_block
        start_long = start_bit >> 6
        bit_offset = start_bit & 63

        if start_long >= num_longs:
            break

        if bit_offset + bits_per_block <= 64:
            indices[idx] = (u_longs[start_long] >> bit_offset) & mask
        else:
            bits_in_first = 64 - bit_offset
            bits_in_second = bits_per_block - bits_in_first
            part1 = (u_longs[start_long] >> bit_offset) & ((1 << bits_in_first) - 1)
            part2 = 0
            if start_long + 1 < num_longs:
                part2 = (u_longs[start_long + 1] & ((1 << bits_in_second) - 1)) << bits_in_first
            indices[idx] = part1 | part2

    return indices


def pack_litematica_blocks(
    indices: Sequence[int],
    bits_per_block: int,
) -> List[int]:
    """Pack an array of block palette indices into a continuous bit stream of 64-bit longs.

    Args:
        indices: Sequence of integer block palette indices.
        bits_per_block: Bit width per entry (>= 1).

    Returns:
        List of signed 64-bit integers suitable for TAG_Long_Array.
    """
    num_blocks = len(indices)
    if num_blocks == 0 or bits_per_block <= 0:
        return []

    total_bits = num_blocks * bits_per_block
    num_longs = (total_bits + 63) // 64
    u_longs = [0] * num_longs
    mask = (1 << bits_per_block) - 1

    for idx, raw_val in enumerate(indices):
        val = raw_val & mask
        start_bit = idx * bits_per_block
        start_long = start_bit >> 6
        bit_offset = start_bit & 63

        if bit_offset + bits_per_block <= 64:
            u_longs[start_long] |= (val << bit_offset)
        else:
            bits_in_first = 64 - bit_offset
            bits_in_second = bits_per_block - bits_in_first
            u_longs[start_long] |= ((val & ((1 << bits_in_first) - 1)) << bit_offset)
            if start_long + 1 < num_longs:
                u_longs[start_long + 1] |= ((val >> bits_in_first) & ((1 << bits_in_second) - 1))

    # Convert unsigned 64-bit to signed 64-bit representation
    signed_longs = []
    for x in u_longs:
        if x >= (1 << 63):
            signed_longs.append(x - (1 << 64))
        else:
            signed_longs.append(x)
    return signed_longs


def read_varint(stream: BinaryIO) -> int:
    """Read a single Minecraft VarInt from a binary stream."""
    val = 0
    shift = 0
    while True:
        b = stream.read(1)
        if not b:
            raise EOFError("Unexpected EOF reading VarInt")
        byte = b[0]
        val |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
        if shift > 35:
            raise ValueError("VarInt exceeds 35 bits")
    return val


def write_varint(value: int) -> bytes:
    """Encode an integer as a Minecraft VarInt byte sequence."""
    res = bytearray()
    val = value & 0xFFFFFFFF  # Treat as 32-bit int
    while True:
        if (val & ~0x7F) == 0:
            res.append(val)
            break
        else:
            res.append((val & 0x7F) | 0x80)
            val >>= 7
    return bytes(res)


def read_varint_stream(data: bytes, expected_count: int) -> List[int]:
    """Read a stream of VarInts from a byte buffer.

    Args:
        data: Raw byte array containing VarInts.
        expected_count: Number of VarInt entries to extract.
    """
    stream = io.BytesIO(data)
    results = [0] * expected_count
    for i in range(expected_count):
        results[i] = read_varint(stream)
    return results


def write_varint_stream(values: Sequence[int]) -> bytes:
    """Encode a sequence of integers into a continuous VarInt byte array."""
    out = io.BytesIO()
    for v in values:
        out.write(write_varint(v))
    return out.getvalue()
