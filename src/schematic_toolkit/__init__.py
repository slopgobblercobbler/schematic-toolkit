"""schematic-toolkit: Ultimate Minecraft Schematic inspector, converter, and materials calculator."""

__version__ = "1.0.0"

from schematic_toolkit.exporters.ascii_art import render_ascii_layer_y, render_schematic_ascii
from schematic_toolkit.exporters.json_export import export_json
from schematic_toolkit.exporters.markdown import export_markdown
from schematic_toolkit.formats import (
    FormatHandler,
    LitematicHandler,
    SpongeSchematicHandler,
    VanillaStructureHandler,
    load_schematic,
    save_schematic,
)
from schematic_toolkit.materials.calculator import (
    MaterialEntry,
    ShoppingList,
    calculate_materials,
)
from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.region import Region
from schematic_toolkit.models.schematic import Schematic
from schematic_toolkit.operations.converter import convert_schematic_file
from schematic_toolkit.operations.slicer import slice_schematic_file, slice_schematic_y
from schematic_toolkit.operations.swapper import swap_palette, swap_schematic_file

__all__ = [
    "__version__",
    "BlockState",
    "Region",
    "Schematic",
    "FormatHandler",
    "LitematicHandler",
    "SpongeSchematicHandler",
    "VanillaStructureHandler",
    "load_schematic",
    "save_schematic",
    "calculate_materials",
    "ShoppingList",
    "MaterialEntry",
    "swap_palette",
    "swap_schematic_file",
    "slice_schematic_y",
    "slice_schematic_file",
    "convert_schematic_file",
    "render_ascii_layer_y",
    "render_schematic_ascii",
    "export_markdown",
    "export_json",
]
