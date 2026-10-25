"""Tests for Litematica bit-packing and Sponge VarInt codecs."""

from __future__ import annotations

import random
import pytest

from schematic_toolkit.nbt import (
    calc_bits_per_block,
    pack_litematica_blocks,
    read_varint,
    read_varint_stream,
    unpack_litematica_blocks,
    write_varint,
    write_varint_stream,
)


def test_calc_bits_per_block() -> None:
    assert calc_bits_per_block(0) == 2
    assert calc_bits_per_block(1) == 2
    assert calc_bits_per_block(2) == 2
    assert calc_bits_per_block(3) == 2
    assert calc_bits_per_block(4) == 2
    assert calc_bits_per_block(5) == 3
    assert calc_bits_per_block(8) == 3
    assert calc_bits_per_block(9) == 4
    assert calc_bits_per_block(16) == 4
    assert calc_bits_per_block(17) == 5
    assert calc_bits_per_block(100) == 7


@pytest.mark.parametrize("bits", [2, 3, 4, 5, 7, 9, 12])
def test_litematica_bitpack_roundtrip(bits: int) -> None:
    max_val = (1 << bits) - 1
    # 200 elements is guaranteed to cross multiple 64-bit boundaries
    num_elements = 200
    rng = random.Random(42)
    original_indices = [rng.randint(0, max_val) for _ in range(num_elements)]

    packed_longs = pack_litematica_blocks(original_indices, bits)
    unpacked_indices = unpack_litematica_blocks(packed_longs, bits, num_elements)

    assert unpacked_indices == original_indices


def test_litematica_boundary_crossing() -> None:
    # 3 bits per block:
    # index 21 starts at bit 63.
    # bit 63 is in long 0. Bits 64 and 65 are in long 1.
    bits = 3
    indices = [0] * 30
    indices[21] = 5  # binary 101: bit 0 in long 0, bits 1 & 2 in long 1
    indices[22] = 7  # binary 111: bits in long 1

    packed = pack_litematica_blocks(indices, bits)
    unpacked = unpack_litematica_blocks(packed, bits, len(indices))
    assert unpacked[21] == 5
    assert unpacked[22] == 7
    assert unpacked == indices


def test_litematica_empty() -> None:
    assert pack_litematica_blocks([], 2) == []
    assert unpack_litematica_blocks([], 2, 0) == []


@pytest.mark.parametrize("val", [0, 1, 63, 127, 128, 255, 256, 16384, 2097151, 2147483647])
def test_varint_single_roundtrip(val: int) -> None:
    encoded = write_varint(val)
    import io
    stream = io.BytesIO(encoded)
    decoded = read_varint(stream)
    assert decoded == val


def test_varint_stream_roundtrip() -> None:
    test_values = [0, 1, 128, 500, 2048, 100000, 7, 42]
    encoded_bytes = write_varint_stream(test_values)
    decoded_values = read_varint_stream(encoded_bytes, len(test_values))
    assert decoded_values == test_values
