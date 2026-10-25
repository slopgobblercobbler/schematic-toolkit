"""3D Volumetric Region model for Minecraft structures."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Sequence, Set, Tuple

from schematic_toolkit.models.block import BlockState


class Region:
    """Represents a 3D volume of Minecraft blocks with a palette of block states."""

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        length: int,
        offset_x: int = 0,
        offset_y: int = 0,
        offset_z: int = 0,
        palette: Optional[Sequence[BlockState]] = None,
        blocks: Optional[Sequence[int]] = None,
    ) -> None:
        if width <= 0 or height <= 0 or length <= 0:
            raise ValueError(f"Region dimensions must be positive integers: {width}x{height}x{length}")

        self.name = name
        self.width = int(width)
        self.height = int(height)
        self.length = int(length)
        self.offset_x = int(offset_x)
        self.offset_y = int(offset_y)
        self.offset_z = int(offset_z)

        # Initialize palette
        if palette is not None and len(palette) > 0:
            self.palette: List[BlockState] = list(palette)
        else:
            self.palette = [BlockState.air()]

        # Initialize blocks flat array: index = (y * length + z) * width + x
        expected_size = self.width * self.height * self.length
        if blocks is not None:
            if len(blocks) != expected_size:
                raise ValueError(
                    f"Block array size mismatch: expected {expected_size} (for {width}x{height}x{length}), got {len(blocks)}"
                )
            self.blocks: List[int] = list(blocks)
        else:
            self.blocks = [0] * expected_size

    @property
    def volume(self) -> int:
        """Total volume in cubic blocks (width * height * length)."""
        return self.width * self.height * self.length

    def get_index(self, x: int, y: int, z: int) -> int:
        """Calculate 1D array index from 3D relative coordinates."""
        if not (0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.length):
            raise IndexError(
                f"Coordinates ({x}, {y}, {z}) out of bounds for region size ({self.width}, {self.height}, {self.length})"
            )
        return (y * self.length + z) * self.width + x

    def get_coords(self, index: int) -> Tuple[int, int, int]:
        """Convert 1D array index back to (x, y, z) relative coordinates."""
        if not (0 <= index < self.volume):
            raise IndexError(f"Index {index} out of bounds for volume {self.volume}")
        x = index % self.width
        rem = index // self.width
        z = rem % self.length
        y = rem // self.length
        return (x, y, z)

    def get_block(self, x: int, y: int, z: int) -> BlockState:
        """Get the BlockState at relative coordinates (x, y, z)."""
        idx = self.get_index(x, y, z)
        palette_idx = self.blocks[idx]
        if 0 <= palette_idx < len(self.palette):
            return self.palette[palette_idx]
        return BlockState.air()

    def set_block(self, x: int, y: int, z: int, block_state: BlockState) -> None:
        """Set the BlockState at relative coordinates (x, y, z)."""
        idx = self.get_index(x, y, z)
        palette_idx = self.ensure_palette_entry(block_state)
        self.blocks[idx] = palette_idx

    def ensure_palette_entry(self, block_state: BlockState) -> int:
        """Ensure block_state exists in the palette, returning its index."""
        try:
            return self.palette.index(block_state)
        except ValueError:
            self.palette.append(block_state)
            return len(self.palette) - 1

    def count_by_state(self) -> Counter[BlockState]:
        """Count occurrences of each unique BlockState in the region."""
        counts: Counter[BlockState] = Counter()
        for palette_idx in self.blocks:
            if 0 <= palette_idx < len(self.palette):
                counts[self.palette[palette_idx]] += 1
            else:
                counts[BlockState.air()] += 1
        return counts

    def count_by_material(self, include_air: bool = False) -> Counter[str]:
        """Count occurrences of blocks grouped by block ID/name (e.g. 'minecraft:stone')."""
        material_counts: Counter[str] = Counter()
        for state, count in self.count_by_state().items():
            if not include_air and state.is_air:
                continue
            material_counts[state.name] += count
        return material_counts

    def total_blocks(self, include_air: bool = False) -> int:
        """Total count of placed blocks (excluding air by default)."""
        if include_air:
            return self.volume
        return sum(self.count_by_material(include_air=False).values())

    def compact_palette(self) -> None:
        """Remove unused or duplicate palette entries and re-index blocks."""
        used_indices = set(self.blocks)
        new_palette: List[BlockState] = []
        old_to_new: Dict[int, int] = {}

        # Always ensure air exists in palette
        air_state = BlockState.air()

        for old_idx, state in enumerate(self.palette):
            if old_idx in used_indices or state == air_state:
                if state not in new_palette:
                    new_idx = len(new_palette)
                    new_palette.append(state)
                    old_to_new[old_idx] = new_idx
                else:
                    old_to_new[old_idx] = new_palette.index(state)

        if not new_palette:
            new_palette = [air_state]

        # Update all block indices
        self.blocks = [old_to_new.get(idx, 0) for idx in self.blocks]
        self.palette = new_palette

    def substitute_palette(
        self,
        mapping: Dict[str, str],
        preserve_properties: bool = True,
    ) -> int:
        """Substitute block types according to mapping.

        Mapping keys and values can be:
        - Full names: "minecraft:stone" -> "minecraft:deepslate"
        - Short names: "stone" -> "deepslate"
        - Exact block state strings: "minecraft:oak_stairs[facing=north]" -> "minecraft:spruce_stairs[facing=north]"

        Args:
            mapping: Dictionary mapping source block patterns to target block patterns.
            preserve_properties: If True, keep original block properties unless overridden.

        Returns:
            Number of blocks altered in the region.
        """
        # Normalize mapping dictionary
        normalized_map: Dict[str, BlockState] = {}
        for src_str, dst_str in mapping.items():
            # Parse destination state
            dst_state = BlockState.from_string(dst_str)
            # Normalize source pattern
            src_str_norm = src_str.strip()
            if "[" not in src_str_norm and ":" not in src_str_norm:
                src_str_norm = f"minecraft:{src_str_norm}"
            normalized_map[src_str_norm] = dst_state

        # Precompute palette index replacements
        new_palette_indices: Dict[int, int] = {}
        affected_palette_indices: Set[int] = set()

        for old_idx, state in enumerate(self.palette):
            target_state: Optional[BlockState] = None

            # 1. Exact match with properties: "minecraft:oak_stairs[facing=north]"
            if state.to_string() in normalized_map:
                target_state = normalized_map[state.to_string()]
            # 2. Match by full name: "minecraft:stone"
            elif state.name in normalized_map:
                dest = normalized_map[state.name]
                if preserve_properties:
                    # Inherit state's properties, overriding with dest properties if any
                    merged_props = dict(state.properties)
                    merged_props.update(dest.properties)
                    target_state = BlockState(name=dest.name, properties=merged_props)
                else:
                    target_state = dest
            # 3. Match by short name: "stone"
            elif state.base_name in normalized_map:
                dest = normalized_map[state.base_name]
                if preserve_properties:
                    merged_props = dict(state.properties)
                    merged_props.update(dest.properties)
                    target_state = BlockState(name=dest.name, properties=merged_props)
                else:
                    target_state = dest

            if target_state is not None and target_state != state:
                affected_palette_indices.add(old_idx)
                # We update the palette entry in place or add new
                new_idx = self.ensure_palette_entry(target_state)
                new_palette_indices[old_idx] = new_idx

        if not affected_palette_indices:
            return 0

        # Apply remapped indices to block array
        altered_count = 0
        for i, val in enumerate(self.blocks):
            if val in affected_palette_indices:
                self.blocks[i] = new_palette_indices[val]
                altered_count += 1

        self.compact_palette()
        return altered_count

    def extract_subvolume(
        self,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int,
        min_z: int,
        max_z: int,
        recenter: bool = False,
    ) -> Region:
        """Extract a 3D subvolume bounding box into a new Region.

        Coordinates are inclusive: [min_x, max_x], [min_y, max_y], [min_z, max_z].

        Args:
            min_x: Minimum X coordinate (relative 0 to width - 1)
            max_x: Maximum X coordinate (relative 0 to width - 1)
            min_y: Minimum Y coordinate (relative 0 to height - 1)
            max_y: Maximum Y coordinate (relative 0 to height - 1)
            min_z: Minimum Z coordinate (relative 0 to length - 1)
            max_z: Maximum Z coordinate (relative 0 to length - 1)
            recenter: If True, set offset to (0,0,0); if False, preserve world offset.
        """
        # Clamp coordinates to boundaries
        clamped_min_x = max(0, min(min_x, self.width - 1))
        clamped_max_x = max(0, min(max_x, self.width - 1))
        clamped_min_y = max(0, min(min_y, self.height - 1))
        clamped_max_y = max(0, min(max_y, self.height - 1))
        clamped_min_z = max(0, min(min_z, self.length - 1))
        clamped_max_z = max(0, min(max_z, self.length - 1))

        if clamped_min_x > clamped_max_x or clamped_min_y > clamped_max_y or clamped_min_z > clamped_max_z:
            raise ValueError("Invalid slice bounds resulting in empty volume")

        sub_width = clamped_max_x - clamped_min_x + 1
        sub_height = clamped_max_y - clamped_min_y + 1
        sub_length = clamped_max_z - clamped_min_z + 1

        new_offset_x = 0 if recenter else (self.offset_x + clamped_min_x)
        new_offset_y = 0 if recenter else (self.offset_y + clamped_min_y)
        new_offset_z = 0 if recenter else (self.offset_z + clamped_min_z)

        sub_blocks: List[int] = [0] * (sub_width * sub_height * sub_length)
        new_palette = list(self.palette)

        for sy in range(sub_height):
            oy = clamped_min_y + sy
            for sz in range(sub_length):
                oz = clamped_min_z + sz
                for sx in range(sub_width):
                    ox = clamped_min_x + sx
                    orig_idx = self.get_index(ox, oy, oz)
                    new_idx = (sy * sub_length + sz) * sub_width + sx
                    sub_blocks[new_idx] = self.blocks[orig_idx]

        sub_region = Region(
            name=f"{self.name}_slice",
            width=sub_width,
            height=sub_height,
            length=sub_length,
            offset_x=new_offset_x,
            offset_y=new_offset_y,
            offset_z=new_offset_z,
            palette=new_palette,
            blocks=sub_blocks,
        )
        sub_region.compact_palette()
        return sub_region

    def clone(self) -> Region:
        """Create a deep copy of this region."""
        return Region(
            name=self.name,
            width=self.width,
            height=self.height,
            length=self.length,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            offset_z=self.offset_z,
            palette=list(self.palette),
            blocks=list(self.blocks),
        )

    def __repr__(self) -> str:
        return (
            f"Region('{self.name}', {self.width}x{self.height}x{self.length}, "
            f"offset=({self.offset_x},{self.offset_y},{self.offset_z}), "
            f"palette_size={len(self.palette)})"
        )
