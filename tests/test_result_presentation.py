import numpy as np

from crystal_elastic_workbench.result_presentation import (
    format_sampled_surface_extrema,
    format_stability_report,
    summary_display_rows,
    summary_labeled_values,
)
from crystal_elastic_workbench.sampling import DirectionalSurface
from crystal_elastic_workbench.stability import StabilityResult


def test_stability_report_uses_readable_sections_and_statuses():
    result = StabilityResult(
        is_symmetric=True,
        is_invertible=True,
        is_positive_definite=True,
        born_stable=True,
        overall_stable=True,
        condition_number=3.6871859296,
        min_eigenvalue_gpa=79.6,
        failed_conditions=[],
        warnings=[],
        crystal_system_relations_checked=True,
        matches_crystal_system=True,
        born_criteria_applied=True,
    )

    report = format_stability_report(result)

    assert "Matrix checks" in report
    assert "Symmetry: PASS" in report
    assert "Minimum eigenvalue: 79.6 GPa" in report
    assert "Selected crystal system" in report
    assert "Matrix relations: PASS" in report
    assert "Born criteria: PASS" in report
    assert "Overall stability: PASS" in report
    assert "Failed conditions\n  None" in report
    assert "Warnings\n  None" in report
    assert "is_symmetric" not in report


def test_stability_report_keeps_failures_and_not_applied_states_visible():
    result = StabilityResult(
        is_symmetric=False,
        is_invertible=True,
        is_positive_definite=False,
        born_stable=None,
        overall_stable=False,
        condition_number=1.25e12,
        min_eigenvalue_gpa=-2.5,
        failed_conditions=["Cij is not symmetric", "matrix is not positive definite"],
        warnings=["Condition number is high."],
        crystal_system_relations_checked=False,
        matches_crystal_system=None,
        born_criteria_applied=False,
    )

    report = format_stability_report(result)

    assert "Symmetry: FAIL" in report
    assert "Positive definiteness: FAIL" in report
    assert "Matrix relations: NOT CHECKED" in report
    assert "Born criteria: NOT APPLIED" in report
    assert "Overall stability: FAIL" in report
    assert "  - Cij is not symmetric" in report
    assert "  - Condition number is high." in report


def test_summary_rows_replace_internal_keys_with_labels_and_units():
    rows = summary_display_rows(
        {
            "bulk_voigt_gpa": 97.833333333,
            "young_hill_gpa": 162.71864,
            "poisson_hill": 0.22279618,
            "bulk_anisotropy_percent": 0.0,
            "cauchy_pressure_gpa": None,
        }
    )

    assert rows == [
        ("Bulk modulus (Voigt) [GPa]", "97.8333"),
        ("Young's modulus (Hill) [GPa]", "162.719"),
        ("Poisson ratio (Hill)", "0.222796"),
        ("Bulk anisotropy [%]", "0"),
        ("Cauchy pressure [GPa]", "not applicable"),
    ]


def test_summary_rows_have_a_readable_fallback_for_future_fields():
    assert summary_display_rows({"future_metric": 1.25}) == [("Future metric", "1.25")]


def test_summary_labeled_values_keep_numeric_types_for_export():
    assert summary_labeled_values({"bulk_voigt_gpa": 97.5, "cauchy_pressure_gpa": None}) == {
        "Bulk modulus (Voigt) [GPa]": 97.5,
        "Cauchy pressure [GPa]": None,
    }


def test_surface_extrema_report_names_grid_resolution_mode_and_directions():
    values = np.array([[-0.2, 0.4], [0.1, 0.3]])
    surface = DirectionalSurface(
        property_name="poisson",
        theta=np.zeros((2, 2)),
        phi=np.zeros((2, 2)),
        directions=np.zeros((2, 2, 3)),
        values=values,
        x=np.zeros((2, 2)),
        y=np.zeros((2, 2)),
        z=np.zeros((2, 2)),
        min_value=-0.2,
        max_value=0.4,
        min_direction=np.array([1.0, 0.0, 0.0]),
        max_direction=np.array([0.0, 1.0, 0.0]),
        transverse_mode="min",
    )

    report = format_sampled_surface_extrema(surface)

    assert "Sampled-grid extrema (theta x phi = 2 x 2" in report
    assert "transverse min over 72 sampled directions" in report
    assert "refine theta/phi and transverse sampling to check convergence" in report
    assert "nu, transverse min" in report
    assert "at n=(+1.000, +0.000, +0.000)" in report
    assert "at n=(+0.000, +1.000, +0.000)" in report
