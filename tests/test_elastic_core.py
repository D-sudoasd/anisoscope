import math

import numpy as np
import pytest

from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.stability import check_stability
from crystal_elastic_workbench.templates import apply_crystal_template


def isotropic_cubic_matrix(bulk_gpa: float = 160.0, shear_gpa: float = 80.0) -> np.ndarray:
    """Return an exactly isotropic cubic stiffness matrix in Voigt notation."""
    c11 = bulk_gpa + 4.0 * shear_gpa / 3.0
    c12 = bulk_gpa - 2.0 * shear_gpa / 3.0
    c44 = shear_gpa
    return np.array(
        [
            [c11, c12, c12, 0.0, 0.0, 0.0],
            [c12, c11, c12, 0.0, 0.0, 0.0],
            [c12, c12, c11, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, c44, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, c44, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, c44],
        ],
        dtype=float,
    )


def test_vrh_reduces_to_input_bulk_and_shear_for_isotropic_cubic():
    tensor = ElasticTensor(isotropic_cubic_matrix(160.0, 80.0), crystal_system="cubic")

    summary = tensor.polycrystalline_summary()

    assert summary.bulk_voigt_gpa == pytest.approx(160.0)
    assert summary.bulk_reuss_gpa == pytest.approx(160.0)
    assert summary.bulk_hill_gpa == pytest.approx(160.0)
    assert summary.shear_voigt_gpa == pytest.approx(80.0)
    assert summary.shear_reuss_gpa == pytest.approx(80.0)
    assert summary.shear_hill_gpa == pytest.approx(80.0)
    assert summary.young_hill_gpa == pytest.approx(205.71428571428572)
    assert summary.poisson_hill == pytest.approx(0.2857142857142857)
    assert summary.universal_anisotropy == pytest.approx(0.0, abs=1e-12)


def test_directional_properties_use_engineering_shear_convention_correctly():
    tensor = ElasticTensor(isotropic_cubic_matrix(160.0, 80.0), crystal_system="cubic")

    n = np.array([1.0, 0.0, 0.0])
    m = np.array([0.0, 1.0, 0.0])

    assert tensor.youngs_modulus(n) == pytest.approx(205.71428571428572)
    assert tensor.shear_modulus(n, m) == pytest.approx(80.0)
    assert tensor.poisson_ratio(n, m) == pytest.approx(0.2857142857142857)
    assert tensor.linear_compressibility(n) == pytest.approx(1.0 / (3.0 * 160.0))


def test_directional_youngs_modulus_is_rotation_invariant_for_isotropic_cubic():
    tensor = ElasticTensor(isotropic_cubic_matrix(160.0, 80.0), crystal_system="cubic")
    expected = 205.71428571428572

    for direction in ([1, 0, 0], [1, 1, 0], [1, 1, 1], [2, -1, 3]):
        assert tensor.youngs_modulus(direction) == pytest.approx(expected)


def test_stability_reports_positive_definite_and_born_rules():
    stable = check_stability(isotropic_cubic_matrix(160.0, 80.0), crystal_system="cubic")

    assert stable.is_symmetric
    assert stable.is_invertible
    assert stable.is_positive_definite
    assert stable.born_stable
    assert stable.overall_stable
    assert stable.min_eigenvalue_gpa > 0

    unstable_cubic = isotropic_cubic_matrix(160.0, 80.0)
    unstable_cubic[3, 3] = -5.0
    unstable = check_stability(unstable_cubic, crystal_system="cubic")

    assert not unstable.is_positive_definite
    assert not unstable.born_stable
    assert not unstable.overall_stable
    assert any("C44 > 0" in item for item in unstable.failed_conditions)


def test_stability_rejects_matrix_that_does_not_match_selected_crystal_system():
    not_cubic = isotropic_cubic_matrix(160.0, 80.0)
    not_cubic[1, 1] = 500.0

    result = check_stability(not_cubic, crystal_system="cubic")

    assert result.is_positive_definite
    assert not result.matches_crystal_system
    assert not result.overall_stable
    assert "crystal-system relation C11 = C22" in result.failed_conditions


def test_stability_rejects_hexagonal_matrix_with_inconsistent_c66():
    matrix = apply_crystal_template(
        "hexagonal",
        {"C11": 220.0, "C12": 80.0, "C13": 70.0, "C33": 240.0, "C44": 60.0},
    )
    matrix[5, 5] = 1.0

    result = check_stability(matrix, crystal_system="hexagonal")

    assert result.is_positive_definite
    assert not result.matches_crystal_system
    assert not result.overall_stable
    assert "crystal-system relation C66 = (C11 - C12)/2" in result.failed_conditions


def test_stability_marks_unapplied_monoclinic_and_triclinic_checks_as_not_evaluated():
    matrix = isotropic_cubic_matrix(160.0, 80.0)

    for system in ("monoclinic", "triclinic"):
        result = check_stability(matrix, crystal_system=system)
        assert not result.crystal_system_relations_checked
        assert result.matches_crystal_system is None
        assert not result.born_criteria_applied
        assert result.born_stable is None
        assert result.overall_stable


def test_unknown_crystal_system_fails_closed():
    result = check_stability(np.eye(6), crystal_system="not-a-system")

    assert not result.crystal_system_relations_checked
    assert result.matches_crystal_system is None
    assert not result.overall_stable
    assert result.failed_conditions == [
        "supported crystal system ('not-a-system' is unknown)"
    ]


def test_rhombohedral_alias_applies_trigonal_born_criteria_and_fails_closed():
    matrix = apply_crystal_template(
        "rhombohedral",
        {"C11": 220.0, "C12": 80.0, "C13": 70.0, "C14": 90.0, "C33": 240.0, "C44": 60.0},
    )

    result = check_stability(matrix, crystal_system="rhombohedral")

    assert result.crystal_system_relations_checked
    assert result.matches_crystal_system
    assert result.born_criteria_applied
    assert result.born_stable is False
    assert result.overall_stable is False
    assert any("(C11 - C12)*C44 > 2*C14^2" in item for item in result.failed_conditions)


def test_rejects_invalid_direction_and_non_orthogonal_transverse_direction():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    with pytest.raises(ValueError, match="non-zero"):
        tensor.youngs_modulus([0.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="orthogonal"):
        tensor.shear_modulus([1.0, 0.0, 0.0], [1.0, 1.0, 0.0])


def test_roundtrip_compliance_inverts_stiffness_matrix():
    matrix = isotropic_cubic_matrix(160.0, 80.0)
    tensor = ElasticTensor(matrix, crystal_system="cubic")

    assert np.linalg.norm(matrix @ tensor.compliance_matrix - np.eye(6)) < 1e-10
    assert math.isfinite(tensor.condition_number)


def test_directional_property_rejects_unknown_transverse_mode():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    with pytest.raises(ValueError, match="transverse_mode"):
        tensor.directional_property(
            [1.0, 0.0, 0.0],
            property_name="shear",
            transverse_mode="median",
        )


def test_tensor_accepts_only_gpa_and_normalizes_unit_label():
    tensor = ElasticTensor(isotropic_cubic_matrix(), unit="gpa")
    assert tensor.unit == "GPa"

    with pytest.raises(ValueError, match="unit must be 'GPa'"):
        ElasticTensor(isotropic_cubic_matrix(), unit="MPa")
