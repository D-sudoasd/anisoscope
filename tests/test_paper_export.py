import json
import subprocess
from pathlib import Path

import pytest

from crystal_elastic_workbench import atomic_publish as atomic_publish_module
from crystal_elastic_workbench import paper_export as paper_export_module
from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.examples import EXAMPLE_MATERIALS
from crystal_elastic_workbench.paper_export import (
    PaperFigureExportOptions,
    _render_surface_png_isolated,
    export_paper_figures,
)
from crystal_elastic_workbench.render3d import PyVistaUnavailableError, Render3DOptions
from crystal_elastic_workbench.sampling import (
    sample_direction_path,
    sample_plane,
    sample_sphere,
)


def _paper_inputs():
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    line_data = sample_direction_path(
        tensor,
        property_name="young",
        points=[("[100]", [1, 0, 0]), ("[110]", [1, 1, 0])],
        points_per_segment=3,
    )
    polar_data = sample_plane(tensor, property_name="young", plane="xy", angle_count=13)
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)
    return tensor, line_data, polar_data, surface


def test_export_paper_figures_writes_traceable_png_set(tmp_path):
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    line_data = sample_direction_path(
        tensor,
        property_name="young",
        points=[
            ("[100]", [1, 0, 0]),
            ("[110]", [1, 1, 0]),
            ("[111]", [1, 1, 1]),
        ],
        points_per_segment=5,
    )
    polar_data = sample_plane(tensor, property_name="young", plane="xy", angle_count=37)
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)

    exported = export_paper_figures(
        tensor,
        line_data=line_data,
        polar_data=polar_data,
        surface=surface,
        output_dir=tmp_path,
        options=PaperFigureExportOptions(
            dpi=120,
            theme_name="Nature White",
            palette_name="Nature White",
            surface_palette_name="Viridis Refined",
            render3d_options=Render3DOptions(window_size=(360, 300)),
        ),
    )

    assert set(exported) == {"line_png", "polar_png", "surface_png"}
    for key, path in exported.items():
        assert isinstance(path, Path)
        assert path.exists()
        assert path.stat().st_size > 1000
        manifest = json.loads(
            path.with_name(f"{path.name}.manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["material_name"] == "Si cubic"
        assert manifest["parameters"]["dpi"] == 120
        assert manifest["parameters"]["theme"] == "Nature White"
        assert "transverse_mode" not in manifest["parameters"]
        assert "transverse_samples" not in manifest["parameters"]
        if key == "surface_png":
            assert manifest["parameters"]["theta_count"] == 5
            assert manifest["parameters"]["phi_count"] == 9
            assert manifest["parameters"]["backend"] in {"pyvista", "matplotlib"}
            assert manifest["parameters"]["palette"] == "Nature Surface"
            assert manifest["parameters"]["palette_category"] == "sequential"
            assert manifest["parameters"]["compose_annotations"] is True
            assert manifest["parameters"]["annotation_backend"] == "matplotlib"
            if manifest["parameters"]["backend"] == "pyvista":
                assert manifest["parameters"]["title_font_size"] == 18
                assert manifest["parameters"]["surface_subdivision"] == 1
                assert manifest["parameters"]["ignored_render_options"] == []
            else:
                assert "title_font_size" not in manifest["parameters"]
                assert "surface_subdivision" not in manifest["parameters"]
                assert "lighting_intensity" in manifest["parameters"]["ignored_render_options"]
            assert manifest["parameters"]["requested_render_style"]["ambient"] == 0.28
            assert manifest["parameters"]["requested_render_style"]["diffuse"] == 0.74
            assert manifest["parameters"]["requested_render_style"]["specular"] == 0.32
            assert manifest["parameters"]["requested_render_style"]["specular_power"] == 28.0


def test_paper_surface_fallback_uses_render_options_palette_instead_of_stale_option(
    tmp_path, monkeypatch
):
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    line_data = sample_direction_path(
        tensor,
        property_name="young",
        points=[("[100]", [1, 0, 0]), ("[110]", [1, 1, 0])],
        points_per_segment=3,
    )
    polar_data = sample_plane(tensor, property_name="young", plane="xy", angle_count=13)
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)
    seen = {}
    original_plot = paper_export_module.plot_directional_surface

    def fail_pyvista(*args, **kwargs):
        raise PyVistaUnavailableError("forced unavailable")

    def capture_matplotlib_surface(surface_arg, **kwargs):
        seen["palette_name"] = kwargs.get("palette_name")
        seen["theme_name"] = kwargs.get("theme_name")
        return original_plot(surface_arg, **kwargs)

    monkeypatch.setattr(
        "crystal_elastic_workbench.paper_export._render_surface_png_isolated",
        fail_pyvista,
    )
    monkeypatch.setattr(
        "crystal_elastic_workbench.paper_export.plot_directional_surface",
        capture_matplotlib_surface,
    )

    exported = export_paper_figures(
        tensor,
        line_data=line_data,
        polar_data=polar_data,
        surface=surface,
        output_dir=tmp_path,
        options=PaperFigureExportOptions(
            surface_palette_name="Viridis Refined",
            render3d_options=Render3DOptions(
                window_size=(360, 300),
                theme_name="Gray Print",
                palette_name="Blue-Gold",
                compose_annotations=False,
            ),
        ),
    )

    assert seen["palette_name"] == "Blue-Gold"
    assert seen["theme_name"] == "Gray Print"
    manifest = json.loads(
        exported["surface_png"]
        .with_name(f"{exported['surface_png'].name}.manifest.json")
        .read_text(encoding="utf-8")
    )
    assert manifest["parameters"]["backend"] == "matplotlib"
    assert manifest["parameters"]["fallback_reason"] == "forced unavailable"
    assert manifest["parameters"]["theme"] == "Gray Print"
    assert manifest["parameters"]["palette"] == "Blue-Gold"
    assert manifest["parameters"]["compose_annotations"] is True
    assert manifest["parameters"]["annotation_backend"] == "matplotlib"
    assert "lighting_intensity" not in manifest["parameters"]
    assert "lighting_intensity" in manifest["parameters"]["ignored_render_options"]
    assert manifest["parameters"]["requested_render_style"]["compose_annotations"] is False


@pytest.mark.parametrize(
    ("worker_failure", "message"),
    [
        (subprocess.TimeoutExpired(["python", "worker"], timeout=120), "timed out"),
        (OSError("worker executable unavailable"), "worker executable unavailable"),
        (
            subprocess.CompletedProcess(
                ["python", "worker"],
                returncode=17,
                stdout="",
                stderr="worker crashed",
            ),
            "worker crashed",
        ),
    ],
)
def test_isolated_surface_worker_failures_become_pyvista_unavailable_error(
    tmp_path, monkeypatch, worker_failure, message
):
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)

    def fail_worker(*args, **kwargs):
        if isinstance(worker_failure, BaseException):
            raise worker_failure
        return worker_failure

    monkeypatch.setattr(paper_export_module.subprocess, "run", fail_worker)

    with pytest.raises(PyVistaUnavailableError, match=message):
        _render_surface_png_isolated(
            surface, tmp_path / "surface.png", Render3DOptions(window_size=(320, 260))
        )


@pytest.mark.parametrize(
    "worker_failure",
    [
        subprocess.TimeoutExpired(["python", "worker"], timeout=120),
        OSError("worker executable unavailable"),
        subprocess.CompletedProcess(
            ["python", "worker"],
            returncode=17,
            stdout="",
            stderr="worker crashed",
        ),
    ],
)
def test_paper_surface_worker_failures_complete_matplotlib_fallback_and_manifest(
    tmp_path, monkeypatch, worker_failure
):
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    line_data = sample_direction_path(
        tensor,
        property_name="young",
        points=[("[100]", [1, 0, 0]), ("[110]", [1, 1, 0])],
        points_per_segment=3,
    )
    polar_data = sample_plane(tensor, property_name="young", plane="xy", angle_count=13)
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)

    def fail_worker(*args, **kwargs):
        if isinstance(worker_failure, BaseException):
            raise worker_failure
        return worker_failure

    monkeypatch.setattr(paper_export_module.subprocess, "run", fail_worker)
    exported = export_paper_figures(
        tensor,
        line_data=line_data,
        polar_data=polar_data,
        surface=surface,
        output_dir=tmp_path,
        options=PaperFigureExportOptions(dpi=120),
    )

    assert set(exported) == {"line_png", "polar_png", "surface_png"}
    assert all(
        path.exists() and path.stat().st_size > 1000 for path in exported.values()
    )
    manifest_path = exported["surface_png"].with_name(
        f"{exported['surface_png'].name}.manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["parameters"]["backend"] == "matplotlib"
    assert manifest["parameters"]["fallback_reason"]


def test_paper_manifest_failure_preserves_complete_existing_set_and_unrelated_file(
    tmp_path, monkeypatch
):
    tensor, line_data, polar_data, surface = _paper_inputs()
    output_dir = tmp_path / "figures"
    output_dir.mkdir()
    owned_names = (
        "paper_1d.png",
        "paper_1d.png.manifest.json",
        "paper_2d_polar.png",
        "paper_2d_polar.png.manifest.json",
        "paper_3d_surface.png",
        "paper_3d_surface.png.manifest.json",
    )
    old_bytes = {}
    for name in owned_names:
        path = output_dir / name
        old_bytes[name] = f"old:{name}".encode()
        path.write_bytes(old_bytes[name])
    unrelated = output_dir / "keep.txt"
    unrelated.write_bytes(b"keep me")
    real_manifest = paper_export_module.write_export_manifest

    def fail_surface_manifest(tensor_arg, staged_output, **kwargs):
        if Path(staged_output).name == "paper_3d_surface.png":
            Path(staged_output).with_name(
                f"{Path(staged_output).name}.manifest.json"
            ).write_bytes(b"partial")
            raise RuntimeError("paper manifest injection")
        return real_manifest(tensor_arg, staged_output, **kwargs)

    monkeypatch.setattr(
        paper_export_module, "write_export_manifest", fail_surface_manifest
    )
    monkeypatch.setattr(
        paper_export_module,
        "_render_surface_png_isolated",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PyVistaUnavailableError("forced fallback")
        ),
    )

    with pytest.raises(RuntimeError, match="paper manifest injection"):
        export_paper_figures(
            tensor,
            line_data=line_data,
            polar_data=polar_data,
            surface=surface,
            output_dir=output_dir,
            options=PaperFigureExportOptions(dpi=100),
        )

    assert {name: (output_dir / name).read_bytes() for name in owned_names} == old_bytes
    assert unrelated.read_bytes() == b"keep me"
    assert not list(tmp_path.glob(f".{output_dir.name}-*"))


def test_paper_publish_failure_rolls_back_complete_set_and_preserves_unrelated_file(
    tmp_path, monkeypatch
):
    tensor, line_data, polar_data, surface = _paper_inputs()
    output_dir = tmp_path / "figures"
    output_dir.mkdir()
    owned_names = (
        "paper_1d.png",
        "paper_1d.png.manifest.json",
        "paper_2d_polar.png",
        "paper_2d_polar.png.manifest.json",
        "paper_3d_surface.png",
        "paper_3d_surface.png.manifest.json",
    )
    old_bytes = {}
    for name in owned_names:
        path = output_dir / name
        old_bytes[name] = f"old:{name}".encode()
        path.write_bytes(old_bytes[name])
    unrelated = output_dir / "keep.txt"
    unrelated.write_bytes(b"keep me")
    real_replace = atomic_publish_module.os.replace
    failing_name = "paper_3d_surface.png.manifest.json"

    def fail_surface_manifest_install(source, destination):
        if (
            Path(destination).parent == output_dir
            and Path(destination).name == failing_name
        ):
            raise OSError("paper commit injection")
        return real_replace(source, destination)

    monkeypatch.setattr(
        atomic_publish_module.os, "replace", fail_surface_manifest_install
    )
    monkeypatch.setattr(
        paper_export_module,
        "_render_surface_png_isolated",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PyVistaUnavailableError("forced fallback")
        ),
    )

    with pytest.raises(OSError, match="paper commit injection"):
        export_paper_figures(
            tensor,
            line_data=line_data,
            polar_data=polar_data,
            surface=surface,
            output_dir=output_dir,
            options=PaperFigureExportOptions(dpi=100),
        )

    assert {name: (output_dir / name).read_bytes() for name in owned_names} == old_bytes
    assert unrelated.read_bytes() == b"keep me"
    assert not list(tmp_path.glob(f".{output_dir.name}-*"))


def test_paper_export_refuses_to_replace_an_owned_directory_path(tmp_path, monkeypatch):
    tensor, line_data, polar_data, surface = _paper_inputs()
    output_dir = tmp_path / "figures"
    protected = output_dir / "paper_1d.png"
    protected.mkdir(parents=True)
    marker = protected / "keep.txt"
    marker.write_bytes(b"keep")
    monkeypatch.setattr(
        paper_export_module,
        "_render_surface_png_isolated",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PyVistaUnavailableError("forced fallback")
        ),
    )

    with pytest.raises(IsADirectoryError, match="Refusing to replace"):
        export_paper_figures(
            tensor,
            line_data=line_data,
            polar_data=polar_data,
            surface=surface,
            output_dir=output_dir,
            options=PaperFigureExportOptions(dpi=100),
        )

    assert marker.read_bytes() == b"keep"
    assert not list(tmp_path.glob(f".{output_dir.name}-*"))
