"""Structure slice extractor operation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple, Union

from schematic_toolkit.formats import load_schematic, save_schematic
from schematic_toolkit.models.schematic import Schematic


def parse_range_spec(range_str: str) -> Tuple[int, int]:
    """Parse range string formats like '10:20', '10..20', '10-20', or '15'.

    Returns:
        Tuple of (min_val, max_val) inclusive.
    """
    s = range_str.strip()
    # Check single number
    if re.fullmatch(r"^-?\d+$", s):
        val = int(s)
        return (val, val)

    # Check colon, dots, or dash separator
    m = re.match(r"^(-?\d+)\s*(?::|\.\.|-)\s*(-?\d+)$", s)
    if m:
        v1 = int(m.group(1))
        v2 = int(m.group(2))
        return (min(v1, v2), max(v1, v2))

    raise ValueError(
        f"Invalid range specification: '{range_str}'. Expected 'min:max', 'min..max', or single integer."
    )


def slice_schematic_y(
    schematic: Schematic,
    min_y: int,
    max_y: int,
    recenter: bool = False,
) -> Schematic:
    """Extract layers min_y to max_y (inclusive) into a new Schematic."""
    return schematic.extract_slice_y(min_y, max_y, recenter=recenter)


def slice_schematic_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]],
    min_y: int,
    max_y: int,
    recenter: bool = False,
) -> Tuple[Schematic, Path]:
    """Load a schematic, slice layers min_y..max_y, and save to output.

    Args:
        input_path: Path to source schematic.
        output_path: Path to save sub-schematic (or None for default name).
        min_y: Starting layer (inclusive).
        max_y: Ending layer (inclusive).
        recenter: If True, adjust relative origin to 0.

    Returns:
        Tuple of (sliced_schematic, output_path)
    """
    in_p = Path(input_path).resolve()
    schematic = load_schematic(in_p)

    sliced = slice_schematic_y(schematic, min_y, max_y, recenter=recenter)

    if output_path:
        dest_p = Path(output_path).resolve()
    else:
        dest_p = in_p.with_stem(f"{in_p.stem}_y{min_y}-{max_y}")

    save_schematic(sliced, dest_p)
    return (sliced, dest_p)
