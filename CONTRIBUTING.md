# Contributing to AnisoScope

Thank you for helping improve AnisoScope. Contributions may include bug reports,
documentation, numerical validation cases, tests, or code changes.

## Before opening an issue

- Search existing issues for the same behavior.
- Confirm the problem on the current default branch when practical.
- Remove confidential or unpublished material from matrices and manifests.
- For a numerical discrepancy, state the Voigt order, engineering/tensorial
  shear convention, units, crystal system, and an independently derived
  expected value or reference.

Security-sensitive reports should follow [`SECURITY.md`](SECURITY.md) instead of
using a public issue.

## Development setup

AnisoScope supports Python 3.11, 3.12, and 3.13. From a clone of the repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

On macOS or Linux, use `python3 -m venv .venv` and
`source .venv/bin/activate` before the two `pip` commands.

## Making a change

1. Create a focused branch from the current default branch.
2. Keep numerical logic separate from GUI state and rendering where possible.
3. Preserve the fixed Voigt order `[11, 22, 33, 23, 13, 12]` and engineering
   shear convention unless the change explicitly introduces and documents a
   new convention.
4. Add or update tests for changed behavior. Numerical tests should use an
   analytic limit, independently calculated value, or cited reference rather
   than only snapshotting the current implementation.
5. Update user or API documentation when commands, inputs, outputs, or limits
   change.
6. Do not commit environments, downloaded papers, generated output packages,
   caches, build directories, or manuscript PDFs.

## Verification

Run the test suite:

```powershell
python -m pytest -q
```

Run the executable example:

```powershell
python examples\minimal_analysis.py --output outputs\minimal-example
```

Build the distribution artifacts:

```powershell
python -m build
```

Before opening a pull request, check `git status --short` and include only the
files needed for the change. In the pull request, describe the motivation,
verification commands and results, scientific assumptions, compatibility
impact, and any remaining limitation.

## Merge readiness

Before merging a change:

- Confirm `git status --short --branch` contains only intended files.
- Run `python -m pytest -q` in the supported virtual environment.
- Build the source distribution and wheel.
- Check that README commands and GUI labels still match the software.
- Confirm exported manifests retain the inputs needed to interpret the output.
- Keep generated figures, `outputs/`, environments, caches, and build artifacts
  out of version control.

## Review expectations

Maintainers may request a smaller reproduction, stronger numerical evidence,
documentation updates, or a regression test. No performance, compatibility, or
scientific-validity claim should be added without reproducible evidence.
