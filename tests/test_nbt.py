"""Tests for NBT tags, reader, and writer."""

from __future__ import annotations

import io
import pytest

from schematic_toolkit.nbt import (
    NBTFormatError,
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
    native_to_tag,
    read_nbt,
    write_nbt,
)


def test_primitive_tags() -> None:
    b = TAG_Byte(42)
    assert b.value == 42
    assert b == 42
    assert int(b) == 42

    s = TAG_Short(30000)
    assert s.value == 30000
    assert int(s) == 30000

    i = TAG_Int(-123456)
    assert i.value == -123456
    assert int(i) == -123456

    l = TAG_Long(98765432109876)
    assert l.value == 98765432109876

    f = TAG_Float(3.14)
    assert abs(f.value - 3.14) < 1e-4

    d = TAG_Double(2.718281828459)
    assert abs(d.value - 2.718281828459) < 1e-9

    st = TAG_String("Minecraft")
    assert st.value == "Minecraft"
    assert str(st) == "Minecraft"
    assert len(st) == 9


def test_array_tags() -> None:
    ba = TAG_Byte_Array(b"\x01\x02\x03\xFF")
    assert len(ba) == 4
    assert ba[3] == 255
    ba[0] = 42
    assert ba[0] == 42
    assert ba.to_native() == b"\x2a\x02\x03\xFF"

    ia = TAG_Int_Array([10, -20, 30])
    assert len(ia) == 3
    assert ia[1] == -20
    ia.append(40)
    assert len(ia) == 4
    assert ia.to_native() == [10, -20, 30, 40]

    la = TAG_Long_Array([1000000000, 2000000000])
    assert len(la) == 2
    assert la[0] == 1000000000
    la.append(3000000000)
    assert len(la) == 3


def test_compound_and_list() -> None:
    comp = TAG_Compound()
    comp["name"] = TAG_String("Alex")
    comp["score"] = TAG_Int(100)
    comp["active"] = TAG_Byte(1)

    assert len(comp) == 3
    assert "name" in comp
    assert comp.get_value("score") == 100
    assert comp.get_value("nonexistent", "default") == "default"

    # List
    tag_list = TAG_List(TagId.STRING)
    tag_list.append(TAG_String("item1"))
    tag_list.append(TAG_String("item2"))
    assert len(tag_list) == 2
    assert tag_list[0].value == "item1"

    # Mixed type insertion raises TypeError
    with pytest.raises(TypeError):
        tag_list.append(TAG_Int(10))

    comp["items"] = tag_list

    native = comp.to_native()
    assert native["name"] == "Alex"
    assert native["score"] == 100
    assert native["items"] == ["item1", "item2"]


def test_native_to_tag() -> None:
    data = {
        "text": "hello",
        "num": 42,
        "float_num": 3.5,
        "flag": True,
        "bytes_field": b"raw",
        "list_field": [1, 2, 3],
    }
    tag = native_to_tag(data)
    assert isinstance(tag, TAG_Compound)
    assert tag.get_value("text") == "hello"
    assert tag.get_value("flag") == 1


def test_nbt_roundtrip_uncompressed() -> None:
    comp = TAG_Compound()
    comp["title"] = TAG_String("Test Schematic")
    comp["count"] = TAG_Int(99)
    comp["coords"] = TAG_List(TagId.INT, [TAG_Int(1), TAG_Int(2), TAG_Int(3)])
    comp["sub"] = TAG_Compound({"key": TAG_String("value")})
    comp["byte_data"] = TAG_Byte_Array(b"\xde\xad\xbe\xef")
    comp["long_data"] = TAG_Long_Array([100, 200, 300])

    buf = io.BytesIO()
    write_nbt(comp, buf, root_name="Root", compress=False)
    raw = buf.getvalue()

    buf.seek(0)
    name, loaded = read_nbt(buf)
    assert name == "Root"
    assert loaded["title"].value == "Test Schematic"
    assert loaded["count"].value == 99
    assert loaded["coords"].to_native() == [1, 2, 3]
    assert loaded["sub"]["key"].value == "value"
    assert bytes(loaded["byte_data"].value) == b"\xde\xad\xbe\xef"
    assert loaded["long_data"].to_native() == [100, 200, 300]


def test_nbt_roundtrip_gzip() -> None:
    comp = TAG_Compound()
    comp["magic"] = TAG_String("GzipTest")
    comp["values"] = TAG_Int_Array([1, 2, 3, 4, 5])

    buf = io.BytesIO()
    write_nbt(comp, buf, root_name="", compress=True)
    raw = buf.getvalue()
    assert raw[:2] == b"\x1f\x8b"  # Gzip magic header

    buf.seek(0)
    name, loaded = read_nbt(buf)
    assert loaded["magic"].value == "GzipTest"
    assert loaded["values"].to_native() == [1, 2, 3, 4, 5]


def test_corrupted_nbt() -> None:
    with pytest.raises(Exception):
        read_nbt(b"\x0a\x00\x05title\x99")
