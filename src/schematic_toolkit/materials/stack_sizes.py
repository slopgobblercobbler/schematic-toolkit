"""Minecraft stack sizes database and block-to-item drops mapping."""

from __future__ import annotations

from typing import Dict, Set

# Items that stack to a maximum of 16 in Minecraft Java Edition
STACK_16_PATTERNS: Set[str] = {
    # Signs and hanging signs
    "oak_sign", "spruce_sign", "birch_sign", "jungle_sign", "acacia_sign",
    "dark_oak_sign", "mangrove_sign", "cherry_sign", "bamboo_sign", "crimson_sign", "warped_sign",
    "oak_hanging_sign", "spruce_hanging_sign", "birch_hanging_sign", "jungle_hanging_sign",
    "acacia_hanging_sign", "dark_oak_hanging_sign", "mangrove_hanging_sign", "cherry_hanging_sign",
    "bamboo_hanging_sign", "crimson_hanging_sign", "warped_hanging_sign",
    # Banners
    "white_banner", "orange_banner", "magenta_banner", "light_blue_banner", "yellow_banner",
    "lime_banner", "pink_banner", "gray_banner", "light_gray_banner", "cyan_banner",
    "purple_banner", "blue_banner", "brown_banner", "green_banner", "red_banner", "black_banner",
    # Projectiles / Throwables
    "ender_pearl", "snowball", "egg",
    # Buckets & food
    "bucket", "honey_bottle",
    # Misc
    "armor_stand",
}

# Items that do not stack (stack size of 1)
STACK_1_PATTERNS: Set[str] = {
    # Beds
    "white_bed", "orange_bed", "magenta_bed", "light_blue_bed", "yellow_bed",
    "lime_bed", "pink_bed", "gray_bed", "light_gray_bed", "cyan_bed",
    "purple_bed", "blue_bed", "brown_bed", "green_bed", "red_bed", "black_bed",
    # Vehicles
    "boat", "oak_boat", "spruce_boat", "birch_boat", "jungle_boat", "acacia_boat",
    "dark_oak_boat", "mangrove_boat", "cherry_boat", "bamboo_raft",
    "chest_boat", "oak_chest_boat", "spruce_chest_boat", "birch_chest_boat", "jungle_chest_boat",
    "acacia_chest_boat", "dark_oak_chest_boat", "mangrove_chest_boat", "cherry_chest_boat",
    "bamboo_chest_raft",
    "minecart", "chest_minecart", "furnace_minecart", "tnt_minecart", "hopper_minecart",
    # Shulker boxes
    "shulker_box", "white_shulker_box", "orange_shulker_box", "magenta_shulker_box",
    "light_blue_shulker_box", "yellow_shulker_box", "lime_shulker_box", "pink_shulker_box",
    "gray_shulker_box", "light_gray_shulker_box", "cyan_shulker_box", "purple_shulker_box",
    "blue_shulker_box", "brown_shulker_box", "green_shulker_box", "red_shulker_box", "black_shulker_box",
    # Equipment & Potions
    "potion", "splash_potion", "lingering_potion",
    "totem_of_undying", "saddle", "elytra", "shield",
}

# Block to item mapping (for blocks that drop or are placed using a different item)
BLOCK_TO_ITEM_MAP: Dict[str, str] = {
    "minecraft:wall_torch": "minecraft:torch",
    "minecraft:soul_wall_torch": "minecraft:soul_torch",
    "minecraft:redstone_wall_torch": "minecraft:redstone_torch",
    "minecraft:redstone_wire": "minecraft:redstone",
    "minecraft:water": "minecraft:water_bucket",
    "minecraft:flowing_water": "minecraft:water_bucket",
    "minecraft:lava": "minecraft:lava_bucket",
    "minecraft:flowing_lava": "minecraft:lava_bucket",
    "minecraft:tripwire": "minecraft:string",
    "minecraft:wheat": "minecraft:wheat_seeds",
    "minecraft:carrots": "minecraft:carrot",
    "minecraft:potatoes": "minecraft:potato",
    "minecraft:beetroots": "minecraft:beetroot_seeds",
    "minecraft:cocoa": "minecraft:cocoa_beans",
    "minecraft:sweet_berry_bush": "minecraft:sweet_berries",
    "minecraft:cave_vines": "minecraft:glow_berries",
    "minecraft:cave_vines_plant": "minecraft:glow_berries",
    "minecraft:kelp_plant": "minecraft:kelp",
    "minecraft:bamboo_sapling": "minecraft:bamboo",
    "minecraft:attached_melon_stem": "minecraft:melon_seeds",
    "minecraft:attached_pumpkin_stem": "minecraft:pumpkin_seeds",
    "minecraft:melon_stem": "minecraft:melon_seeds",
    "minecraft:pumpkin_stem": "minecraft:pumpkin_seeds",
}


def get_item_for_block(block_name: str) -> str:
    """Map a placed block ID to the survival inventory item required to place it."""
    norm = block_name.strip()
    if ":" not in norm:
        norm = f"minecraft:{norm}"
    return BLOCK_TO_ITEM_MAP.get(norm, norm)


def get_stack_size(item_or_block_name: str) -> int:
    """Return the maximum stack size (64, 16, or 1) for the given item or block."""
    norm = item_or_block_name.strip()
    base = norm.split(":", 1)[1] if ":" in norm else norm

    # Check unstackable (1)
    if base in STACK_1_PATTERNS or base.endswith("_bed") or base.endswith("_boat") or base.endswith("shulker_box"):
        return 1

    # Check 16 stack
    if base in STACK_16_PATTERNS or base.endswith("_sign") or base.endswith("_banner"):
        return 16

    # Default is 64
    return 64
