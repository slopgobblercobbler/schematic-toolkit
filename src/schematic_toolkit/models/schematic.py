"""Universal Schematic data model unifying all Minecraft schematic formats."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

from schematic_toolkit.models.block import BlockState
from schematic_toolkit.models.region import Region


class Schematic:
    """Universal representation of a Minecraft schematic.

    Can contain one or more regions (as in Litematica), or a single main region
    (as in Sponge .schem and Vanilla .nbt structures).
    """

    def __init__(
        self,
        name: str = "Unnamed",
        author: str = "",
        description: str = "",
        data_version: int = 3463,  # Modern default (Minecraft 1.20+)
        regions: Optional[Dict[str, Region]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_format: str = "litematic",
    ) -> None:
        self.name = name
        self.author = author
        self.description = description
        self.data_version = data_version
        self.metadata: Dict[str, Any] = metadata if metadata is not None else {}
        self.source_format = source_format
        self.regions: Dict[str, Region] = {}

        if regions:
            for r_name, r in regions.items():
                self.add_region(r, r_name)

    @classmethod
    def create_single_region(
        cls,
        name: str,
        width: int,
        height: int,
        length: int,
        author: str = "",
        palette: Optional[Sequence[BlockState]] = None,
        blocks: Optional[Sequence[int]] = None,
        source_format: str = "litematic",
    ) -> Schematic:
        """Helper factory to create a schematic containing a single region."""
        region = Region(
            name=name,
            width=width,
            height=height,
            length=length,
            palette=palette,
            blocks=blocks,
        )
        schem = cls(
            name=name,
            author=author,
            source_format=source_format,
        )
        schem.add_region(region, name)
        return schem

    def add_region(self, region: Region, name: Optional[str] = None) -> None:
        """Add or replace a region in the schematic."""
        reg_name = name or region.name
        self.regions[reg_name] = region

    @property
    def primary_region(self) -> Region:
        """Get the primary (first) region in this schematic, or create an empty one."""
        if not self.regions:
            default_reg = Region("Main", 1, 1, 1)
            self.regions["Main"] = default_reg
            return default_reg
        return next(iter(self.regions.values()))

    @property
    def width(self) -> int:
        """Width of primary region."""
        return self.primary_region.width

    @property
    def height(self) -> int:
        """Height of primary region."""
        return self.primary_region.height

    @property
    def length(self) -> int:
        """Length of primary region."""
        return self.primary_region.length

    @property
    def total_volume(self) -> int:
        """Total volume across all regions in cubic blocks."""
        return sum(r.volume for r in self.regions.values())

    def total_blocks(self, include_air: bool = False) -> int:
        """Total number of blocks placed across all regions."""
        return sum(r.total_blocks(include_air=include_air) for r in self.regions.values())

    def material_counts(self, include_air: bool = False) -> Counter[str]:
        """Aggregate material counts across all regions."""
        counts: Counter[str] = Counter()
        for r in self.regions.values():
            counts.update(r.count_by_material(include_air=include_air))
        return counts

    def state_counts(self) -> Counter[BlockState]:
        """Aggregate exact BlockState counts across all regions."""
        counts: Counter[BlockState] = Counter()
        for r in self.regions.values():
            counts.update(r.count_by_state())
        return counts

    def swap_palette(
        self,
        mapping: Dict[str, str],
        preserve_properties: bool = True,
    ) -> int:
        """Substitute block types across all regions in this schematic.

        Returns:
            Total number of blocks changed.
        """
        total_changed = 0
        for r in self.regions.values():
            total_changed += r.substitute_palette(mapping, preserve_properties=preserve_properties)
        return total_changed

    def extract_slice_y(
        self,
        min_y: int,
        max_y: int,
        recenter: bool = False,
    ) -> Schematic:
        """Extract a vertical layer slice between min_y and max_y (inclusive) across all regions."""
        new_regions: Dict[str, Region] = {}
        for r_name, r in self.regions.items():
            sub_r = r.extract_subvolume(
                min_x=0,
                max_x=r.width - 1,
                min_y=min_y,
                max_y=max_y,
                min_z=0,
                max_z=r.length - 1,
                recenter=recenter,
            )
            new_regions[r_name] = sub_r

        new_schem = Schematic(
            name=f"{self.name}_y{min_y}-{max_y}",
            author=self.author,
            description=f"Extracted Y={min_y}..{max_y} slice of {self.name}",
            data_version=self.data_version,
            regions=new_regions,
            metadata=dict(self.metadata),
            source_format=self.source_format,
        )
        return new_schem

    def extract_bounding_box(
        self,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int,
        min_z: int,
        max_z: int,
        recenter: bool = False,
    ) -> Schematic:
        """Extract a 3D bounding box sub-volume from the schematic's primary region."""
        primary = self.primary_region
        sub_r = primary.extract_subvolume(
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
            min_z=min_z,
            max_z=max_z,
            recenter=recenter,
        )
        return Schematic(
            name=f"{self.name}_subvolume",
            author=self.author,
            description=f"Extracted subvolume of {self.name}",
            data_version=self.data_version,
            regions={sub_r.name: sub_r},
            metadata=dict(self.metadata),
            source_format=self.source_format,
        )

    def clone(self) -> Schematic:
        """Return a deep copy of the schematic."""
        return Schematic(
            name=self.name,
            author=self.author,
            description=self.description,
            data_version=self.data_version,
            regions={name: r.clone() for name, r in self.regions.items()},
            metadata=dict(self.metadata),
            source_format=self.source_format,
        )

    def save(
        self,
        target_path: Union[str, Path],
        target_format: Optional[str] = None,
    ) -> Path:
        """Save schematic to disk in requested or inferred format."""
        from schematic_toolkit.formats import save_schematic

        return save_schematic(self, target_path, target_format)

    def __repr__(self) -> str:
        regions_repr = ", ".join(f"{name}: {r.width}x{r.height}x{r.length}" for name, r in self.regions.items())
        return f"Schematic('{self.name}', format='{self.source_format}', regions=[{regions_repr}])"
