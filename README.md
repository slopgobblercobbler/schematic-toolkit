# Schematic Toolkit 📐

[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/schematic-toolkit/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-61%20passed-brightgreen.svg)](tests/)

**Schematic Toolkit** is the Swiss Army knife for Minecraft builders and technical redstone players. It parses, inspects, converts, swaps palettes, slices, and calculates exact material shopping lists for `.litematic` (Litematica), `.schem` (Sponge / WorldEdit), and `.nbt` (Vanilla Structure Block) files.

---

## ⚡ Features

- **Format Interoperability**:
  - Seamlessly convert between **Litematica** (`.litematic`), **Sponge / WorldEdit** (`.schem`), and **Vanilla Structure Block** (`.nbt`).
  - Bit-exact support for Litematica's 64-bit cross-boundary bitpacking and Sponge's VarInt block data streams.
- **Material Shopping Lists**:
  - Generates comprehensive resource tables formatted by exact item count, stacks (e.g. `27 stacks + 14 items`), and Shulker Box counts.
  - Export to Markdown, CSV, and formatted JSON.
- **In-Place Palette Swapper**:
  - Replace blocks across massive schematics in one command (e.g., substitute `deepslate_bricks` for `stone_bricks`, or map oxidized copper to wax-preserved copper).
  - Preserves block state properties (facing, half, shape, waterlogged).
- **3D Slice Extractor**:
  - Extract specific vertical sub-sections or horizontal slices (e.g., floor-by-floor blueprints).
- **ASCII Cross-Section Visualizer**:
  - Render terminal ASCII blueprints of any layer for quick in-console verification.

---

## 🚀 CLI Commands

### 1. Inspect Schematic
```bash
schematic-toolkit info castle.litematic
```

### 2. Calculate Materials
```bash
schematic-toolkit materials farm.schem --format markdown
```

### 3. Swap Block Palette
```bash
schematic-toolkit swap base.litematic -s "oak_planks=spruce_planks" "glass=tinted_glass"
```

### 4. Extract Layer Slice
```bash
schematic-toolkit slice tower.litematic --y 64:80 -o tower_mid.litematic
```

### 5. Format Conversion
```bash
schematic-toolkit convert temple.nbt temple.litematic
```

---

## 🧪 Testing

```bash
pytest
```

100% test pass rate across 61 unit tests covering bitpacking, compression round-trips, and matrix converters.

---

## 📄 License

Licensed under the [MIT License](LICENSE).
