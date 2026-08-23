import json
from pathlib import Path

import numpy as np
import pytest

from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.exporting import (
    export_analysis_package,
    export_elastic_model_table,
    export_sampled_data,
    path_to_frame,
    sampled_data_to_frame,
    write_export_manifest,
)
from crystal_elastic_workbench.sampling import sample_direction_path, sample_plane, sample_sphere


def isotropic_cubic_matrix(bulk_gpa: float = 160.0, shear_gpa: float = 80.0) -> np.ndarray:
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


def test_plane_sampling_returns_unit_directions_in_requested_plane():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    result = sample_plane(tensor, property_name="young", plane="xy", angle_count=181)

    assert result.angles_deg.shape == (181,)
    assert result.values.shape == (181,)
    assert np.allclose(np.linalg.norm(result.directions, axis=1), 1.0)
    assert np.allclose(result.directions[:, 2], 0.0)
    assert np.ptp(result.values) == pytest.approx(0.0, abs=1e-8)
    assert result.values[0] == pytest.approx(205.71428571428572)


def test_sphere_sampling_has_grid_shape_and_reports_extrema():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    surface = sample_sphere(tensor, property_name="young", theta_count=13, phi_count=25)

    assert surface.values.shape == (13, 25)
    assert surface.x.shape == surface.values.shape
    assert surface.min_value == pytest.approx(205.71428571428572)
    assert surface.max_value == pytest.approx(205.71428571428572)
    assert np.linalg.norm(surface.min_direction) == pytest.approx(1.0)
    assert np.linalg.norm(surface.max_direction) == pytest.approx(1.0)


def test_direction_path_sampling_supports_high_symmetry_style_paths():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    path = sample_direction_path(
        tensor,
        property_name="young",
        points=[
            ("[100]", [1, 0, 0]),
            ("[110]", [1, 1, 0]),
            ("[111]", [1, 1, 1]),
        ],
        points_per_segment=9,
    )

    assert path.values.size == path.directions.shape[0]
    assert path.tick_labels == ["[100]", "[110]", "[111]"]
    assert np.all(np.diff(path.distance) >= 0.0)
    assert np.allclose(np.linalg.norm(path.directions, axis=1), 1.0)
    assert np.ptp(path.values) == pytest.approx(0.0, abs=1e-8)
    frame = path_to_frame(path)
    assert {"distance", "nx", "ny", "nz", "young"}.issubset(frame.columns)
    assert len(frame) == path.values.size


def test_direction_path_uses_spherical_interpolation_and_handles_antipodal_points():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    path = sample_direction_path(
        tensor,
        property_name="young",
        points=[("[100]", [1, 0, 0]), ("[110]", [1, 1, 0])],
        points_per_segment=5,
    )
    actual_angles = np.arccos(np.clip(path.directions @ path.directions[0], -1.0, 1.0))

    assert np.allclose(path.distance, actual_angles, atol=1e-12)
    assert path.directions[2] == pytest.approx(
        [np.cos(np.pi / 8.0), np.sin(np.pi / 8.0), 0.0], abs=1e-12
    )

    antipodal = sample_direction_path(
        tensor,
        property_name="young",
        points=[("[100]", [1, 0, 0]), ("[-100]", [-1, 0, 0])],
        points_per_segment=5,
    )

    assert np.allclose(np.linalg.norm(antipodal.directions, axis=1), 1.0)
    assert antipodal.distance[-1] == pytest.approx(np.pi)
    assert antipodal.directions[-1] == pytest.approx([-1.0, 0.0, 0.0], abs=1e-12)


def test_export_analysis_package_writes_traceable_manifest_and_data(tmp_path):
    tensor = ElasticTensor(
        isotropic_cubic_matrix(),
        crystal_system="cubic",
        unit="GPa",
        material_name="isotropic-test",
    )

    manifest_path = export_analysis_package(
        tensor,
        tmp_path,
        plane_angle_count=91,
        sphere_theta_count=9,
        sphere_phi_count=17,
    )

    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["program"] == "AnisoScope"
    assert manifest["material_name"] == "isotropic-test"
    assert manifest["unit"] == "GPa"
    assert manifest["crystal_system"] == "cubic"
    assert "stiffness_matrix_csv" in manifest["files"]
    assert "surface_young_csv" in manifest["files"]
    assert "model_table_csv" in manifest["files"]
    assert "model_table_xlsx" in manifest["files"]
    assert "model_table_notes_json" in manifest["files"]
    assert manifest["recommended_model"] == "Hill"
    assert manifest["included_models"] == ["Voigt", "Reuss", "Hill", "Geometric"]
    assert manifest["sampling"]["transverse_mode_for_shear_and_poisson"] == "mean"
    assert manifest["sampling"]["transverse_samples_for_shear_and_poisson"] == 72
    assert (tmp_path / manifest["files"]["stiffness_matrix_csv"]).exists()
    assert (tmp_path / manifest["files"]["surface_young_csv"]).exists()
    assert (tmp_path / manifest["files"]["model_table_csv"]).exists()
    assert (tmp_path / manifest["files"]["model_table_xlsx"]).exists()
    assert (tmp_path / manifest["files"]["model_table_notes_json"]).exists()
    notes = json.loads((tmp_path / manifest["files"]["model_table_notes_json"]).read_text(encoding="utf-8"))
    assert notes["recommended_model"] == "Hill"
    assert notes["diagnostics"]["B_spread"] == pytest.approx(0.0)


def test_export_analysis_package_failure_preserves_existing_package_and_unrelated_files(tmp_path):
    package_dir = tmp_path / "package"
    tensor = ElasticTensor(
        isotropic_cubic_matrix(),
        crystal_system="cubic",
        unit="GPa",
        material_name="atomic-export-test",
    )
    export_analysis_package(
        tensor,
        package_dir,
        plane_angle_count=19,
        sphere_theta_count=5,
        sphere_phi_count=7,
    )
    unrelated = package_dir / "user-not-owned.txt"
    unrelated.write_bytes(b"keep this file")
    before = {
        path.name: path.read_bytes()
        for path in package_dir.iterdir()
        if path.is_file()
    }
    failing_tensor = ElasticTensor(
        isotropic_cubic_matrix(bulk_gpa=180.0, shear_gpa=90.0),
        crystal_system="cubic",
        unit="GPa",
        material_name="failed-export-must-not-leak",
    )

    with pytest.raises(ValueError, match="angle_count must be at least 3"):
        export_analysis_package(
            failing_tensor,
            package_dir,
            plane_angle_count=2,
            sphere_theta_count=5,
            sphere_phi_count=7,
        )

    after = {
        path.name: path.read_bytes()
        for path in package_dir.iterdir()
        if path.is_file()
    }
    assert after == before
    assert unrelated.read_bytes() == b"keep this file"
    assert not list(tmp_path.glob(".analysis-package-*"))


def test_export_analysis_package_rolls_back_a_partial_commit(tmp_path, monkeypatch):
    from crystal_elastic_workbench import exporting as exporting_module

    package_dir = tmp_path / "package"
    original = ElasticTensor(
        isotropic_cubic_matrix(),
        crystal_system="cubic",
        unit="GPa",
        material_name="original-package",
    )
    export_analysis_package(
        original,
        package_dir,
        plane_angle_count=19,
        sphere_theta_count=5,
        sphere_phi_count=7,
    )
    unrelated = package_dir / "user-not-owned.txt"
    unrelated.write_bytes(b"keep this file")
    before = {path.name: path.read_bytes() for path in package_dir.iterdir() if path.is_file()}

    real_replace = exporting_module.os.replace
    failed_once = False

    def fail_during_commit(source, destination):
        nonlocal failed_once
        source_path = Path(source)
        if (
            not failed_once
            and source_path.name == "polycrystalline_summary.csv"
            and source_path.parent.name.startswith(".analysis-package-")
        ):
            failed_once = True
            raise OSError("injected commit failure")
        return real_replace(source, destination)

    monkeypatch.setattr(exporting_module.os, "replace", fail_during_commit)
    replacement = ElasticTensor(
        isotropic_cubic_matrix(bulk_gpa=180.0, shear_gpa=90.0),
        crystal_system="cubic",
        unit="GPa",
        material_name="replacement-must-roll-back",
    )

    with pytest.raises(OSError, match="injected commit failure"):
        export_analysis_package(
            replacement,
            package_dir,
            plane_angle_count=19,
            sphere_theta_count=5,
            sphere_phi_count=7,
        )

    after = {path.name: path.read_bytes() for path in package_dir.iterdir() if path.is_file()}
    assert failed_once is True
    assert after == before
    assert unrelated.read_bytes() == b"keep this file"
    assert not list(tmp_path.glob(".analysis-package-*"))


def test_export_analysis_package_accepts_numpy_integer_sampling_counts(tmp_path):
    tensor = ElasticTensor(
        isotropic_cubic_matrix(),
        crystal_system="cubic",
        unit="GPa",
        material_name="numpy-counts",
    )

    manifest_path = export_analysis_package(
        tensor,
        tmp_path / "package",
        plane_angle_count=np.int64(19),
        sphere_theta_count=np.int64(5),
        sphere_phi_count=np.int64(7),
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["sampling"]["plane_angle_count"] == 19
    assert manifest["sampling"]["sphere_theta_count"] == 5
    assert manifest["sampling"]["sphere_phi_count"] == 7


def test_export_sampled_data_writes_csv_and_manifest(tmp_path):
    tensor = ElasticTensor(
        isotropic_cubic_matrix(),
        crystal_system="cubic",
        unit="GPa",
        material_name="sampled-export-test",
    )
    plane = sample_plane(tensor, property_name="young", plane="xy", angle_count=19)

    output = export_sampled_data(tensor, plane, tmp_path / "plane.csv", kind="polar")

    assert output.exists()
    assert len(sampled_data_to_frame(plane)) == 19
    manifest = json.loads(output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8"))
    assert manifest["export_type"] == "polar_sampled_data"
    assert manifest["parameters"]["property"] == "young"
    assert manifest["parameters"]["rows"] == 19
    assert manifest["parameters"]["angle_count"] == 19
    assert "transverse_mode" not in manifest["parameters"]
    assert "transverse_samples" not in manifest["parameters"]


def test_custom_path_and_plane_manifests_preserve_exact_sampling_inputs(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    path = sample_direction_path(
        tensor,
        property_name="young",
        points=[("start", [1.0, 2.0, 3.0]), ("end", [-2.0, 1.0, 4.0])],
        points_per_segment=7,
    )
    normal = np.array([0.123456789, -0.987654321, 0.333333333])
    plane = sample_plane(tensor, property_name="young", plane=normal, angle_count=19)

    path_output = export_sampled_data(tensor, path, tmp_path / "path.csv", kind="line")
    plane_output = export_sampled_data(tensor, plane, tmp_path / "plane.csv", kind="polar")
    path_manifest = json.loads(
        path_output.with_name(f"{path_output.name}.manifest.json").read_text(encoding="utf-8")
    )
    plane_manifest = json.loads(
        plane_output.with_name(f"{plane_output.name}.manifest.json").read_text(encoding="utf-8")
    )

    assert path_manifest["parameters"]["path_labels"] == ["start", "end"]
    assert path_manifest["parameters"]["path_interpolation"] == "slerp"
    assert path_manifest["parameters"]["path_distance_unit"] == "radian"
    assert np.allclose(
        path_manifest["parameters"]["path_points"],
        np.array([[1.0, 2.0, 3.0], [-2.0, 1.0, 4.0]])
        / np.linalg.norm(np.array([[1.0, 2.0, 3.0], [-2.0, 1.0, 4.0]]), axis=1)[:, None],
    )
    assert np.allclose(
        plane_manifest["parameters"]["plane_normal"],
        normal / np.linalg.norm(normal),
        rtol=0.0,
        atol=1e-15,
    )


def test_shear_manifest_records_transverse_sampling(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    plane = sample_plane(tensor, property_name="shear", plane="xy", angle_count=19)

    output = export_sampled_data(tensor, plane, tmp_path / "shear.csv", kind="polar")
    manifest = json.loads(output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8"))

    assert manifest["parameters"]["transverse_mode"] == "mean"
    assert manifest["parameters"]["transverse_samples"] == 72


def test_sampling_normalizes_transverse_mode_case():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    plane = sample_plane(
        tensor,
        property_name="shear",
        plane="xy",
        angle_count=9,
        transverse_mode=" MAX ",
    )

    assert plane.transverse_mode == "max"


@pytest.mark.parametrize(("alias", "canonical"), [("g", "shear"), ("nu", "poisson")])
def test_transverse_property_aliases_are_canonicalized_in_manifest(tmp_path, alias, canonical):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    plane = sample_plane(tensor, property_name=alias, plane="xy", angle_count=19)

    output = export_sampled_data(tensor, plane, tmp_path / f"{canonical}.csv", kind="polar")
    manifest = json.loads(output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8"))

    assert plane.property_name == canonical
    assert manifest["parameters"]["property"] == canonical
    assert manifest["parameters"]["transverse_mode"] == "mean"
    assert manifest["parameters"]["transverse_samples"] == 72


def test_export_sampled_data_rejects_unknown_kind(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    plane = sample_plane(tensor, property_name="young", plane="xy", angle_count=19)

    with pytest.raises(ValueError, match="kind must be one of"):
        export_sampled_data(tensor, plane, tmp_path / "plane.csv", kind="unknown")


def test_export_elastic_model_table_writes_sidecar_manifest(tmp_path):
    tensor = ElasticTensor(
        isotropic_cubic_matrix(),
        crystal_system="cubic",
        unit="GPa",
        material_name="model-table-test",
    )

    output = export_elastic_model_table(tensor, tmp_path / "elastic_model_summary.csv")

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "Voigt" in text
    assert "Geometric" in text
    manifest = json.loads(output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8"))
    assert manifest["export_type"] == "elastic_model_table"
    assert manifest["parameters"]["recommended_model"] == "Hill"
    assert manifest["parameters"]["included_models"] == ["Voigt", "Reuss", "Hill", "Geometric"]


def test_export_elastic_model_table_rejects_mislabeled_xls_output(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")

    with pytest.raises(ValueError, match="supports .xlsx only"):
        export_elastic_model_table(tensor, tmp_path / "elastic_model_summary.xls")

    assert not (tmp_path / "elastic_model_summary.xls").exists()


def test_single_export_manifest_records_input_and_output_file(tmp_path):
    tensor = ElasticTensor(
        isotropic_cubic_matrix(),
        crystal_system="cubic",
        unit="GPa",
        material_name="sidecar-test",
    )
    exported_file = tmp_path / "plot.png"
    exported_file.write_bytes(b"fake image bytes")

    manifest_path = write_export_manifest(
        tensor,
        exported_file,
        export_type="figure",
        parameters={"dpi": 300},
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["program"] == "AnisoScope"
    assert manifest["material_name"] == "sidecar-test"
    assert manifest["export_type"] == "figure"
    assert manifest["exported_file"] == "plot.png"
    assert manifest["parameters"]["dpi"] == 300
