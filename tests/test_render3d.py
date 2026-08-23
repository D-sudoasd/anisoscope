from dataclasses import replace

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from crystal_elastic_workbench.core import ElasticTensor
import crystal_elastic_workbench.render3d as render3d_module
from crystal_elastic_workbench.render3d import (
    PyVistaUnavailableError,
    Render3DOptions,
    pyvista_status,
    render_surface_image,
    render_surface_png,
)
from crystal_elastic_workbench.sampling import DirectionalSurface, sample_sphere


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


def signed_surface() -> DirectionalSurface:
    values = np.array([[-2.0, 1.0], [-1.0, 0.5]])
    directions = np.zeros((2, 2, 3), dtype=float)
    directions[..., 0] = 1.0
    return DirectionalSurface(
        property_name="poisson",
        theta=np.zeros((2, 2)),
        phi=np.zeros((2, 2)),
        directions=directions,
        values=values,
        x=np.array([[0.0, 1.0], [0.0, 1.0]]),
        y=np.array([[0.0, 0.0], [1.0, 1.0]]),
        z=values.copy(),
        min_value=-2.0,
        max_value=1.0,
        min_direction=np.array([1.0, 0.0, 0.0]),
        max_direction=np.array([1.0, 0.0, 0.0]),
    )


def test_render3d_defaults_match_high_quality_white_backend():
    options = Render3DOptions()

    assert options.theme_name == "Nature White"
    assert options.palette_name == "Nature Surface"
    assert options.window_size == (2400, 2000)
    assert options.parallel_projection is True
    assert options.smooth_shading is True
    assert options.transparent_background is False
    assert options.compose_annotations is True
    assert options.title_font_size == 18
    assert options.label_font_size == 12
    assert options.colorbar_title_size == 12
    assert options.colorbar_tick_size == 10
    assert options.lighting_intensity == pytest.approx(1.0)
    assert options.surface_subdivision == 1
    assert options.ambient == pytest.approx(0.28)
    assert options.diffuse == pytest.approx(0.74)
    assert options.specular == pytest.approx(0.32)
    assert options.specular_power == pytest.approx(28.0)


def test_render3d_style_parameters_include_palette_and_annotation_metadata():
    from crystal_elastic_workbench.render3d import render3d_style_parameters

    parameters = render3d_style_parameters(Render3DOptions())

    assert parameters["palette"] == "Nature Surface"
    assert parameters["palette_category"] == "sequential"
    assert parameters["compose_annotations"] is True
    assert parameters["annotation_backend"] == "matplotlib"
    assert parameters["title_font_size"] == 18
    assert parameters["label_font_size"] == 12
    assert parameters["colorbar_title_size"] == 12
    assert parameters["colorbar_tick_size"] == 10


def test_matplotlib_manifest_separates_requested_from_effective_3d_style():
    from crystal_elastic_workbench.render3d import render3d_manifest_style_parameters

    parameters = render3d_manifest_style_parameters(
        Render3DOptions(compose_annotations=False, surface_subdivision=2),
        backend="matplotlib",
    )

    assert parameters["compose_annotations"] is True
    assert parameters["annotation_backend"] == "matplotlib"
    assert "surface_subdivision" not in parameters
    assert parameters["requested_render_style"]["surface_subdivision"] == 2
    assert parameters["requested_render_style"]["compose_annotations"] is False
    assert "surface_subdivision" in parameters["ignored_render_options"]


def test_pyvista_clim_and_composite_colorbar_share_centered_diverging_limits(monkeypatch):
    seen = {}

    class FakeCamera:
        parallel_projection = False

    class FakePlotter:
        def __init__(self, **_kwargs):
            self.camera = FakeCamera()

        def set_background(self, _color):
            pass

        def enable_anti_aliasing(self, _mode):
            pass

        def enable_parallel_projection(self):
            pass

        def add_mesh(self, _mesh, **kwargs):
            seen["mesh_kwargs"] = kwargs

        def add_points(self, *_args, **_kwargs):
            pass

        def add_text(self, *_args, **_kwargs):
            pass

        def add_axes(self, *_args, **_kwargs):
            pass

        def add_legend(self, *_args, **_kwargs):
            pass

        def reset_camera(self):
            pass

    class FakePyVista:
        Plotter = FakePlotter

    surface = signed_surface()
    monkeypatch.setattr(render3d_module, "_import_pyvista", lambda: FakePyVista)
    monkeypatch.setattr(render3d_module, "_surface_mesh", lambda *_args: object())
    monkeypatch.setattr(render3d_module, "_add_three_point_lighting", lambda *_args: None)

    options = Render3DOptions(palette_name="Blue-White-Red", compose_annotations=False)
    render3d_module._build_plotter(surface, options)
    normalizer = render3d_module._normalizer(surface, options.palette_name)

    assert seen["mesh_kwargs"]["clim"] == pytest.approx((-2.0, 2.0))
    assert (normalizer.vmin, normalizer.vmax) == pytest.approx((-2.0, 2.0))


@pytest.mark.parametrize(
    ("property_name", "expected"),
    [
        ("shear", "transverse mean [GPa]"),
        ("poisson", "transverse mean"),
    ],
)
def test_3d_scalar_bar_labels_name_transverse_aggregation(property_name, expected):
    surface = replace(signed_surface(), property_name=property_name, transverse_mode="mean")

    assert expected in render3d_module._surface_property_label(surface)


def test_3d_titles_name_selected_transverse_aggregation():
    surface = replace(signed_surface(), property_name="shear", transverse_mode="max")

    assert "transverse max" in render3d_module._surface_property_title(surface)


def test_pyvista_backend_can_be_disabled_for_unsupported_headless_hosts(monkeypatch):
    monkeypatch.setenv("ANISOSCOPE_DISABLE_PYVISTA", "1")
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)

    status = pyvista_status()

    assert status.available is False
    assert "ANISOSCOPE_DISABLE_PYVISTA" in status.message
    assert "unset it or set it to 0" in status.message
    with pytest.raises(PyVistaUnavailableError, match="unset it or set it to 0"):
        render_surface_image(surface, options=Render3DOptions(window_size=(320, 260)))


def test_render_surface_image_returns_nonblank_preview_or_clear_unavailable_message():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)
    status = pyvista_status()

    if not status.available:
        with pytest.raises(PyVistaUnavailableError, match="PyVista/VTK"):
            render_surface_image(surface, options=Render3DOptions(window_size=(320, 260)))
        return

    image = render_surface_image(surface, options=Render3DOptions(window_size=(320, 260)))

    assert image.ndim == 3
    assert image.shape[0] == 260
    assert image.shape[1] == 320
    assert image.shape[2] in {3, 4}
    assert float(np.std(image)) > 0.0


def test_pyvista_png_render_or_clear_unavailable_message(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)
    output = tmp_path / "surface.png"
    status = pyvista_status()

    if not status.available:
        with pytest.raises(PyVistaUnavailableError, match="PyVista/VTK"):
            render_surface_png(surface, output, options=Render3DOptions(window_size=(320, 260)))
        assert not output.exists()
        return

    render_surface_png(surface, output, options=Render3DOptions(window_size=(320, 260)))

    assert output.stat().st_size > 1000
