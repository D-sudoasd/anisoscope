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

## [0.1.0] - not yet tagged

- Initial AnisoScope desktop GUI and numerical toolkit.
- Crystal-system templates, stability checks, Voigt/Reuss/Hill summaries,
  directional sampling, plots, animations, and traceable exports.

Version `0.1.0` is present in the package metadata, but no Git tag or GitHub
Release is claimed here.
