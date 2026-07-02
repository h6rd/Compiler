# Compiler

A tool for compiling Valve Resource Format assets into their final formats.

---

## Download

| Platform | Link |
| --- | --- |
| Windows | [Compiler-Win.zip](https://github.com/h6rd/Compiler/releases/latest/download/Compiler-Win.zip) |

---

## Files

The script automatically detects source files and compiles them into compiled formats:

| Source Format | Compiled Extension |
| --- | --- |
| `.png` | `.vtex_c` |
| `.mp3`/`.wav` | `.vsnd_c` |
| `.vpcf` | `.vpcf_c` |
| `.xml` | `.vxml_c` |
| `.css` | `.vcss_c` |

---

## Usage

Place your source files (like `.png`, `.mp3`, etc.) in the input folder next to the script and run it.

The result will be the corresponding compiled `_c` files ready for use in your mod.
