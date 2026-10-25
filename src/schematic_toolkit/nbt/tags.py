"""NBT (Named Binary Tag) data types.

Implements all standard Minecraft Java NBT tags (IDs 0-12) with full support
for type checking, serialization, representation, and dictionary/list-like operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, MutableMapping, MutableSequence, Optional, Sequence, Union


class TagId:
    END = 0
    BYTE = 1
    SHORT = 2
    INT = 3
    LONG = 4
    FLOAT = 5
    DOUBLE = 6
    BYTE_ARRAY = 7
    STRING = 8
    LIST = 9
    COMPOUND = 10
    INT_ARRAY = 11
    LONG_ARRAY = 12


class TAG(ABC):
    """Base class for all NBT tags."""

    tag_id: int = TagId.END

    @property
    @abstractmethod
    def value(self) -> Any:
        """The underlying Python value."""
        ...

    def to_native(self) -> Any:
        """Convert this tag recursively into native Python types (int, float, str, list, dict, bytes)."""
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


class TAG_End(TAG):
    tag_id = TagId.END

    @property
    def value(self) -> None:
        return None

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, TAG_End)


class TAG_Byte(TAG):
    tag_id = TagId.BYTE

    def __init__(self, value: int = 0) -> None:
        # 1 byte signed integer: -128 to 127
        if value > 127:
            value = (value & 0xFF) - 256 if (value & 0x80) else (value & 0x7F)
        elif value < -128:
            value = (value & 0xFF) - 256 if (value & 0x80) else (value & 0x7F)
        self._value = int(value)

    @property
    def value(self) -> int:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Byte):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __int__(self) -> int:
        return self._value


class TAG_Short(TAG):
    tag_id = TagId.SHORT

    def __init__(self, value: int = 0) -> None:
        # 2 byte signed integer: -32768 to 32767
        if value > 32767:
            value = (value & 0xFFFF) - 65536 if (value & 0x8000) else (value & 0x7FFF)
        elif value < -32768:
            value = (value & 0xFFFF) - 65536 if (value & 0x8000) else (value & 0x7FFF)
        self._value = int(value)

    @property
    def value(self) -> int:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Short):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __int__(self) -> int:
        return self._value


class TAG_Int(TAG):
    tag_id = TagId.INT

    def __init__(self, value: int = 0) -> None:
        # 4 byte signed integer: -2147483648 to 2147483647
        if value > 2147483647:
            value = (value & 0xFFFFFFFF) - 4294967296 if (value & 0x80000000) else (value & 0x7FFFFFFF)
        elif value < -2147483648:
            value = (value & 0xFFFFFFFF) - 4294967296 if (value & 0x80000000) else (value & 0x7FFFFFFF)
        self._value = int(value)

    @property
    def value(self) -> int:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Int):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __int__(self) -> int:
        return self._value


class TAG_Long(TAG):
    tag_id = TagId.LONG

    def __init__(self, value: int = 0) -> None:
        # 8 byte signed integer
        if value > 9223372036854775807:
            value = (value & 0xFFFFFFFFFFFFFFFF) - (1 << 64) if (value & (1 << 63)) else (value & 0x7FFFFFFFFFFFFFFF)
        elif value < -9223372036854775808:
            value = (value & 0xFFFFFFFFFFFFFFFF) - (1 << 64) if (value & (1 << 63)) else (value & 0x7FFFFFFFFFFFFFFF)
        self._value = int(value)

    @property
    def value(self) -> int:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Long):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __int__(self) -> int:
        return self._value


class TAG_Float(TAG):
    tag_id = TagId.FLOAT

    def __init__(self, value: float = 0.0) -> None:
        self._value = float(value)

    @property
    def value(self) -> float:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Float):
            return abs(self._value - other._value) < 1e-6
        if isinstance(other, (int, float)):
            return abs(self._value - float(other)) < 1e-6
        return False

    def __float__(self) -> float:
        return self._value


class TAG_Double(TAG):
    tag_id = TagId.DOUBLE

    def __init__(self, value: float = 0.0) -> None:
        self._value = float(value)

    @property
    def value(self) -> float:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Double):
            return abs(self._value - other._value) < 1e-12
        if isinstance(other, (int, float)):
            return abs(self._value - float(other)) < 1e-12
        return False

    def __float__(self) -> float:
        return self._value


class TAG_Byte_Array(TAG):
    tag_id = TagId.BYTE_ARRAY

    def __init__(self, value: Union[bytes, bytearray, Sequence[int]] = b"") -> None:
        if isinstance(value, (bytes, bytearray)):
            self._value = bytearray(value)
        else:
            self._value = bytearray(int(b) & 0xFF for b in value)

    @property
    def value(self) -> bytearray:
        return self._value

    def __len__(self) -> int:
        return len(self._value)

    def __getitem__(self, idx: Union[int, slice]) -> Any:
        return self._value[idx]

    def __setitem__(self, idx: int, val: int) -> None:
        self._value[idx] = val & 0xFF

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Byte_Array):
            return self._value == other._value
        if isinstance(other, (bytes, bytearray)):
            return self._value == other
        return False

    def to_native(self) -> bytes:
        return bytes(self._value)


class TAG_String(TAG):
    tag_id = TagId.STRING

    def __init__(self, value: str = "") -> None:
        self._value = str(value)

    @property
    def value(self) -> str:
        return self._value

    def __len__(self) -> int:
        return len(self._value)

    def __str__(self) -> str:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_String):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return False


class TAG_List(TAG, MutableSequence[TAG]):
    tag_id = TagId.LIST

    def __init__(
        self,
        element_type: int = TagId.END,
        elements: Optional[Sequence[TAG]] = None,
    ) -> None:
        self.element_type = element_type
        self._elements: List[TAG] = []
        if elements:
            for item in elements:
                self.append(item)

    @property
    def value(self) -> List[TAG]:
        return self._elements

    def __len__(self) -> int:
        return len(self._elements)

    def __getitem__(self, idx: int) -> TAG:
        return self._elements[idx]

    def __setitem__(self, idx: int, item: TAG) -> None:
        if self.element_type == TagId.END:
            self.element_type = item.tag_id
        elif item.tag_id != self.element_type:
            raise TypeError(
                f"Cannot insert tag of type {item.tag_id} into TAG_List of type {self.element_type}"
            )
        self._elements[idx] = item

    def __delitem__(self, idx: int) -> None:
        del self._elements[idx]
        if len(self._elements) == 0:
            self.element_type = TagId.END

    def insert(self, idx: int, item: TAG) -> None:
        if len(self._elements) == 0 and self.element_type == TagId.END:
            self.element_type = item.tag_id
        elif item.tag_id != self.element_type:
            raise TypeError(
                f"Cannot insert tag of type {item.tag_id} into TAG_List of type {self.element_type}"
            )
        self._elements.insert(idx, item)

    def append(self, item: TAG) -> None:
        self.insert(len(self._elements), item)

    def __iter__(self) -> Iterator[TAG]:
        return iter(self._elements)

    def to_native(self) -> List[Any]:
        return [item.to_native() for item in self._elements]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_List):
            return self.element_type == other.element_type and self._elements == other._elements
        return False


class TAG_Compound(TAG, MutableMapping[str, TAG]):
    tag_id = TagId.COMPOUND

    def __init__(self, tags: Optional[Dict[str, TAG]] = None) -> None:
        self._tags: Dict[str, TAG] = {}
        if tags:
            for k, v in tags.items():
                self[k] = v

    @property
    def value(self) -> Dict[str, TAG]:
        return self._tags

    def __len__(self) -> int:
        return len(self._tags)

    def __iter__(self) -> Iterator[str]:
        return iter(self._tags)

    def __contains__(self, key: object) -> bool:
        return key in self._tags

    def __getitem__(self, key: str) -> TAG:
        return self._tags[key]

    def __setitem__(self, key: str, value: Union[TAG, Any]) -> None:
        if not isinstance(value, TAG):
            value = native_to_tag(value)
        self._tags[str(key)] = value

    def __delitem__(self, key: str) -> None:
        del self._tags[key]

    def get_tag(self, key: str, default: Optional[TAG] = None) -> Optional[TAG]:
        return self._tags.get(key, default)

    def get_value(self, key: str, default: Any = None) -> Any:
        tag = self._tags.get(key)
        if tag is not None:
            return tag.value
        return default

    def to_native(self) -> Dict[str, Any]:
        return {k: v.to_native() for k, v in self._tags.items()}

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Compound):
            return self._tags == other._tags
        return False


class TAG_Int_Array(TAG, MutableSequence[int]):
    tag_id = TagId.INT_ARRAY

    def __init__(self, value: Optional[Sequence[int]] = None) -> None:
        self._value: List[int] = [int(x) for x in value] if value is not None else []

    @property
    def value(self) -> List[int]:
        return self._value

    def __len__(self) -> int:
        return len(self._value)

    def __getitem__(self, idx: int) -> int:
        return self._value[idx]

    def __setitem__(self, idx: int, val: int) -> None:
        self._value[idx] = int(val)

    def __delitem__(self, idx: int) -> None:
        del self._value[idx]

    def insert(self, idx: int, val: int) -> None:
        self._value.insert(idx, int(val))

    def append(self, val: int) -> None:
        self._value.append(int(val))

    def __iter__(self) -> Iterator[int]:
        return iter(self._value)

    def to_native(self) -> List[int]:
        return list(self._value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Int_Array):
            return self._value == other._value
        if isinstance(other, list):
            return self._value == other
        return False


class TAG_Long_Array(TAG, MutableSequence[int]):
    tag_id = TagId.LONG_ARRAY

    def __init__(self, value: Optional[Sequence[int]] = None) -> None:
        self._value: List[int] = [int(x) for x in value] if value is not None else []

    @property
    def value(self) -> List[int]:
        return self._value

    def __len__(self) -> int:
        return len(self._value)

    def __getitem__(self, idx: int) -> int:
        return self._value[idx]

    def __setitem__(self, idx: int, val: int) -> None:
        self._value[idx] = int(val)

    def __delitem__(self, idx: int) -> None:
        del self._value[idx]

    def insert(self, idx: int, val: int) -> None:
        self._value.insert(idx, int(val))

    def append(self, val: int) -> None:
        self._value.append(int(val))

    def __iter__(self) -> Iterator[int]:
        return iter(self._value)

    def to_native(self) -> List[int]:
        return list(self._value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TAG_Long_Array):
            return self._value == other._value
        if isinstance(other, list):
            return self._value == other
        return False


TAG_MAP: Dict[int, type] = {
    TagId.END: TAG_End,
    TagId.BYTE: TAG_Byte,
    TagId.SHORT: TAG_Short,
    TagId.INT: TAG_Int,
    TagId.LONG: TAG_Long,
    TagId.FLOAT: TAG_Float,
    TagId.DOUBLE: TAG_Double,
    TagId.BYTE_ARRAY: TAG_Byte_Array,
    TagId.STRING: TAG_String,
    TagId.LIST: TAG_List,
    TagId.COMPOUND: TAG_Compound,
    TagId.INT_ARRAY: TAG_Int_Array,
    TagId.LONG_ARRAY: TAG_Long_Array,
}


def native_to_tag(obj: Any) -> TAG:
    """Recursively convert a native Python object to an appropriate NBT tag."""
    if isinstance(obj, TAG):
        return obj
    if isinstance(obj, bool):
        return TAG_Byte(1 if obj else 0)
    if isinstance(obj, int):
        if -128 <= obj <= 127:
            return TAG_Int(obj)  # Default ints to TAG_Int
        elif -2147483648 <= obj <= 2147483647:
            return TAG_Int(obj)
        else:
            return TAG_Long(obj)
    if isinstance(obj, float):
        return TAG_Double(obj)
    if isinstance(obj, str):
        return TAG_String(obj)
    if isinstance(obj, (bytes, bytearray)):
        return TAG_Byte_Array(obj)
    if isinstance(obj, dict):
        return TAG_Compound({k: native_to_tag(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            return TAG_List(TagId.END)
        converted = [native_to_tag(item) for item in obj]
        first_type = converted[0].tag_id
        # All items in TAG_List must have matching type
        for item in converted:
            if item.tag_id != first_type:
                # Fallback to compound if mixed
                raise ValueError(
                    f"TAG_List requires homogeneous element types, but got {first_type} and {item.tag_id}"
                )
        return TAG_List(first_type, converted)
    raise TypeError(f"Cannot convert object of type {type(obj)} to NBT tag")
