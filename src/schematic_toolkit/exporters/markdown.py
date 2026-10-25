"""Markdown report exporter for Minecraft schematics."""

from __future__ import annotations

from typing import List, Optional

from schematic_toolkit.exporters.ascii_art import render_ascii_layer_y
from schematic_toolkit.materials.calculator import calculate_materials
from schematic_toolkit.models.schematic import Schematic


def export_markdown(
    schematic: Schematic,
    include_diagram: bool = True,
    sample_layer_y: Optional[int] = None,
) -> str:
    """Generate a comprehensive Markdown documentation report for a schematic."""
    primary = schematic.primary_region
    materials = calculate_materials(schematic, include_air=False)

    lines: List[str] = [
        f"# Schematic Report: {schematic.name}",
        "",
        "## Overview",
        "",
        f"- **Author:** {schematic.author or 'Unknown'}",
        f"- **Description:** {schematic.description or 'None'}",
        f"- **Format:** {schematic.source_format.upper()}",
        f"- **DataVersion:** {schematic.data_version}",
        f"- **Dimensions (WxHxL):** {primary.width} x {primary.height} x {primary.length} blocks",
        f"- **Total Volume:** {schematic.total_volume:,} blocks",
        f"- **Total Blocks Placed:** {schematic.total_blocks(include_air=False):,} blocks",
        f"- **Regions Count:** {len(schematic.regions)}",
        "",
    ]

    # Region details if multiple
    if len(schematic.regions) > 1:
        lines.append("## Regions")
        lines.append("")
        lines.append("| Region Name | Width | Height | Length | Offset (X,Y,Z) | Blocks |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
        for r_name, r in schematic.regions.items():
            lines.append(
                f"| `{r_name}` | {r.width} | {r.height} | {r.length} | "
                f"({r.offset_x}, {r.offset_y}, {r.offset_z}) | {r.total_blocks(include_air=False):,} |"
            )
        lines.append("")

    # Materials Shopping List
    lines.append("## Materials Shopping List")
    lines.append("")
    lines.append(f"- **Total Items:** {materials.total_items:,}")
    lines.append(f"- **Unique Materials:** {materials.total_unique_items}")
    lines.append(f"- **Inventory Slots:** {materials.total_inventory_slots:,}")
    lines.append(f"- **Compacted Shulker Boxes (~27 slots):** {materials.total_shulker_boxes_compacted} SBs")
    lines.append(f"- **Dedicated Shulker Boxes:** {materials.total_shulker_boxes_dedicated} SBs")
    lines.append("")
    lines.append("| Material | ID | Total Count | Stack Size | Breakdown (SB + Stacks + Remainder) |")
    lines.append("| :--- | :--- | :---: | :---: | :--- |")
    for m in materials.items:
        lines.append(
            f"| {m.display_name} | `{m.item_id}` | {m.count:,} | {m.stack_size} | {m.formatted_breakdown} |"
        )
    lines.append("")

    # Layer by layer summary
    lines.append("## Layer Analysis (Y Axis)")
    lines.append("")
    lines.append("| Layer (Y) | Placed Blocks | Fill Ratio | Dominant Material |")
    lines.append("| :---: | :---: | :---: | :--- |")
    layer_area = primary.width * primary.length
    for y in range(primary.height):
        placed_in_layer = 0
        layer_materials = {}
        for z in range(primary.length):
            for x in range(primary.width):
                b = primary.get_block(x, y, z)
                if not b.is_air:
                    placed_in_layer += 1
                    layer_materials[b.name] = layer_materials.get(b.name, 0) + 1

        dominant = max(layer_materials.items(), key=lambda item: item[1])[0] if layer_materials else "Air"
        dom_clean = dominant.split(":", 1)[1].replace("_", " ").title() if ":" in dominant else dominant
        fill_pct = (placed_in_layer / layer_area) * 100 if layer_area > 0 else 0.0
        lines.append(f"| Y={y} | {placed_in_layer:,} | {fill_pct:.1f}% | {dom_clean} |")
    lines.append("")

    # Sample ASCII Diagram
    if include_diagram:
        target_y = sample_layer_y if sample_layer_y is not None else 0
        target_y = min(max(0, target_y), primary.height - 1)
        lines.append(f"## Cross-Section Diagram (Layer Y={target_y})")
        lines.append("")
        lines.append("```text")
        diagram_text = render_ascii_layer_y(primary, target_y, show_legend=True)
        lines.append(diagram_text)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)
