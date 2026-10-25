"""JSON data exporter for Minecraft schematics."""

from __future__ import annotations

import json
from typing import Any, Dict

from schematic_toolkit.materials.calculator import calculate_materials
from schematic_toolkit.models.schematic import Schematic


def export_json(
    schematic: Schematic,
    indent: int = 2,
    include_layer_summary: bool = True,
) -> str:
    """Export complete schematic metadata and shopping list as a JSON string."""
    primary = schematic.primary_region
    materials = calculate_materials(schematic, include_air=False)

    data: Dict[str, Any] = {
        "name": schematic.name,
        "author": schematic.author,
        "description": schematic.description,
        "source_format": schematic.source_format,
        "data_version": schematic.data_version,
        "dimensions": {
            "width": primary.width,
            "height": primary.height,
            "length": primary.length,
        },
        "total_volume": schematic.total_volume,
        "total_blocks_placed": schematic.total_blocks(include_air=False),
        "regions": {
            r_name: {
                "width": r.width,
                "height": r.height,
                "length": r.length,
                "offset": [r.offset_x, r.offset_y, r.offset_z],
                "blocks_placed": r.total_blocks(include_air=False),
                "palette_size": len(r.palette),
            }
            for r_name, r in schematic.regions.items()
        },
        "materials": materials.to_dict(),
    }

    if include_layer_summary:
        layers = []
        for y in range(primary.height):
            layer_blocks = 0
            layer_mats: Dict[str, int] = {}
            for z in range(primary.length):
                for x in range(primary.width):
                    b = primary.get_block(x, y, z)
                    if not b.is_air:
                        layer_blocks += 1
                        layer_mats[b.name] = layer_mats.get(b.name, 0) + 1
            layers.append({
                "y": y,
                "blocks_count": layer_blocks,
                "materials": layer_mats,
            })
        data["layers"] = layers

    return json.dumps(data, indent=indent)
