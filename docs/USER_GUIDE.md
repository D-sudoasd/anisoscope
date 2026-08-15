# AnisoScope user guide

## 1. What the software expects

AnisoScope accepts a finite, invertible `6 × 6` elastic stiffness matrix using
the Voigt order `[11, 22, 33, 23, 13, 12]`. Values displayed by the current GUI
and exports are interpreted as GPa. Shear strains use the engineering
convention `[e11, e22, e33, 2e23, 2e13, 2e12]`.

Before analysis, confirm the source's tensor convention, unit, axis order,
temperature, pressure, and crystal symmetry. AnisoScope cannot infer or certify
those physical inputs.

## 2. Start the application

Install the package as described in the README, then run:

```powershell
python -m anisoscope
```

The application opens with a matrix editor and tabs for the dashboard, scalar
results, one-dimensional paths, polar slices, and three-dimensional surfaces.

## 3. Enter a tensor

Choose one of three routes:

- select a bundled demonstration matrix;
- paste a rectangular numeric block from a spreadsheet; or
- enter or edit matrix cells manually.

Selecting a crystal-system template exposes the independent constants expected
by that template. The full matrix remains the numerical input to the analysis.
Editing a single off-diagonal cell mirrors it to preserve symmetry; importing a
complete matrix preserves asymmetry so that it can be diagnosed.

The bundled Al, Si, and MgO values have no literature provenance in the current
repository. Treat them only as interface demonstrations and regression inputs.

## 4. Analyze and interpret diagnostics

Select **Analyze + Update Figures**. The stability report distinguishes:

- symmetry within the configured tolerance;
- agreement with the selected high-symmetry template relations, when implemented;
- numerical invertibility and condition number;
- positive definiteness of the symmetrized matrix; and
- applicable implemented crystal-system Born inequalities.

The relation checks use the conventions implemented by the input templates.
For monoclinic and triclinic systems, no relation validator or compact
system-specific Born shortcut is applied; users must confirm the source axis and
sign convention, while symmetry, invertibility, and positive definiteness
provide the numerical diagnostics. Trigonal inputs also require special care
because published sign and axis conventions can differ.

The Results tab reports Voigt and Reuss bounds and their Hill arithmetic mean.
The geometric estimate is an additional empirical center and is not a rigorous
bound. Cubic-only Zener anisotropy and Cauchy pressure are shown only for a cubic
tensor.

## 5. Directional properties

AnisoScope can evaluate:

- Young's modulus, $E(\mathbf{n})$;
- linear compressibility, $\beta(\mathbf{n})$;
- shear modulus, $G(\mathbf{n},\mathbf{m})$; and
- Poisson ratio, $\nu(\mathbf{n},\mathbf{m})$.

For shear modulus and Poisson ratio, the transverse direction
$\mathbf{m}$ must be orthogonal to the loading direction $\mathbf{n}$. Surface
plots use the mean of a 72-point transverse scan by default. That value must not
be described as the global transverse minimum or maximum.

Sampling density controls visual and numerical resolution. A denser grid is not
automatically more scientifically valid; verify convergence for the intended
quantity and report the chosen sampling counts.

## 6. Export results

Use **Export Full Package** when results need to be inspected or reused. The
package contains the stiffness/compliance matrices, scalar summaries, stability
diagnostics, sampled planes and surfaces, and `manifest.json`.

Use the relevant tab's export control for one figure or sampled data set. A
sidecar manifest records the tensor, unit, crystal system, program version,
sampling grid, plotting style, and output filename. For shear and Poisson-ratio
sampling, it also records the transverse aggregation and sample count. Keep
each sidecar with its corresponding output.

## 7. Reproducible minimal check

Run the repository example after installation:

```powershell
python examples\minimal_analysis.py --output outputs\minimal-example
```

The example constructs an analytic synthetic isotropic tensor with bulk modulus
140 GPa and shear modulus 60 GPa. It checks stability, evaluates the expected
direction-independent elastic response, samples the `xy` plane, and writes a
small result package.

## 8. Troubleshooting

- **The window does not open:** confirm PySide6 imports in the active environment
  and that the correct environment owns the `anisoscope` command.
- **A matrix cannot be inverted:** check for missing rows, wrong units, duplicated
  axes, or a singular/ill-conditioned tensor.
- **A plot is blank or VTK is unstable in a remote/headless session:** set
  `ANISOSCOPE_DISABLE_PYVISTA=1` to force the Matplotlib fallback, or configure
  a working off-screen VTK/OpenGL environment. Accepted true values are `1`,
  `true`, `yes`, and `on` (case-insensitive); unset the variable or set it to
  `0` to restore the default PyVista preference. This changes only the 3D
  rendering backend, not tensor analysis, stability checks, or sampling.
- **MP4 export fails:** install `ffmpeg` and confirm it is on `PATH`, or export a
  GIF instead.
- **Numbers differ from another package:** first compare Voigt order, shear
  convention, transverse aggregation, units, and sampling grid.
