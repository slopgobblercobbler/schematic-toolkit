"""End-to-end tests for the CLI interface."""

from __future__ import annotations

from pathlib import Path
from click.testing import CliRunner

from schematic_toolkit.cli import main


def test_cli_version_and_help() -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["--version"])
    assert res.exit_code == 0
    assert "schematic-toolkit, version 1.0.0" in res.output

    res_help = runner.invoke(main, ["--help"])
    assert res_help.exit_code == 0
    assert "Ultimate Minecraft Schematic" in res_help.output


def test_cli_info(sample_litematic_file: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["info", str(sample_litematic_file)])
    assert res.exit_code == 0
    assert "CozyCottage" in res.output
    assert "3 x 3 x 3 blocks" in res.output
    assert "Notch" in res.output


def test_cli_materials(sample_litematic_file: Path, temp_dir: Path) -> None:
    runner = CliRunner()

    # Rich default
    res = runner.invoke(main, ["materials", str(sample_litematic_file)])
    assert res.exit_code == 0
    assert "Stone" in res.output
    assert "minecraft:stone" in res.output

    # Markdown format
    res_md = runner.invoke(main, ["materials", str(sample_litematic_file), "-f", "markdown"])
    assert res_md.exit_code == 0
    assert "# Materials Shopping List" in res_md.output

    # JSON format
    res_json = runner.invoke(main, ["materials", str(sample_litematic_file), "-f", "json"])
    assert res_json.exit_code == 0
    assert '"total_items": 16' in res_json.output

    # CSV format to file
    out_csv = temp_dir / "materials.csv"
    res_csv = runner.invoke(
        main,
        ["materials", str(sample_litematic_file), "-f", "csv", "-o", str(out_csv)],
    )
    assert res_csv.exit_code == 0
    assert out_csv.exists()
    content = out_csv.read_text(encoding="utf-8")
    assert "minecraft:stone" in content


def test_cli_swap(sample_litematic_file: Path, temp_dir: Path) -> None:
    runner = CliRunner()
    out_swapped = temp_dir / "swapped.litematic"
    res = runner.invoke(
        main,
        [
            "swap",
            str(sample_litematic_file),
            "--from",
            "minecraft:stone",
            "--to",
            "minecraft:deepslate",
            "-o",
            str(out_swapped),
        ],
    )
    assert res.exit_code == 0
    assert "9 blocks altered" in res.output
    assert out_swapped.exists()


def test_cli_slice(sample_litematic_file: Path, temp_dir: Path) -> None:
    runner = CliRunner()
    out_slice = temp_dir / "slice.litematic"
    res = runner.invoke(
        main,
        [
            "slice",
            str(sample_litematic_file),
            "-y",
            "0:1",
            "-o",
            str(out_slice),
        ],
    )
    assert res.exit_code == 0
    assert "Extracted Layers: Y=0 to Y=1" in res.output
    assert out_slice.exists()


def test_cli_convert(sample_litematic_file: Path, temp_dir: Path) -> None:
    runner = CliRunner()
    out_schem = temp_dir / "converted.schem"
    res = runner.invoke(main, ["convert", str(sample_litematic_file), str(out_schem)])
    assert res.exit_code == 0
    assert "Conversion Successful" in res.output
    assert out_schem.exists()


def test_cli_ascii(sample_litematic_file: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["ascii", str(sample_litematic_file), "-y", "0"])
    assert res.exit_code == 0
    assert "Layer Y=0" in res.output
    assert "###" in res.output


def test_cli_export(sample_litematic_file: Path, temp_dir: Path) -> None:
    runner = CliRunner()

    # Markdown export
    out_md = temp_dir / "report.md"
    res_md = runner.invoke(
        main,
        ["export", str(sample_litematic_file), "-f", "markdown", "-o", str(out_md)],
    )
    assert res_md.exit_code == 0
    assert out_md.exists()
    assert "# Schematic Report" in out_md.read_text(encoding="utf-8")

    # JSON export
    out_json = temp_dir / "report.json"
    res_json = runner.invoke(
        main,
        ["export", str(sample_litematic_file), "-f", "json", "-o", str(out_json)],
    )
    assert res_json.exit_code == 0
    assert out_json.exists()
    assert '"CozyCottage"' in out_json.read_text(encoding="utf-8")
