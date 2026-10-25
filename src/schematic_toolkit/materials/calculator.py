"""Materials shopping list calculator for Minecraft schematics."""

from __future__ import annotations

import csv
import io
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from schematic_toolkit.materials.stack_sizes import get_item_for_block, get_stack_size
from schematic_toolkit.models.schematic import Schematic


@dataclass
class MaterialEntry:
    """Represents an item in the materials shopping list."""

    item_id: str
    display_name: str
    count: int
    stack_size: int
    full_stacks: int
    remainder_items: int
    shulker_boxes: int
    remainder_stacks: int
    shulker_box_estimate: float

    @classmethod
    def from_count(cls, item_id: str, count: int) -> MaterialEntry:
        stack_size = get_stack_size(item_id)
        full_stacks = count // stack_size
        remainder_items = count % stack_size

        shulker_capacity = 27 * stack_size
        shulker_boxes = count // shulker_capacity
        items_in_last_sb = count % shulker_capacity
        remainder_stacks = items_in_last_sb // stack_size

        shulker_box_estimate = count / shulker_capacity

        base = item_id.split(":", 1)[1] if ":" in item_id else item_id
        display_name = base.replace("_", " ").title()

        return cls(
            item_id=item_id,
            display_name=display_name,
            count=count,
            stack_size=stack_size,
            full_stacks=full_stacks,
            remainder_items=remainder_items,
            shulker_boxes=shulker_boxes,
            remainder_stacks=remainder_stacks,
            shulker_box_estimate=shulker_box_estimate,
        )

    @property
    def formatted_breakdown(self) -> str:
        """Human-readable breakdown: e.g. '1 SB + 3 stacks + 14 items' or '4 stacks + 10 items'."""
        parts = []
        if self.shulker_boxes > 0:
            sb_word = "SB" if self.shulker_boxes == 1 else "SBs"
            parts.append(f"{self.shulker_boxes} {sb_word}")

        if self.remainder_stacks > 0:
            s_word = "stack" if self.remainder_stacks == 1 else "stacks"
            parts.append(f"{self.remainder_stacks} {s_word}")
        elif self.shulker_boxes == 0 and self.full_stacks > 0:
            s_word = "stack" if self.full_stacks == 1 else "stacks"
            parts.append(f"{self.full_stacks} {s_word}")

        if self.remainder_items > 0:
            i_word = "item" if self.remainder_items == 1 else "items"
            parts.append(f"{self.remainder_items} {i_word}")

        if not parts:
            return "0 items"
        return " + ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "display_name": self.display_name,
            "total_count": self.count,
            "stack_size": self.stack_size,
            "full_stacks": self.full_stacks,
            "remainder_items": self.remainder_items,
            "shulker_boxes": self.shulker_boxes,
            "remainder_stacks": self.remainder_stacks,
            "shulker_box_estimate": round(self.shulker_box_estimate, 2),
            "formatted": self.formatted_breakdown,
        }


@dataclass
class ShoppingList:
    """Complete materials shopping list for a schematic."""

    items: List[MaterialEntry]
    schematic_name: str
    total_blocks_placed: int
    total_unique_items: int

    @property
    def total_items(self) -> int:
        return sum(item.count for item in self.items)

    @property
    def total_inventory_slots(self) -> int:
        """Total slots required (count / stack_size rounded up per item)."""
        return sum(math.ceil(item.count / item.stack_size) for item in self.items)

    @property
    def total_shulker_boxes_dedicated(self) -> int:
        """Total shulkers needed if each item has dedicated shulker boxes."""
        return sum(math.ceil(item.shulker_box_estimate) for item in self.items)

    @property
    def total_shulker_boxes_compacted(self) -> float:
        """Theoretical minimum shulkers if slots are packed together efficiently."""
        return round(self.total_inventory_slots / 27.0, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schematic_name": self.schematic_name,
            "total_blocks_placed": self.total_blocks_placed,
            "total_items": self.total_items,
            "total_unique_items": self.total_unique_items,
            "total_inventory_slots": self.total_inventory_slots,
            "total_shulker_boxes_dedicated": self.total_shulker_boxes_dedicated,
            "total_shulker_boxes_compacted": self.total_shulker_boxes_compacted,
            "materials": [item.to_dict() for item in self.items],
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Materials Shopping List: {self.schematic_name}",
            "",
            f"- **Total Items Placed:** {self.total_items:,}",
            f"- **Unique Materials:** {self.total_unique_items}",
            f"- **Inventory Slots Required:** {self.total_inventory_slots:,} slots",
            f"- **Compacted Shulker Boxes (~27 slots):** {self.total_shulker_boxes_compacted} SBs",
            f"- **Dedicated Shulker Boxes:** {self.total_shulker_boxes_dedicated} SBs",
            "",
            "| Item | ID | Total Count | Stack Size | Breakdown (SB + Stacks + Items) |",
            "| :--- | :--- | :---: | :---: | :--- |",
        ]
        for m in self.items:
            lines.append(
                f"| {m.display_name} | `{m.item_id}` | {m.count:,} | {m.stack_size} | {m.formatted_breakdown} |"
            )
        return "\n".join(lines)

    def to_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Item Name",
            "Item ID",
            "Total Count",
            "Stack Size",
            "Full Stacks",
            "Remainder Items",
            "Shulker Boxes",
            "Breakdown",
        ])
        for m in self.items:
            writer.writerow([
                m.display_name,
                m.item_id,
                m.count,
                m.stack_size,
                m.full_stacks,
                m.remainder_items,
                m.shulker_boxes,
                m.formatted_breakdown,
            ])
        return output.getvalue()


def calculate_materials(
    schematic: Schematic,
    include_air: bool = False,
    map_to_items: bool = True,
    sort_by: str = "count",
) -> ShoppingList:
    """Calculate the exact material shopping list for a schematic.

    Args:
        schematic: The input Schematic.
        include_air: Whether to include air blocks in the list.
        map_to_items: If True, map blocks to their placing item (e.g. wall torches -> torch).
        sort_by: 'count' (descending) or 'name' (alphabetical).

    Returns:
        ShoppingList object.
    """
    raw_counts = schematic.material_counts(include_air=include_air)

    item_counts: Counter[str] = Counter()
    for block_name, count in raw_counts.items():
        if map_to_items:
            item_id = get_item_for_block(block_name)
        else:
            item_id = block_name
        item_counts[item_id] += count

    entries: List[MaterialEntry] = [
        MaterialEntry.from_count(item_id, count)
        for item_id, count in item_counts.items()
    ]

    if sort_by == "name":
        entries.sort(key=lambda x: x.display_name.lower())
    else:
        entries.sort(key=lambda x: x.count, reverse=True)

    return ShoppingList(
        items=entries,
        schematic_name=schematic.name,
        total_blocks_placed=schematic.total_blocks(include_air=False),
        total_unique_items=len(entries),
    )
