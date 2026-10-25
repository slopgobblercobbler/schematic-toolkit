"""Schematic format readers, writers, and automatic format detection."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO, Dict, Optional, Type, Union

from schematic_toolkit.formats.base import FormatHandler
from schematic_toolkit.formats.litematic import LitematicHandler
from schematic_toolkit.formats.sponge import SpongeSchematicHandler
from schematic_toolkit.formats.vanilla_nbt import VanillaStructureHandler
from schematic_toolkit.models.schematic import Schematic
from schematic_toolkit.nbt import read_nbt

HANDLERS: Dict[str, Type[FormatHandler]] = {
    "litematic": LitematicHandler,
    "sponge": SpongeSchematicHandler,
    "schem": SpongeSchematicHandler,
    "vanilla_nbt": VanillaStructureHandler,
    "nbt": VanillaStructureHandler,
}

EXTENSION_MAP: Dict[str, Type[FormatHandler]] = {
    ".litematic": LitematicHandler,
    ".schem": SpongeSchematicHandler,
    ".nbt": VanillaStructureHandler,
}


def detect_format_from_data(source: Union[str, Path, bytes, BinaryIO]) -> str:
    """Detect schematic format by inspecting NBT tags or file extension."""
    if isinstance(source, (str, Path)):
        ext = Path(source).suffix.lower()
        if ext == ".litematic":
            return "litematic"
        elif ext == ".schem":
            return "sponge"
        elif ext == ".nbt":
            return "vanilla_nbt"

    # Inspect internal NBT root
    try:
        _, root = read_nbt(source)
        if "Regions" in root:
            return "litematic"
        if "BlockData" in root or "Palette" in root or "BlockPalette" in root:
            return "sponge"
        if "size" in root and "palette" in root and "blocks" in root:
            return "vanilla_nbt"
    except Exception:
        pass

    return "litematic"


def load_schematic(
    source: Union[str, Path, bytes, BinaryIO],
    format_name: Optional[str] = None,
) -> Schematic:
    """Load a schematic from a file path, bytes, or binary stream.

    Args:
        source: Path or binary stream.
        format_name: Explicit format name ("litematic", "sponge", "nbt"), or None for auto-detection.

    Returns:
        Schematic instance.
    """
    if not format_name:
        format_name = detect_format_from_data(source)

    norm_name = format_name.lower().replace(".", "")
    handler_cls = HANDLERS.get(norm_name)
    if not handler_cls:
        raise ValueError(
            f"Unsupported format '{format_name}'. Supported formats: {list(HANDLERS.keys())}"
        )

    handler = handler_cls()
    return handler.read(source)


def save_schematic(
    schematic: Schematic,
    target: Union[str, Path, BinaryIO],
    format_name: Optional[str] = None,
) -> Path:
    """Save a schematic to a file or binary stream.

    Args:
        schematic: Schematic instance to serialize.
        target: Destination file path or binary stream.
        format_name: Explicit format name, or inferred from target file extension.

    Returns:
        Path of the saved file if target is a path.
    """
    if not format_name:
        if isinstance(target, (str, Path)):
            ext = Path(target).suffix.lower()
            handler_cls = EXTENSION_MAP.get(ext)
            if not handler_cls:
                handler_cls = LitematicHandler
        else:
            handler_cls = LitematicHandler
    else:
        norm_name = format_name.lower().replace(".", "")
        handler_cls = HANDLERS.get(norm_name, LitematicHandler)

    handler = handler_cls()
    handler.write(schematic, target)

    if isinstance(target, (str, Path)):
        return Path(target).resolve()
    return Path(".")


__all__ = [
    "FormatHandler",
    "LitematicHandler",
    "SpongeSchematicHandler",
    "VanillaStructureHandler",
    "load_schematic",
    "save_schematic",
    "detect_format_from_data",
]
