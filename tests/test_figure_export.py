import json

import matplotlib

matplotlib.use("Agg")

from crystal_elastic_workbench import figure_export as figure_export_module
from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.examples import EXAMPLE_MATERIALS
from crystal_elastic_workbench.figure_export import SurfaceFigureExportOptions, export_surface_figure
from crystal_elastic_workbench.render3d import PyVistaUnavailableError, Render3DOptions
from crystal_elastic_workbench.sampling import sample_sphere


def test_surface_figure_export_falls_back_to_matplotlib_and_records_manifest(tmp_path, monkeypatch):
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)

    def fail_pyvista(*args, **kwargs):
        raise PyVistaUnavailableError("forced unavailable")

    seen = {}
    original_plot = figure_export_module.plot_directional_surface

    def capture_matplotlib_surface(surface_arg, **kwargs):
        seen["palette_name"] = kwargs.get("palette_name")
        seen["value_range"] = kwargs.get("value_range")
        seen["radius_mode"] = kwargs.get("radius_mode")
        seen["show_edges"] = kwargs.get("show_edges")
        return original_plot(surface_arg, **kwargs)

    monkeypatch.setattr("crystal_elastic_workbench.figure_export.render_surface_png", fail_pyvista)
    monkeypatch.setattr(
        "crystal_elastic_workbench.figure_export.plot_directional_surface",
        capture_matplotlib_surface,
    )

    result = export_surface_figure(
        tensor,
        surface,
        tmp_path / "surface.png",
        options=SurfaceFigureExportOptions(
            dpi=120,
            theme_name="Nature White",
            palette_name="Viridis Refined",
            transparent_background=False,
            render3d_options=Render3DOptions(
                window_size=(320, 260),
                theme_name="Gray Print",
                transparent_background=True,
                scalar_range=(100.0, 300.0),
                radius_mode="normalized",
                show_edges=True,
            ),
        ),
    )

    assert result.backend == "matplotlib"
    assert result.fallback_message == "forced unavailable"
    assert seen["palette_name"] == "Nature Surface"
    assert seen["value_range"] == (100.0, 300.0)
    assert seen["radius_mode"] == "normalized"
    assert seen["show_edges"] is True
    assert result.path.stat().st_size > 1000
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["export_type"] == "3d_figure"
    assert manifest["parameters"]["backend"] == "matplotlib"
    assert manifest["parameters"]["fallback_reason"] == "forced unavailable"
    assert manifest["parameters"]["dpi"] == 120
    assert manifest["parameters"]["transparent_background"] is True
    assert manifest["parameters"]["theme"] == "Gray Print"
    assert manifest["parameters"]["palette"] == "Nature Surface"
    assert manifest["parameters"]["palette_category"] == "sequential"
    assert manifest["parameters"]["compose_annotations"] is True
    assert manifest["parameters"]["annotation_backend"] == "matplotlib"
    assert "title_font_size" not in manifest["parameters"]
    assert "surface_subdivision" not in manifest["parameters"]
    assert "lighting_intensity" in manifest["parameters"]["ignored_render_options"]
    assert "scalar_range" not in manifest["parameters"]["ignored_render_options"]
    assert manifest["parameters"]["scalar_range"] == [100.0, 300.0]
    assert manifest["parameters"]["radius_mode"] == "normalized"
    requested = manifest["parameters"]["requested_render_style"]
    assert requested["title_font_size"] == 18
    assert requested["colorbar_tick_size"] == 10
    assert requested["surface_subdivision"] == 1
    assert requested["ambient"] == 0.28
    assert requested["diffuse"] == 0.74
    assert requested["specular"] == 0.32
    assert requested["specular_power"] == 28.0
    assert manifest["parameters"]["property"] == "young"
    assert manifest["parameters"]["theta_count"] == 5
    assert manifest["parameters"]["phi_count"] == 9
    assert "transverse_mode" not in manifest["parameters"]
    assert "transverse_samples" not in manifest["parameters"]
