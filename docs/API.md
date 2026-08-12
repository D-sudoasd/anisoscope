# Public Python API

AnisoScope's stable public numerical interface is intentionally small. Import
these names from `anisoscope` or `crystal_elastic_workbench`:

```python
from anisoscope import ElasticTensor, PolycrystalSummary, StabilityResult, check_stability
```

The implementation currently lives in `crystal_elastic_workbench`; the
`anisoscope` package provides the public project-name import path.

## `ElasticTensor`

```python
ElasticTensor(
    stiffness_matrix,
    *,
    crystal_system="triclinic",
    unit="GPa",
    material_name="Untitled",
    symmetrize=False,
)
```

`stiffness_matrix` must be a finite `6 × 6` array in Voigt order
`[11, 22, 33, 23, 13, 12]`. Construction computes its inverse; a singular matrix
raises `numpy.linalg.LinAlgError`. `symmetrize=False` preserves the supplied
matrix so asymmetry remains detectable.

Important methods:

- `polycrystalline_summary()` returns a frozen `PolycrystalSummary` containing
  Voigt, Reuss, and Hill elastic estimates and anisotropy metrics.
- `youngs_modulus(direction)` returns $E(\mathbf{n})$ in GPa.
- `linear_compressibility(direction)` returns $\beta(\mathbf{n})$ in GPa⁻¹.
- `shear_modulus(direction, transverse)` returns
  $G(\mathbf{n},\mathbf{m})$ in GPa.
- `poisson_ratio(direction, transverse)` returns
  $\nu(\mathbf{n},\mathbf{m})$.
- `transverse_scan(direction, property_name=..., samples=72)` reports the
  sampled transverse minimum, maximum, and arithmetic mean.

Direction vectors are normalized internally. A zero or non-finite direction,
or non-orthogonal transverse direction, raises `ValueError`.

## `check_stability`

```python
result = check_stability(matrix, crystal_system="cubic")
```

The returned `StabilityResult` separates symmetry, whether crystal-system
relations were checked and matched, invertibility, positive definiteness,
whether Born inequalities were applied and passed, the matrix condition number,
minimum eigenvalue, failed conditions, and warnings. `overall_stable` is true
only when all applicable checks pass. High-symmetry relation checks follow the
implemented template conventions; monoclinic and triclinic source conventions
are not validated. The check uses a symmetrized matrix for the remaining
diagnostics but reports an asymmetric input as a failure.

## Sampling API

Sampling helpers are available from `crystal_elastic_workbench.sampling`:

```python
from crystal_elastic_workbench.sampling import (
    sample_direction_path,
    sample_plane,
    sample_sphere,
)
```

- `sample_plane(..., angle_count=361)` returns a `PlaneSlice`.
- `sample_sphere(..., theta_count=37, phi_count=73)` returns a
  `DirectionalSurface`.
- `sample_direction_path(..., points_per_segment=101)` returns a
  `DirectionPath`.

For shear and Poisson sampling, `transverse_mode` selects `min`, `max`, or
`mean` from the fixed 72-point transverse scan. The default is `mean`; other
values raise `ValueError`.

## Export API

```python
from crystal_elastic_workbench.exporting import export_analysis_package

manifest = export_analysis_package(
    tensor,
    "outputs/example",
    plane_angle_count=37,
    sphere_theta_count=7,
    sphere_phi_count=13,
)
```

The function returns the path to `manifest.json`. It also writes matrix tables,
scalar summaries, model diagnostics, stability information, and sampled data.
Existing files with the same names in the output directory are overwritten, so
use a dedicated output directory for each run.
