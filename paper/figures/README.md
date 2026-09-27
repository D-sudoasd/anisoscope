# Figure sources

`render_architecture_workflow.py` generates the workflow as editable SVG, embedded-font PDF and 450 dpi PNG. The supplied stiffness matrix is inspected independently of compliance inversion. Scalar and directional outputs retain their separate meanings.

`capture_interface.py` captures the real Qt application after loading the bundled Si-cubic demonstration and running analysis. Input and matrix widgets form panel (a); the complete status label and four real metric widgets form panel (b). The capture reflows widgets for legibility, without redrawing numerical values or clipping labels. Only panel headings and spacing are added. The input convention and demonstration constants are retained.

Run both scripts from the repository root. For headless rendering, set `QT_QPA_PLATFORM=offscreen` and, if required, `ANISOSCOPE_DISABLE_PYVISTA=1`. The capture script sets a 3× Qt scale itself. The JSON records image and widget sizes, the conservative font estimate, source constants, capture time and the PNG SHA-256. Actual capture times may differ across runs.

Inspect both figures in the final official JOSS PDF after regeneration. The scientific figures do not use the AI-generated conceptual cover shown in the README; see `docs/joss/visual-provenance.md`.
