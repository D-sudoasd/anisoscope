"""Human-readable presentation helpers for desktop analysis results."""

from __future__ import annotations

from collections.abc import Mapping

from crystal_elastic_workbench.sampling import DirectionalSurface
from crystal_elastic_workbench.stability import StabilityResult


SUMMARY_LABELS = {
    "bulk_voigt_gpa": "Bulk modulus (Voigt) [GPa]",
    "bulk_reuss_gpa": "Bulk modulus (Reuss) [GPa]",
    "bulk_hill_gpa": "Bulk modulus (Hill) [GPa]",
    "shear_voigt_gpa": "Shear modulus (Voigt) [GPa]",
    "shear_reuss_gpa": "Shear modulus (Reuss) [GPa]",
    "shear_hill_gpa": "Shear modulus (Hill) [GPa]",
    "young_hill_gpa": "Young's modulus (Hill) [GPa]",
    "poisson_hill": "Poisson ratio (Hill)",
    "pugh_ratio": "Pugh ratio B/G",
    "universal_anisotropy": "Universal anisotropy index",
    "bulk_anisotropy_percent": "Bulk anisotropy [%]",
    "shear_anisotropy_percent": "Shear anisotropy [%]",
    "cauchy_pressure_gpa": "Cauchy pressure [GPa]",
    "zener_anisotropy": "Zener anisotropy ratio",
}

_SURFACE_SYMBOLS = {
    "young": "E",
    "compressibility": "beta",
    "shear": "G",
    "poisson": "nu",
}

_SURFACE_UNITS = {
    "young": "GPa",
    "compressibility": "1/GPa",
    "shear": "GPa",
    "poisson": "",
}


def _status(value: bool | None, *, unavailable: str) -> str:
    if value is None:
        return unavailable
    return "PASS" if value else "FAIL"


def _list_section(title: str, values: list[str]) -> list[str]:
    return [title, *(f"  - {value}" for value in values)] if values else [title, "  None"]


def format_stability_report(result: StabilityResult) -> str:
    """Format stability diagnostics for researchers rather than internal field names."""

    lines = [
        "Matrix checks",
        f"  Symmetry: {_status(result.is_symmetric, unavailable='NOT CHECKED')}",
        f"  Invertibility: {_status(result.is_invertible, unavailable='NOT CHECKED')}",
        f"  Positive definiteness: {_status(result.is_positive_definite, unavailable='NOT CHECKED')}",
        f"  Minimum eigenvalue: {result.min_eigenvalue_gpa:.6g} GPa",
        f"  Condition number: {result.condition_number:.6g}",
        "",
        "Selected crystal system",
        "  Matrix relations: "
        + _status(
            result.matches_crystal_system if result.crystal_system_relations_checked else None,
            unavailable="NOT CHECKED",
        ),
        "  Born criteria: "
        + _status(result.born_stable if result.born_criteria_applied else None, unavailable="NOT APPLIED"),
        f"  Overall stability: {_status(result.overall_stable, unavailable='NOT CHECKED')}",
        "",
        *_list_section("Failed conditions", result.failed_conditions),
        "",
        *_list_section("Warnings", result.warnings),
    ]
    return "\n".join(lines)


def _fallback_label(key: str) -> str:
    return key.replace("_", " ").strip().capitalize()


def summary_display_rows(values: Mapping[str, float | None]) -> list[tuple[str, str]]:
    """Return display labels and compact values while preserving source order."""

    rows: list[tuple[str, str]] = []
    for key, value in values.items():
        label = SUMMARY_LABELS.get(key, _fallback_label(key))
        value_text = "not applicable" if value is None else f"{float(value):.6g}"
        rows.append((label, value_text))
    return rows


def summary_labeled_values(values: Mapping[str, float | None]) -> dict[str, float | None]:
    """Return numeric summary values under the same readable labels as the GUI."""

    return {
        SUMMARY_LABELS.get(key, _fallback_label(key)): value
        for key, value in values.items()
    }


def format_sampled_surface_extrema(surface: DirectionalSurface) -> str:
    """Describe grid extrema without presenting them as a continuous global search."""

    symbol = _SURFACE_SYMBOLS.get(surface.property_name, surface.property_name)
    unit = _SURFACE_UNITS.get(surface.property_name, "")
    if surface.property_name in {"shear", "poisson"}:
        symbol = f"{symbol}, transverse {surface.transverse_mode}"
    unit_suffix = f" {unit}" if unit else ""

    def direction_text(direction) -> str:
        return "(" + ", ".join(f"{float(component):+.3f}" for component in direction) + ")"

    rows, columns = surface.values.shape
    sampling_note = f"theta x phi = {rows} x {columns}"
    convergence_note = "refine theta/phi to check convergence"
    if surface.property_name in {"shear", "poisson"}:
        sampling_note += (
            f"; transverse {surface.transverse_mode} over "
            f"{surface.transverse_samples} sampled directions"
        )
        convergence_note = "refine theta/phi and transverse sampling to check convergence"
    return (
        f"Sampled-grid extrema ({sampling_note}; {convergence_note}):\n"
        f"{symbol} min {surface.min_value:.6g}{unit_suffix} "
        f"at n={direction_text(surface.min_direction)}\n"
        f"{symbol} max {surface.max_value:.6g}{unit_suffix} "
        f"at n={direction_text(surface.max_direction)}"
    )
