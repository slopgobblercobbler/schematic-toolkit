"""Schematic format converter."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

from schematic_toolkit.formats import load_schematic, save_schematic
from schematic_toolkit.models.schematic import Schematic


def convert_schematic_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    output_format: Optional[str] = None,
) -> Tuple[Schematic, Path]:
    """Convert a schematic file to another format.

    Args:
        input_path: Source file (.litematic, .schem, .nbt).
        output_path: Destination file.
        output_format: Format name ("litematic", "sponge", "nbt"), or None to infer from extension.

    Returns:
        Tuple of (schematic, output_path)
    """
    in_p = Path(input_path).resolve()
    dest_p = Path(output_path).resolve()

    schematic = load_schematic(in_p)
    save_schematic(schematic, dest_p, format_name=output_format)

    return (schematic, dest_p)
