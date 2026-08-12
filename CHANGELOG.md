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

### Changed

- Expanded the README so installation, use, scientific conventions, exports,
  limitations, and maintenance pathways are directly reviewable.

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

## [0.1.0] - not yet tagged

- Initial AnisoScope desktop GUI and numerical toolkit.
- Crystal-system templates, stability checks, Voigt/Reuss/Hill summaries,
  directional sampling, plots, animations, and traceable exports.

Version `0.1.0` is present in the package metadata, but no Git tag or GitHub
Release is claimed here.
