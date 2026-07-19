<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="AnisoScope: crystal elastic anisotropy from a 6x6 stiffness matrix Cij.">
</p>

# AnisoScope

**Directional elastic properties from a 6×6 stiffness matrix — with provenance.**

AnisoScope is a Python desktop tool for inspecting crystal elastic anisotropy from Voigt `Cij`. It is aimed at research workflows where **traceability** matters: the program keeps the input matrix, unit, crystal system, sampling parameters, plotting style, and export settings with the generated results.

Priority: **correctness and provenance first**, then publication-quality visualization.

## What it does

- Read a full `6×6` Voigt stiffness matrix (normally GPa)
- Templates for cubic, hexagonal, tetragonal, orthorhombic, trigonal/rhombohedral, monoclinic, triclinic
- Matrix quality: symmetry, invertibility, condition number, positive definiteness, Born criteria where available
- Compliance `Sij`; polycrystalline scalars (Voigt/Reuss/Hill `B`, `G`, `E`, `ν`, `B/G`, `A_U`, …)
- Directional: `E(n)`, linear compressibility `β(n)`, transverse-mean `G(n,m)` and `ν(n,m)`
- Figures: 1D paths, 2D polar slices, 3D surfaces; GIF and MP4 when `ffmpeg` is available
- Export packages with **sidecar manifests** for reproduction

## Install

Python **3.11+** (Windows-focused GUI via PySide6 / PyVista):

```powershell
git clone https://github.com/D-sudoasd/anisoscope.git
cd anisoscope
py -3.11 -m pip install -r requirements.txt
# or editable: py -3.11 -m pip install -e .[test]
```

Runtime: `numpy`, `pandas`, `openpyxl`, `matplotlib`, `pyvista`, `vtk`, `PySide6`, `imageio` (+ `pytest` for tests).

## Launch

```powershell
py -3.11 -m anisoscope
# or after install:
anisoscope
# or:
.\start_anisoscope.bat
```

Legacy aliases: `python -m crystal_elastic_workbench` / `crystal-elastic-workbench`.

## GUI workflow

1. Choose crystal system and material name.  
2. Enter, paste, or import a `6×6` matrix.  
3. **Analyze + Update Figures**.  
4. Inspect Dashboard, Results, and 1D / 2D / 3D tabs.  
5. Export data/figures or **Export Full Package** / **Export Paper Figures**.

Off-diagonal edits update the symmetric mirror; full imports preserve source asymmetry so analysis can still detect it.

## Cij convention

Voigt order:

```text
[11, 22, 33, 23, 13, 12]
```

Engineering shear strain in Voigt form (intentional — avoids common factor-of-two shear mistakes). Directional shear uses physical stress tensors and converts back to a symmetric strain tensor.

## Examples

GUI built-ins: Al, Si, MgO cubic. JSON: `examples/al_cubic.json`, `si_cubic.json`, `mgo_cubic.json`. For publication, verify temperature, pressure, source convention, and units against your reference.

## Calculation notes

Standard Voigt/Reuss averages; Hill is the arithmetic mean of Voigt and Reuss. `G(n,m)` and `ν(n,m)` require `m ⊥ n`. 3D shear/Poisson surfaces use **transverse means by default**, not strict transverse extrema.

## Export package

`Export Full Package` includes among others: `manifest.json`, stiffness/compliance CSVs, polycrystalline and model summaries, stability JSON, plane and surface sample CSVs. Single-figure and animation exports also write `<filename>.manifest.json` with input `Cij`, unit, system, style, and sampling.

## 3D rendering

Preferred path: PyVista/VTK surface + Matplotlib high-DPI titles/colorbars. Fallback: pure Matplotlib 3D. Sequential palettes for modulus; diverging only when a meaningful center exists.

## Tests

```powershell
py -3.11 -m pytest -q
```

## Known limits

- Cannot prove user `Cij` are scientifically correct — verify units, convention, T, P, symmetry.  
- Trigonal/monoclinic templates follow common conventions; literature may differ.  
- Monoclinic/triclinic rely mainly on positive definiteness.  
- High 3D sampling for shear/Poisson is slow; MP4 needs local `ffmpeg` (GIF safer).  

## License

See repository license file if present; treat source provenance as required for published figures.
