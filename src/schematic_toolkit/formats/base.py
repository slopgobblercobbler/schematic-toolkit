"""Base interfaces and registry for schematic file format handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Union

from schematic_toolkit.models.schematic import Schematic


class FormatHandler(ABC):
    """Abstract base class for a schematic file format reader/writer."""

    format_name: str
    extensions: tuple[str, ...]

    @abstractmethod
    def read(self, source: Union[str, Path, bytes, BinaryIO]) -> Schematic:
        """Parse source data into a universal Schematic object."""
        ...

    @abstractmethod
    def write(self, schematic: Schematic, target: Union[str, Path, BinaryIO]) -> None:
        """Serialize a Schematic object into target binary format."""
        ...
