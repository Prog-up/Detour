# 📐 Détour - Native GNOME Desktop Application

Détour is an interactive GTK4 + libadwaita desktop application for cropping and perspective-deskewing image scans. It is designed for digitizing yearbook scans, photos, cards, or directories.

The application allows users to open a folder, scan images, dynamically choose split layouts (columns, rows, grid, or freeform), adjust selections as 4-vertex quadrilaterals (trapezoids) to handle scan or angle skew, and merge adjacent boundaries for rapid editing.

---

## 🚀 Running the Application

### 1. Developer Environment (Nix Flake)

The repository includes a Nix flake that sets up a development shell with all required system libraries and Python dependencies (GTK4, libadwaita, GObject Introspection, Pillow, PyGObject, Pycairo, etc.).

```bash
# Enter the developer shell
nix develop --extra-experimental-features "nix-command flakes"

# Run the application directly from source
python3 src/main.py
```

### 2. Building & Installing as Flatpak (Flathub standard)

Détour is packaged for Flathub. You can build and install it locally using `flatpak-builder`:

```bash
# Build and install the Flatpak package locally
flatpak-builder --user --install --force-clean build-dir io.github.prog_up.Detour.json

# Run the installed Flatpak
flatpak run io.github.prog_up.Detour
```

---

## ⚙️ Architecture & Design Invariants

Détour is structured as a lean PyGObject application:
* **`src/main.py`**: The `Adw.Application` entry point.
* **`src/window.py`**: The application window managing headers, sidebar lists, settings, and shortcuts.
* **`src/canvas.py`**: The custom `Gtk.DrawingArea` canvas that draws the image, selection quads, text labels, and corner handles using Cairo.
* **`src/models.py`**: The Python data models representing points, quads, and layout generators.
* **`src/imaging.py`**: The Pillow-based cropping and deskewing logic.

### Critical Invariants

1. **Coordinate Contract:** The editor canvas operates entirely in normalized `[0.0, 1.0]` coordinates relative to the displayed image, while the cropping backend (`src/imaging.py`) multiplies these by the *original* (full-resolution) dimensions.
2. **EXIF orientation:** `ImageOps.exif_transpose` is applied before reading dimensions and before cropping.
3. **Done Status Inference:** Images are marked as "done" if split output files already exist under `<folder>/split/<basename>_*`. No external database is used.
4. **Merge Neighbors via Shared References:** Adjacent corners of neighboring selection quads share the same mutable `Point` object reference. Dragging a shared corner handle moves both quads simultaneously.
5. **Layout Memory:** The single-session `last_layout` remembers the last layout and carries it over to the next image when the split count matches.

---

## ⌨️ Keyboard Shortcuts

* **Space / Enter**: Save perspective crop selections for the active image and advance.
* **Left Arrow (←)**: Navigate to the previous image.
* **Right Arrow (→)**: Navigate to the next image.
* **R / r**: Reset active layout to equal cuts.
* **V / v**: Switch to Columns layout mode.
* **H / h**: Switch to Rows layout mode.
* **G / g**: Switch to Grid layout mode.
* **F / f**: Switch to Freeform layout mode.
