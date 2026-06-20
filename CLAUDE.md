# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Enter the developer environment (automatically installs all system and python dependencies)
nix develop --extra-experimental-features "nix-command flakes"

# Run the desktop app from the source directory
python3 src/main.py

# Build and install as a Flatpak locally
flatpak-builder --user --install --force-clean build-dir io.github.prog_up.Detour.json

# Run the installed Flatpak application
flatpak run io.github.prog_up.Detour
```

## Architecture

Détour is an interactive GTK4 + libadwaita desktop application for cropping and perspective-deskewing image scans. The HTTP server and browser UI have been removed in favor of a native Python UI using PyGObject.

### Key Invariants to Preserve

1. **Coordinate Contract:** The editor UI works in normalized `[0, 1]` coordinates relative to the displayed image. The cropping backend (`src/imaging.py`) multiplies these by the *original* (full-resolution) image dimensions.
2. **EXIF Orientation:** Apply `ImageOps.exif_transpose` before reading dimensions and before cropping.
3. **Inferred "Done" Status:** An image is considered `done` iff `<folder>/split/<basename>_*` files exist in the same directory. There is no database or state file.
4. **Merge Neighbors via Shared References:** Adjacent corners of neighboring selection quads share the same `Point` object reference, so dragging one handle moves both. Deduping handles in `unique_handles` checks for `id(pt)` uniqueness.
5. **Layout Memory:** The single-session `last_layout` remembers the last quad layout and applies it to the next image in the directory when the split count matches.
