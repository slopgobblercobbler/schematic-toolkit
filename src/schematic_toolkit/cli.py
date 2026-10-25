"""CLI entrypoint for schematic-toolkit."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from schematic_toolkit import __version__
from schematic_toolkit.exporters.ascii_art import render_ascii_layer_y
from schematic_toolkit.exporters.json_export import export_json
from schematic_toolkit.exporters.markdown import export_markdown
from schematic_toolkit.formats import detect_format_from_data, load_schematic, save_schematic
from schematic_toolkit.materials.calculator import calculate_materials
from schematic_toolkit.operations.converter import convert_schematic_file
from schematic_toolkit.operations.slicer import parse_range_spec, slice_schematic_file
from schematic_toolkit.operations.swapper import (
    load_swap_recipe,
    parse_swap_spec,
    swap_schematic_file,
)

console = Console()
err_console = Console(stderr=True)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "--version", prog_name="schematic-toolkit")
def main() -> None:
    """Ultimate Minecraft Schematic (.litematic, .schem, .nbt) Toolkit.

    Inspect, calculate materials, swap palettes, extract slices, and convert formats.
    """
    pass


@main.command(name="info")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def info_cmd(file: Path) -> None:
    """Inspect schematic metadata, dimensions, volume, and regions."""
    try:
        schematic = load_schematic(file)
    except Exception as e:
        err_console.print(f"[bold red]Error loading schematic:[/bold red] {e}")
        sys.exit(1)

    primary = schematic.primary_region
    total_blocks_placed = schematic.total_blocks(include_air=False)
    fill_ratio = (total_blocks_placed / schematic.total_volume * 100) if schematic.total_volume > 0 else 0.0

    meta_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
    meta_table.add_column("Property", style="bold cyan")
    meta_table.add_column("Value")

    meta_table.add_row("File Name", file.name)
    meta_table.add_row("Schematic Name", schematic.name)
    meta_table.add_row("Author", schematic.author or "[dim]None[/dim]")
    meta_table.add_row("Description", schematic.description or "[dim]None[/dim]")
    meta_table.add_row("Detected Format", schematic.source_format.upper())
    meta_table.add_row("DataVersion", str(schematic.data_version))
    meta_table.add_row(
        "Dimensions (WxHxL)",
        f"{primary.width} x {primary.height} x {primary.length} blocks",
    )
    meta_table.add_row("Total Volume", f"{schematic.total_volume:,} blocks")
    meta_table.add_row(
        "Placed Blocks",
        f"{total_blocks_placed:,} ({fill_ratio:.1f}% solid)",
    )
    meta_table.add_row("Region Count", str(len(schematic.regions)))

    console.print(Panel(meta_table, title=f"[bold green]Schematic Info: {file.name}[/bold green]"))

    if len(schematic.regions) > 1:
        reg_table = Table(title="Regions Breakdown", box=box.SIMPLE_HEAVY)
        reg_table.add_column("Name", style="bold")
        reg_table.add_column("Dimensions (WxHxL)", justify="center")
        reg_table.add_column("Offset (X, Y, Z)", justify="center")
        reg_table.add_column("Placed Blocks", justify="right")
        reg_table.add_column("Palette Size", justify="right")

        for r_name, r in schematic.regions.items():
            reg_table.add_row(
                r_name,
                f"{r.width}x{r.height}x{r.length}",
                f"{r.offset_x}, {r.offset_y}, {r.offset_z}",
                f"{r.total_blocks(include_air=False):,}",
                str(len(r.palette)),
            )
        console.print(reg_table)


@main.command(name="materials")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["rich", "markdown", "json", "csv"], case_sensitive=False),
    default="rich",
    help="Output presentation format.",
)
@click.option(
    "--include-air",
    is_flag=True,
    default=False,
    help="Include air blocks in material calculations.",
)
@click.option(
    "--sort",
    "sort_by",
    type=click.Choice(["count", "name"], case_sensitive=False),
    default="count",
    help="Sort order for materials list.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write shopping list to destination file instead of terminal.",
)
def materials_cmd(
    file: Path,
    output_format: str,
    include_air: bool,
    sort_by: str,
    output: Optional[Path],
) -> None:
    """Generate exact material shopping lists with stacks and shulker box estimates."""
    try:
        schematic = load_schematic(file)
    except Exception as e:
        err_console.print(f"[bold red]Error loading schematic:[/bold red] {e}")
        sys.exit(1)

    shopping_list = calculate_materials(schematic, include_air=include_air, sort_by=sort_by)

    if output_format == "markdown":
        result = shopping_list.to_markdown()
    elif output_format == "json":
        import json
        result = json.dumps(shopping_list.to_dict(), indent=2)
    elif output_format == "csv":
        result = shopping_list.to_csv()
    else:
        # Rich table output
        summary_panel = Panel(
            f"[bold]Total Items Placed:[/bold] {shopping_list.total_items:,}\n"
            f"[bold]Unique Materials:[/bold] {shopping_list.total_unique_items}\n"
            f"[bold]Inventory Slots:[/bold] {shopping_list.total_inventory_slots:,} slots\n"
            f"[bold]Compacted Shulker Boxes (~27 slots):[/bold] [green]{shopping_list.total_shulker_boxes_compacted} SBs[/green]\n"
            f"[bold]Dedicated Shulker Boxes:[/bold] [yellow]{shopping_list.total_shulker_boxes_dedicated} SBs[/yellow]",
            title="[bold cyan]Shopping List Summary[/bold cyan]",
            box=box.ROUNDED,
        )
        console.print(summary_panel)

        table = Table(
            title=f"Materials for {file.name}",
            box=box.SIMPLE_HEAVY,
            header_style="bold magenta",
        )
        table.add_column("Item", style="bold")
        table.add_column("Resource Location", style="dim")
        table.add_column("Count", justify="right", style="cyan")
        table.add_column("Stack", justify="center")
        table.add_column("Shopping Breakdown (SB + Stacks + Remainder)", style="green")

        for item in shopping_list.items:
            table.add_row(
                item.display_name,
                item.item_id,
                f"{item.count:,}",
                str(item.stack_size),
                item.formatted_breakdown,
            )

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(shopping_list.to_markdown())
            console.print(f"[bold green]Saved Markdown shopping list to:[/bold green] {output}")
        else:
            console.print(table)
        return

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        console.print(f"[bold green]Saved output to:[/bold green] {output}")
    else:
        click.echo(result)


@main.command(name="swap")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--from", "from_block", help="Source block to replace (e.g. 'minecraft:stone').")
@click.option("--to", "to_block", help="Target replacement block (e.g. 'minecraft:deepslate').")
@click.option(
    "-m",
    "--map",
    "map_spec",
    help="Substitution mapping string (e.g. 'stone=deepslate,oak_planks=spruce_planks').",
)
@click.option(
    "-r",
    "--recipe",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="JSON recipe file mapping old blocks to new blocks.",
)
@click.option(
    "-i",
    "--in-place",
    is_flag=True,
    default=False,
    help="Modify the input schematic file in-place.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output destination path.",
)
@click.option(
    "--preserve-properties/--no-preserve-properties",
    default=True,
    help="Preserve existing block state properties (e.g. facing, axis).",
)
def swap_cmd(
    file: Path,
    from_block: Optional[str],
    to_block: Optional[str],
    map_spec: Optional[str],
    recipe: Optional[Path],
    in_place: bool,
    output: Optional[Path],
    preserve_properties: bool,
) -> None:
    """In-place or target palette swapper to substitute block types."""
    mapping = {}

    if recipe:
        mapping.update(load_swap_recipe(recipe))

    if map_spec:
        mapping.update(parse_swap_spec(map_spec))

    if from_block and to_block:
        mapping[from_block] = to_block

    if not mapping:
        err_console.print("[bold red]Error:[/bold red] Must specify --from and --to, --map, or --recipe.")
        sys.exit(1)

    try:
        schematic, changed_count, dest_path = swap_schematic_file(
            input_path=file,
            output_path=output,
            mapping=mapping,
            in_place=in_place,
            preserve_properties=preserve_properties,
        )
    except Exception as e:
        err_console.print(f"[bold red]Error during palette swap:[/bold red] {e}")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]Swapped blocks:[/bold] [green]{changed_count:,} blocks altered[/green]\n"
            f"[bold]Replacements applied:[/bold] {mapping}\n"
            f"[bold]Destination file:[/bold] {dest_path}",
            title="[bold green]Palette Swap Completed[/bold green]",
            box=box.ROUNDED,
        )
    )


@main.command(name="slice")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-y",
    "--y-range",
    help="Layer range to extract (e.g. '10:20', '10..20', or '15').",
)
@click.option("--min-y", type=int, default=None, help="Minimum Y layer (inclusive).")
@click.option("--max-y", type=int, default=None, help="Maximum Y layer (inclusive).")
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output sub-schematic destination path.",
)
@click.option(
    "--recenter",
    is_flag=True,
    default=False,
    help="Reset relative position offset to (0, 0, 0).",
)
def slice_cmd(
    file: Path,
    y_range: Optional[str],
    min_y: Optional[int],
    max_y: Optional[int],
    output: Optional[Path],
    recenter: bool,
) -> None:
    """Extract a horizontal layer slice (min-y to max-y) into a sub-schematic."""
    if y_range:
        parsed_min_y, parsed_max_y = parse_range_spec(y_range)
    elif min_y is not None and max_y is not None:
        parsed_min_y, parsed_max_y = min_y, max_y
    elif min_y is not None:
        parsed_min_y = parsed_max_y = min_y
    else:
        err_console.print("[bold red]Error:[/bold red] Must specify -y / --y-range or --min-y and --max-y.")
        sys.exit(1)

    try:
        sub_schem, dest_p = slice_schematic_file(
            input_path=file,
            output_path=output,
            min_y=parsed_min_y,
            max_y=parsed_max_y,
            recenter=recenter,
        )
    except Exception as e:
        err_console.print(f"[bold red]Error during slicing:[/bold red] {e}")
        sys.exit(1)

    primary = sub_schem.primary_region
    console.print(
        Panel(
            f"[bold]Extracted Layers:[/bold] Y={parsed_min_y} to Y={parsed_max_y} (height: {primary.height})\n"
            f"[bold]Sub-Schematic Size:[/bold] {primary.width} x {primary.height} x {primary.length}\n"
            f"[bold]Placed Blocks in Slice:[/bold] {sub_schem.total_blocks(include_air=False):,}\n"
            f"[bold]Saved to:[/bold] {dest_p}",
            title="[bold green]Structure Slice Extracted[/bold green]",
            box=box.ROUNDED,
        )
    )


@main.command(name="convert")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output_file", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["litematic", "sponge", "schem", "nbt"], case_sensitive=False),
    default=None,
    help="Explicit output format (if omitted, inferred from output_file extension).",
)
def convert_cmd(
    input_file: Path,
    output_file: Path,
    output_format: Optional[str],
) -> None:
    """Convert schematic between .litematic, .schem, and .nbt formats."""
    try:
        schem, dest_p = convert_schematic_file(
            input_path=input_file,
            output_path=output_file,
            output_format=output_format,
        )
    except Exception as e:
        err_console.print(f"[bold red]Error converting schematic:[/bold red] {e}")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]Source File:[/bold] {input_file} ({schem.source_format.upper()})\n"
            f"[bold]Converted File:[/bold] {dest_p} ({dest_p.suffix.upper()})\n"
            f"[bold]Total Blocks:[/bold] {schem.total_blocks(include_air=False):,}",
            title="[bold green]Conversion Successful[/bold green]",
            box=box.ROUNDED,
        )
    )


@main.command(name="ascii")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-y", "--layer", type=int, default=0, help="Y layer to visualize (default: 0).")
@click.option("--no-legend", is_flag=True, default=False, help="Hide the character legend.")
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Save ASCII diagram to text file.",
)
def ascii_cmd(file: Path, layer: int, no_legend: bool, output: Optional[Path]) -> None:
    """Render an ASCII cross-section diagram of a schematic layer."""
    try:
        schematic = load_schematic(file)
        art = render_ascii_layer_y(schematic.primary_region, y=layer, show_legend=not no_legend)
    except Exception as e:
        err_console.print(f"[bold red]Error rendering ASCII diagram:[/bold red] {e}")
        sys.exit(1)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(art)
        console.print(f"[bold green]Saved ASCII diagram to:[/bold green] {output}")
    else:
        click.echo(art)


@main.command(name="export")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-f",
    "--format",
    "export_format",
    type=click.Choice(["markdown", "json"], case_sensitive=False),
    default="markdown",
    help="Export report format (markdown or json).",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Destination file path.",
)
@click.option(
    "-y",
    "--layer",
    type=int,
    default=0,
    help="Sample layer for diagram in Markdown report (default: 0).",
)
def export_cmd(file: Path, export_format: str, output: Optional[Path], layer: int) -> None:
    """Export complete schematic documentation report to Markdown or JSON."""
    try:
        schematic = load_schematic(file)
    except Exception as e:
        err_console.print(f"[bold red]Error loading schematic:[/bold red] {e}")
        sys.exit(1)

    if export_format == "json":
        result = export_json(schematic)
    else:
        result = export_markdown(schematic, sample_layer_y=layer)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        console.print(f"[bold green]Successfully exported {export_format.upper()} report to:[/bold green] {output}")
    else:
        click.echo(result)


if __name__ == "__main__":
    main()
