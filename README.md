# schematic-toolkit ⛏️

[![CI](https://github.com/deepmind/schematic-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/deepmind/schematic-toolkit/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**schematic-toolkit** is the ultimate production-grade CLI suite and Python library for Minecraft schematics. It natively inspects, converts, palette-swaps, slices, and calculates survival shopping lists for **Litematica (`.litematic`)**, **Sponge Schematic (`.schem`)**, and **Vanilla Structure Block (`.nbt`)** files.

Built with **zero heavy C-extensions**, a custom high-performance pure-Python NBT engine, bit-accurate Litematica continuous 64-bit bitstream codecs, and Sponge VarInt stream packers.

---

## Features

- 📦 **Multi-Format Support:** Read, write, and convert losslessly between `.litematic`, `.schem` (v1, v2, v3), and `.nbt` (Vanilla Structure Blocks).
- 🛒 **Exact Materials Calculator:** Generate shopping lists with exact item counts, 64/16/1 item stack divisions, and 27-slot Shulker Box estimates.
- 🎨 **In-Place Palette Swapper:** Substitute block types across entire schematics or single layers while preserving block state properties (`facing`, `half`, `waterlogged`, etc.).
- 🍰 **Layer Slice Extractor:** Extract vertical layer slices (e.g. `Y=10..20`) or 3D bounding boxes into standalone valid sub-schematics.
- 🗺️ **ASCII Cross-Section Diagrams:** Render terminal-friendly or file-exported 2D layer maps with customizable character legends.
- 📑 **Multi-Format Reports:** Export schematic data and shopping lists to Rich tables, Markdown reports, JSON datasets, and CSV spreadsheets.
- ⚡ **Lightweight & Fast:** 100% pure Python, zero compilation required, cross-platform on Windows, macOS, and Linux.

---

## Installation

### From Source
```bash
git clone https://github.com/your-username/schematic-toolkit.git
cd schematic-toolkit
pip install -e .
```

To install development dependencies (e.g., `pytest`, `pytest-cov`):
```bash
pip install -e ".[dev]"
```

After installation, both `schem` and `schematic-toolkit` CLI commands will be available in your environment.

---

## Quick Start CLI Guide

### 1. Inspect Schematic Metadata & Dimensions (`info`)
Inspect bounding box dimensions, volume, fill percentage, author, data version, and sub-regions:
```bash
schem info castle.litematic
```
*Output:*
```text
╭─────────────────────────────────── Schematic Info: castle.litematic ───────────────────────────────────╮
│ File Name          castle.litematic                                                                   │
│ Schematic Name     Grand Castle                                                                       │
│ Author             BuilderAlex                                                                        │
│ Detected Format    LITEMATIC                                                                          │
│ DataVersion        3463                                                                               │
│ Dimensions (WxHxL) 32 x 45 x 32 blocks                                                                │
│ Total Volume       46,080 blocks                                                                      │
│ Placed Blocks      18,420 (40.0% solid)                                                               │
│ Region Count       1                                                                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

### 2. Materials Shopping List & Shulker Box Estimates (`materials`)
Calculate exact item breakdowns, taking into account unstackable items (beds, boats, minecarts) and 16-stack items (signs, banners, ender pearls):
```bash
schem materials castle.litematic
```

#### Output Formats:
- **Rich Terminal Table:**
  ```bash
  schem materials castle.litematic
  ```
- **Markdown Table:**
  ```bash
  schem materials castle.litematic --format markdown -o shopping_list.md
  ```
- **JSON Data:**
  ```bash
  schem materials castle.litematic --format json -o materials.json
  ```
- **CSV Spreadsheet:**
  ```bash
  schem materials castle.litematic --format csv -o materials.csv
  ```

---

### 3. Palette Swapping (`swap`)
Substitute block types across the entire schematic. By default, existing block states (such as `facing=north`, `waterlogged=false`) are preserved on the destination block!

#### Simple 1-to-1 Swap:
```bash
schem swap castle.litematic --from minecraft:stone --to minecraft:deepslate -o castle_deepslate.litematic
```

#### Multiple Block Mappings:
```bash
schem swap build.schem --map "oak_planks=spruce_planks,stone=blackstone" -o build_dark.schem
```

#### In-Place Modification:
```bash
schem swap tower.litematic --from cobblestone --to cobbled_deepslate --in-place
```

#### JSON Recipe File:
Create `recipe.json`:
```json
{
  "minecraft:stone": "minecraft:deepslate",
  "minecraft:oak_stairs": "minecraft:spruce_stairs",
  "minecraft:torch": "minecraft:soul_torch"
}
```
Run:
```bash
schem swap structure.nbt --recipe recipe.json -o themed_structure.nbt
```

---

### 4. Layer Slice Extractor (`slice`)
Extract specific horizontal layers (e.g., `Y=10` to `Y=20`) into an isolated, playable sub-schematic:
```bash
# Slices Y=10 through Y=20 into a sub-schematic
schem slice castle.litematic -y 10:20 -o castle_roof.litematic
```
Options:
- `-y`, `--y-range`: Range specification (`10:20`, `10..20`, or single layer `15`).
- `--recenter`: Reset relative placement offsets to `(0, 0, 0)`.

---

### 5. Format Converter (`convert`)
Losslessly convert between `.litematic`, `.schem`, and `.nbt`:
```bash
# Convert Litematica to Sponge Schematic (WorldEdit compatible)
schem convert house.litematic house.schem

# Convert Sponge Schematic to Vanilla Structure Block NBT
schem convert house.schem house.nbt

# Convert Vanilla Structure Block NBT to Litematica
schem convert house.nbt house.litematic
```

---

### 6. ASCII Layer Diagrams (`ascii`)
Generate an interactive or printable ASCII cross-section diagram of any layer:
```bash
schem ascii castle.litematic -y 0
```
*Output:*
```text
=== Cross-Section: Region 'Main' at Layer Y=0 (Size: 8x8) ===

        01234567
       +--------+
 0 |########| 0
 1 |#......#| 1
 2 |#.WWWW.#| 2
 3 |#.W..W.#| 3
 4 |#.W..W.#| 4
 5 |#.WWWW.#| 5
 6 |#......#| 6
 7 |########| 7
       +--------+
        01234567

--- Legend ---
  [.]  Air (minecraft:air)
  [#]  Stone (minecraft:stone)
  [W]  Oak Planks (minecraft:oak_planks)
```

---

### 7. Full Documentation Export (`export`)
Export complete reports with metadata, volume metrics, shopping lists, and layer diagrams:
```bash
schem export castle.litematic --format markdown -o REPORT.md
schem export castle.litematic --format json -o report.json
```

---

## Python API Usage

You can embed `schematic-toolkit` directly into your Python pipelines and tools:

```python
from schematic_toolkit import load_schematic, calculate_materials, BlockState

# 1. Load any schematic format
schem = load_schematic("cottage.litematic")
print(f"Loaded: {schem.name} ({schem.width}x{schem.height}x{schem.length})")

# 2. Query blocks
region = schem.primary_region
block = region.get_block(x=1, y=2, z=3)
print(f"Block at (1,2,3): {block.name} {block.properties}")

# 3. Calculate materials shopping list
shopping_list = calculate_materials(schem)
print(f"Total items required: {shopping_list.total_items}")
print(f"Compacted Shulker Boxes: {shopping_list.total_shulker_boxes_compacted}")

for item in shopping_list.items[:5]:
    print(f"- {item.display_name}: {item.count} ({item.formatted_breakdown})")

# 4. Swap palette
schem.swap_palette({"minecraft:oak_planks": "minecraft:dark_oak_planks"})

# 5. Extract a slice
slice_schem = schem.extract_slice_y(min_y=0, max_y=5)

# 6. Save in any format
slice_schem.save("cottage_slice.schem")
```

---

## Technical Specifications

### Continuous 64-Bit Packing in Litematica
Litematica files pack block indices into a `TAG_Long_Array` using continuous bit-packing. Entries have bit width $n = \max(2, \lceil\log_2(\text{palette\_size})\rceil)$ and are packed sequentially without word-boundary alignment padding. `schematic-toolkit` implements precise bit extraction:
$$\text{Bit Offset} = \text{index} \times n$$
When an entry crosses a 64-bit threshold, the codec splits and stitches the bit segments between adjacent longs.

### Sponge VarInt Codec
Sponge schematic files encode block palette indices as variable-length 7-bit integers (VarInts) stored inside a `TAG_Byte_Array`. `schematic-toolkit` implements a high-throughput streaming decoder and encoder supporting large multi-million block volumes.

---

## Testing

The project maintains a 100% test pass rate with pytest:

```bash
pytest
```

To run with coverage reporting:
```bash
pytest --cov=schematic_toolkit --cov-report=term-missing
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
