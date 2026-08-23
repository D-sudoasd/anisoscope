# Changelog

All notable user-facing changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- JOSS manuscript sources and reproducible paper figures.
- User, API, contribution, security, citation, and community documentation.
- MIT license and CFF citation metadata.
- Continuous-integration checks for tests, package builds, metadata validation,
  and clean-environment wheel smoke tests.
- A command-line minimal example using a synthetic isotropic tensor.
- An `ANISOSCOPE_DISABLE_PYVISTA` switch that forces the Matplotlib 3D fallback
  on unsupported remote or headless hosts without changing scientific results.

### Changed

- Expanded the README so installation, use, scientific conventions, exports,
  limitations, and maintenance pathways are directly reviewable.
- Direction paths interpolate on the sphere and record that convention, plus a
  radian distance unit, in sampled-data sidecars.
- The desktop workflow now gates exports on a completed analysis, wraps the
  3D/1D/2D toolbars, and uses status colors for ready, dirty, warning, and
  error states.
- Results now use readable diagnostic sections, status words, labels, units,
  and compact values instead of exposing internal field names.
- Mode-specific 1D/2D controls are shown only when they affect the selected
  sampling route.
- The input column now scrolls on laptop-height displays while the action group
  stays pinned, instead of forcing the whole window beyond the available screen.
- Narrow windows now stack the input and results areas vertically, with
  independent scrolling so analysis controls and every result tab remain
  reachable.
- Three-dimensional views now mark and report sampled-grid extrema, directions,
  grid dimensions, and the selected transverse aggregation without presenting
  the samples as continuous global extrema.

### Fixed

- Restored README sections required by the repository's documentation
  regression test.
- Prevented high-symmetry matrices from being reported as passing when their
  entries violate the selected crystal-system relations.
- Made unknown crystal-system labels fail closed and report a clear failed
  condition instead of allowing a numerically positive-definite matrix through.
- Derived or validated symmetry-dependent `C66` in hexagonal and trigonal input
  templates.
- Recorded sampling grids and transverse aggregation in figure, animation, and
  sampled-data sidecar manifests, including the fixed 72-point transverse scan.
- Reported unsupported transverse aggregation modes as a clear `ValueError`.
- Stabilized CI linting across Ruff default-rule changes and isolated native
  PyVista rendering from unsupported Windows Server test environments.
- Cleared cached scalars and figures after matrix or crystal-system edits so
  the dashboard cannot show a previous Hill result as current.
- Stopped a material-name keystroke from wiping a completed analysis.
- Reported matrix-level symmetry, invertibility, and positive-definiteness
  failures in `failed_conditions` instead of only in flags.
- Rejected `.xls` model-table paths and transparent MP4 export before writing
  files; applied GIF transparency through Matplotlib instead of recording an
  unused option.
- Reported CSV/Excel read errors and kept stability diagnostics when derived
  polycrystalline analysis fails.
- Protected stiffness and compliance arrays from external mutation so cached
  tensor results cannot silently diverge from the stored matrix.
- Staged complete analysis packages before publishing their owned files and
  rolled back partial replacement failures without touching unrelated files.
- Invalidated stale previews after rendering-style changes and reported a
  partial analysis when any requested figure fails.
- Recorded the actual animation and paper-rendering backend, fallback reason,
  and animation frame rate in manifests while preserving GIF/MP4 defaults.
- Centered sign-changing diverging 3D palettes at zero and included physical
  units in default 2D polar titles.
- Matched Matplotlib plot labels to the selected transverse `min`, `max`, or
  `mean` aggregation and derived explicit-colormap normalization from the
  colormap actually rendered.
- Recorded requested and ignored 3D style options separately whenever a
  Matplotlib fallback is used, so sidecars no longer claim PyVista-only effects.
- Recovered from generic PyVista/VTK preview failures through the Matplotlib
  fallback while preserving both errors if the fallback also fails.
- Closed embedded plot resources with the desktop window to avoid accumulated
  Matplotlib figures during repeated sessions and tests.
- Published each animation with its sidecar and all three paper figures with
  their sidecars as rollback-protected file sets, without following output
  symlinks or replacing directories.
- Initialized Windows Qt font discovery before either the standalone matrix
  editor or the main window creates an application, keeping responsive sizing
  stable across import order.

## [0.1.0] - not yet tagged

- Initial AnisoScope desktop GUI and numerical toolkit.
- Crystal-system templates, stability checks, Voigt/Reuss/Hill summaries,
  directional sampling, plots, animations, and traceable exports.

Version `0.1.0` is present in the package metadata, but no Git tag or GitHub
Release is claimed here.
