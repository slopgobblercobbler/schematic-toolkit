"""BlockState representation and parsing for Minecraft blocks."""

from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional

AIR_BLOCKS = {
    "minecraft:air",
    "minecraft:cave_air",
    "minecraft:void_air",
    "air",
    "cave_air",
    "void_air",
}

_BLOCK_STATE_REGEX = re.compile(r"^([^\[]+)(?:\[(.*)\])?$")


class BlockState:
    """Represents an immutable, hashable Minecraft block state with an optional property map."""

    def __init__(
        self,
        name: str,
        properties: Optional[Mapping[str, str]] = None,
    ) -> None:
        norm_name = name.strip()
        if ":" not in norm_name:
            norm_name = f"minecraft:{norm_name}"
        self.name: str = norm_name

        if properties:
            self.properties: Dict[str, str] = {
                str(k).strip(): str(v).strip()
                for k, v in sorted(properties.items())
            }
        else:
            self.properties = {}

        self._hash: Optional[int] = None

    @classmethod
    def air(cls) -> BlockState:
        """Create a default minecraft:air block state."""
        return cls("minecraft:air")

    @classmethod
    def from_string(cls, state_str: str) -> BlockState:
        """Parse a block state string into a BlockState object.

        Examples:
            "minecraft:stone"
            "stone"
            "minecraft:oak_stairs[facing=north,half=bottom]"
            "oak_log[axis=y]"
        """
        match = _BLOCK_STATE_REGEX.match(state_str.strip())
        if not match:
            raise ValueError(f"Invalid block state string: {state_str}")

        raw_name, raw_props = match.groups()
        props: Dict[str, str] = {}
        if raw_props:
            for pair in raw_props.split(","):
                pair = pair.strip()
                if not pair:
                    continue
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    props[k.strip()] = v.strip()
                else:
                    props[pair] = ""

        return cls(name=raw_name.strip(), properties=props)

    def to_string(self) -> str:
        """Format as canonical Minecraft block state string: namespace:id[key1=val1,key2=val2]."""
        if not self.properties:
            return self.name
        props_str = ",".join(f"{k}={v}" for k, v in sorted(self.properties.items()))
        return f"{self.name}[{props_str}]"

    @property
    def is_air(self) -> bool:
        """Check whether this block represents an air block."""
        return self.name in AIR_BLOCKS

    @property
    def namespace(self) -> str:
        """Return the namespace part (e.g. 'minecraft')."""
        return self.name.split(":", 1)[0]

    @property
    def base_name(self) -> str:
        """Return the block name without namespace (e.g. 'stone', 'oak_stairs')."""
        return self.name.split(":", 1)[1] if ":" in self.name else self.name

    @property
    def display_name(self) -> str:
        """Return a human-readable title (e.g. 'Oak Stairs')."""
        return self.base_name.replace("_", " ").title()

    def with_name(self, new_name: str, keep_properties: bool = True) -> BlockState:
        """Return a new BlockState with a new name, optionally keeping properties."""
        return BlockState(
            name=new_name,
            properties=self.properties if keep_properties else {},
        )

    def with_properties(self, **new_properties: str) -> BlockState:
        """Return a new BlockState with updated properties."""
        updated = dict(self.properties)
        updated.update(new_properties)
        return BlockState(name=self.name, properties=updated)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.name, tuple(sorted(self.properties.items()))))
        return self._hash

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BlockState):
            return False
        return self.name == other.name and self.properties == other.properties

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        if self.properties:
            return f"BlockState({self.name!r}, {self.properties!r})"
        return f"BlockState({self.name!r})"
