"""Tests for Markdown, JSON, and ASCII exporters."""

from __future__ import annotations

import json

from schematic_toolkit.exporters.ascii_art import render_ascii_layer_y, render_schematic_ascii
from schematic_toolkit.exporters.json_export import export_json
from schematic_toolkit.exporters.markdown import export_markdown
from schematic_toolkit.models.schematic import Schematic


def test_ascii_art_export(sample_schematic: Schematic) -> None:
    # Layer 0 is all stone floor (#)
    art_y0 = render_ascii_layer_y(sample_schematic.primary_region, y=0, show_legend=True)
    assert "Cross-Section: Region 'Main' at Layer Y=0" in art_y0
    assert "###" in art_y0
    assert "Stone (minecraft:stone)" in art_y0

    # Layer 1 has stairs, planks, torch
    art_y1 = render_ascii_layer_y(sample_schematic.primary_region, y=1, show_legend=True)
    assert "Cross-Section: Region 'Main' at Layer Y=1" in art_y1
    assert "Legend" in art_y1


def test_markdown_export(sample_schematic: Schematic) -> None:
    md = export_markdown(sample_schematic, include_diagram=True, sample_layer_y=0)
    assert "# Schematic Report: CozyCottage" in md
    assert "- **Author:** Notch" in md
    assert "3 x 3 x 3 blocks" in md
    assert "## Materials Shopping List" in md
    assert "## Layer Analysis (Y Axis)" in md
    assert "Cross-Section Diagram (Layer Y=0)" in md


def test_json_export(sample_schematic: Schematic) -> None:
    json_str = export_json(sample_schematic)
    data = json.loads(json_str)

    assert data["name"] == "CozyCottage"
    assert data["dimensions"] == {"width": 3, "height": 3, "length": 3}
    assert data["total_volume"] == 27
    assert data["total_blocks_placed"] == 16
    assert "materials" in data
    assert "layers" in data
    assert len(data["layers"]) == 3
