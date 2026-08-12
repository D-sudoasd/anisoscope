# Paper figures

These assets are the submission-oriented figure set for the JOSS paper. The
layout follows the Nature Portfolio guidance for a double-column main figure:
183 mm wide, Arial/Helvetica text, final body and label text near 5–7 pt, and an
accessible, non-decorative palette. JOSS compiles the PNG files named in
`paper.md`; editable vector files are retained beside them.

## Figure 1: architecture and workflow

`render_architecture_workflow.py` is the only artwork source. Matplotlib draws
and exports the editable SVG, PDF, and 450 dpi PNG from one figure object; no
office-suite or conversion step is involved. The SVG contains selectable text
and no embedded raster image, gradient, filter, or shadow. The layout represents
implemented data dependencies rather than GUI call order: the supplied `Cij`
branches to the numerical core and an independent diagnostic view; scalar VRH
averages and directional sampling remain distinct; results converge on
manifest-backed exports. Panel (b) reduces the desktop interaction to four
open timeline nodes rather than repeating the module graph.

Run from the repository root (Python 3.12+ with the project dependencies):

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" paper/figures/render_architecture_workflow.py
```

Expected output: 183 × 96 mm PDF and 3242 × 1700 px PNG (450 dpi metadata).
`architecture_workflow.svg` is the editable source of record; the PDF and PNG
are derived outputs. Verify synchronization by regenerating and checking that
the three files change together, then inspect the PDF with `pdffonts` and the
PNG dimensions/DPI. At 183 mm width, labels are 7.4–10.5 pt; this preserves a
minimum of about 5.5 pt after the JOSS template scales the figure to its text
width.

## Figure 2: real GUI capture

`capture_interface.py` starts the actual PySide6 `MainWindow` in off-screen Qt
mode, loads the bundled **Si cubic** example, runs the normal analysis action,
and grabs the resulting real widget tree.  It neither synthesizes image content
nor redraws numerical data.  The captured regression/demo state uses C11 =
165.7 GPa, C12 = 63.9 GPa, and C44 = 79.6 GPa from
`crystal_elastic_workbench/examples.py` (also represented in
`examples/si_cubic.json`).

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" paper/figures/capture_interface.py
```

This writes `anisoscope_interface.png` (2400 × 1294 px, 333 dpi metadata) and
`anisoscope_interface.capture.json`.  The JSON contains the SHA-256 of the PNG,
the loaded constants, the successful workflow status, platform, and capture
time.  The real interface includes a dynamic “Last analysis” timestamp; the
metadata time records each occurrence.  Regenerate and compare the JSON SHA-256
to the PNG hash to verify capture synchronization.  It forces a real Qt
`QT_SCALE_FACTOR=3` capture: the actual logical window width, physical capture
width, and device-pixel ratio are recorded in the JSON. Panel (a) uses high-DPI
widget captures from the Input and Cij Matrix groups. Panel (b) uses the real
Dashboard status and four real metric-card widgets in a 2×2 layout. Plot-style
and action controls that do not support the paper's claim are omitted. Only the
panel letters, neutral card backgrounds, and spacing are drawn; scientific
values and interface labels are copied from Qt widgets. The JSON records this
composition rule. The script records a conservative 12-logical-pixel minimum UI
font estimate and computes its final point height at 183 mm as about 6.3 pt.
The timestamp is expected to
change, so byte-identical GUI captures are not expected across runs.

## Specification sources and checks

- Nature Portfolio, [Preparing figures: our specifications](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/): text, graph, accessibility, and export guidance.
- Nature Portfolio, [Building and exporting figure panels](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/): 89/183 mm widths, font/export requirements, and panel arrangement guidance.

Before reuse, visually inspect both PNGs at final manuscript scale and verify
that no text overlaps.  The architecture PDF has an embedded-font check; a GUI
screenshot is intrinsically raster-only, so it has no editable-vector text
claim.  Do not treat this README as evidence that an external journal build or
submission check has passed.
