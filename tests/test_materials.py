"""Tests for materials calculator and shopping list generation."""

from __future__ import annotations

from schematic_toolkit.materials import (
    MaterialEntry,
    ShoppingList,
    calculate_materials,
    get_item_for_block,
    get_stack_size,
)
from schematic_toolkit.models.schematic import Schematic


def test_stack_sizes() -> None:
    assert get_stack_size("minecraft:stone") == 64
    assert get_stack_size("minecraft:oak_planks") == 64
    assert get_stack_size("minecraft:ender_pearl") == 16
    assert get_stack_size("minecraft:oak_sign") == 16
    assert get_stack_size("minecraft:white_banner") == 16
    assert get_stack_size("minecraft:egg") == 16
    assert get_stack_size("minecraft:red_bed") == 1
    assert get_stack_size("minecraft:minecart") == 1
    assert get_stack_size("minecraft:oak_boat") == 1
    assert get_stack_size("minecraft:shulker_box") == 1


def test_item_block_mapping() -> None:
    assert get_item_for_block("minecraft:wall_torch") == "minecraft:torch"
    assert get_item_for_block("minecraft:redstone_wire") == "minecraft:redstone"
    assert get_item_for_block("minecraft:water") == "minecraft:water_bucket"
    assert get_item_for_block("minecraft:stone") == "minecraft:stone"


def test_material_entry_formatting() -> None:
    # 64-stack item, exact count 10
    entry1 = MaterialEntry.from_count("minecraft:stone", 10)
    assert entry1.count == 10
    assert entry1.full_stacks == 0
    assert entry1.remainder_items == 10
    assert entry1.shulker_boxes == 0
    assert entry1.formatted_breakdown == "10 items"

    # 64-stack item: 150 items = 2 stacks + 22 items
    entry2 = MaterialEntry.from_count("minecraft:stone", 150)
    assert entry2.full_stacks == 2
    assert entry2.remainder_items == 22
    assert entry2.shulker_boxes == 0
    assert entry2.formatted_breakdown == "2 stacks + 22 items"

    # 64-stack item: 2000 items (1 SB = 1728 items. 2000 - 1728 = 272. 272 // 64 = 4 stacks, rem 16)
    entry3 = MaterialEntry.from_count("minecraft:stone", 2000)
    assert entry3.shulker_boxes == 1
    assert entry3.remainder_stacks == 4
    assert entry3.remainder_items == 16
    assert entry3.formatted_breakdown == "1 SB + 4 stacks + 16 items"

    # 16-stack item: 35 ender pearls (2 stacks of 16 + 3 items)
    entry4 = MaterialEntry.from_count("minecraft:ender_pearl", 35)
    assert entry4.stack_size == 16
    assert entry4.full_stacks == 2
    assert entry4.remainder_items == 3
    assert entry4.formatted_breakdown == "2 stacks + 3 items"

    # 1-stack item: 5 beds
    entry5 = MaterialEntry.from_count("minecraft:red_bed", 5)
    assert entry5.stack_size == 1
    assert entry5.full_stacks == 5
    assert entry5.remainder_items == 0
    assert entry5.formatted_breakdown == "5 stacks"


def test_calculate_materials_shopping_list(sample_schematic: Schematic) -> None:
    shopping_list = calculate_materials(sample_schematic, include_air=False)

    assert shopping_list.schematic_name == "CozyCottage"
    assert shopping_list.total_unique_items == 6  # stone, planks, stairs, torch, sign, bed
    assert shopping_list.total_items == 16  # 9 stone + 3 planks + 1 stairs + 1 torch + 1 sign + 1 bed

    # Stone is highest count (9)
    top_item = shopping_list.items[0]
    assert top_item.item_id == "minecraft:stone"
    assert top_item.count == 9

    # Markdown export
    md = shopping_list.to_markdown()
    assert "# Materials Shopping List" in md
    assert "minecraft:stone" in md
    assert "| Stone | `minecraft:stone` | 9 | 64 | 9 items |" in md

    # CSV export
    csv_text = shopping_list.to_csv()
    assert "Stone,minecraft:stone,9,64,0,9,0,9 items" in csv_text

    # JSON export
    data = shopping_list.to_dict()
    assert data["total_items"] == 16
    assert data["total_unique_items"] == 6


def test_calculate_materials_sort_by_name(sample_schematic: Schematic) -> None:
    sl = calculate_materials(sample_schematic, sort_by="name")
    names = [i.display_name for i in sl.items]
    assert names == sorted(names, key=lambda s: s.lower())


def test_include_air(sample_schematic: Schematic) -> None:
    sl_no_air = calculate_materials(sample_schematic, include_air=False)
    sl_with_air = calculate_materials(sample_schematic, include_air=True)
    assert sl_with_air.total_items > sl_no_air.total_items
    air_entries = [m for m in sl_with_air.items if "air" in m.item_id]
    assert len(air_entries) > 0
