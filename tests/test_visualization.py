from dataclasses import replace

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.sampling import DirectionalSurface, sample_plane, sample_sphere
from crystal_elastic_workbench.visualization import (
    export_rotating_gif,
    export_rotating_mp4,
    plot_direction_path,
    plot_directional_surface,
    plot_line_slice,
    plot_plane_slice,
    property_label,
)


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
    x = np.array([[0.0, 1.0], [0.0, 1.0]])
    y = np.array([[0.0, 0.0], [1.0, 1.0]])
    z = values.copy()
    return DirectionalSurface(
        property_name="poisson",
        theta=np.zeros((2, 2)),
        phi=np.zeros((2, 2)),
        directions=directions,
        values=values,
        x=x,
        y=y,
        z=z,
        min_value=-2.0,
        max_value=1.0,
        min_direction=np.array([1.0, 0.0, 0.0]),
        max_direction=np.array([1.0, 0.0, 0.0]),
    )


def test_plot_exports_static_png_files(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    plane = sample_plane(tensor, property_name="young", plane="xy", angle_count=37)
    surface = sample_sphere(tensor, property_name="young", theta_count=7, phi_count=13)

    plane_fig = plot_plane_slice(plane)
    surface_fig = plot_directional_surface(surface)

    plane_path = tmp_path / "plane.png"
    surface_path = tmp_path / "surface.png"
    plane_fig.savefig(plane_path, dpi=120)
    surface_fig.savefig(surface_path, dpi=120)

    assert plane_path.stat().st_size > 1000
    assert surface_path.stat().st_size > 1000


def test_direction_path_uses_compact_publication_styling():
    from crystal_elastic_workbench.sampling import sample_direction_path

    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    path = sample_direction_path(
        tensor,
        property_name="young",
        points=[
            ("[100]", [1, 0, 0]),
            ("[110]", [1, 1, 0]),
            ("[111]", [1, 1, 1]),
        ],
        points_per_segment=5,
    )

    fig = plot_direction_path(path, theme_name="Nature White", palette_name="Okabe-Ito")
    ax = fig.axes[0]

    assert ax.get_title()
    assert ax.get_xlabel() == "Direction path"
    assert [label.get_text() for label in ax.get_xticklabels()] == ["[100]", "[110]", "[111]"]
    assert fig.dpi == 150
    assert ax.lines[0].get_linewidth() <= 1.5


def test_diverging_surface_colorbar_centers_zero():
    fig = plot_directional_surface(signed_surface(), palette_name="Blue-White-Red")

    assert fig.axes[-1].get_ylim() == pytest.approx((-2.0, 2.0))
    assert {item.get_text() for item in fig.axes[0].get_legend().get_texts()} == {
        "Sampled-grid min",
        "Sampled-grid max",
    }
    assert any("Sampled-grid extrema" in text.get_text() for text in fig.texts)


def test_explicit_colormap_controls_signed_surface_normalization():
    diverging = plot_directional_surface(
        signed_surface(),
        palette_name="Nature Surface",
        cmap="seismic",
    )
    sequential = plot_directional_surface(
        signed_surface(),
        palette_name="Blue-White-Red",
        cmap="viridis",
    )

    assert diverging.axes[-1].get_ylim() == pytest.approx((-2.0, 2.0))
    assert sequential.axes[-1].get_ylim() == pytest.approx((-2.0, 1.0))


@pytest.mark.parametrize(
    ("property_name", "transverse_mode", "expected"),
    [
        ("shear", "min", "transverse min [GPa]"),
        ("poisson", "max", "transverse max"),
    ],
)
def test_property_labels_follow_selected_transverse_aggregation(
    property_name,
    transverse_mode,
    expected,
):
    assert expected in property_label(property_name, transverse_mode)


def test_matplotlib_figures_use_data_transverse_aggregation_in_labels():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    plane = sample_plane(
        tensor,
        property_name="shear",
        plane="xy",
        angle_count=9,
        transverse_mode="min",
    )
    surface = replace(signed_surface(), transverse_mode="max")

    assert "transverse min" in plot_line_slice(plane).axes[0].get_ylabel()
    assert "transverse min" in plot_line_slice(plane).axes[0].get_title()
    assert "transverse min" in plot_plane_slice(plane).axes[0].get_title()
    surface_figure = plot_directional_surface(surface)
    assert "transverse max" in surface_figure.axes[-1].get_ylabel()
    assert "transverse max" in surface_figure.axes[0].get_title()


def test_plane_slice_title_includes_property_units():
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    plane = sample_plane(tensor, property_name="young", plane="xy", angle_count=9)

    ax = plot_plane_slice(plane).axes[0]

    assert "[GPa]" in ax.get_title()


def test_export_rotating_gif_writes_animation(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=7, phi_count=13)
    gif_path = tmp_path / "rotation.gif"

    export_rotating_gif(surface, gif_path, frames=5, dpi=80)

    assert gif_path.stat().st_size > 1000


def test_export_rotating_mp4_prefers_pyvista_backend(tmp_path, monkeypatch):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=7, phi_count=13)
    seen = {}

    def fake_render(surface_arg, output_path, **kwargs):
        seen["surface"] = surface_arg
        seen["kwargs"] = kwargs
        output_path.write_bytes(b"mp4 bytes")
        return output_path

    monkeypatch.setattr("crystal_elastic_workbench.visualization.render_surface_mp4", fake_render)
    mp4_path = tmp_path / "rotation.mp4"

    export_rotating_mp4(surface, mp4_path, frames=7, dpi=80, surface_subdivision=2, specular=0.4)

    assert seen["surface"] is surface
    assert seen["kwargs"]["frames"] == 7
    assert seen["kwargs"]["options"].surface_subdivision == 2
    assert seen["kwargs"]["options"].specular == 0.4
    assert mp4_path.read_bytes() == b"mp4 bytes"


def test_animation_rotation_parameters_fail_closed(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=3, phi_count=5)

    with pytest.raises(ValueError, match="fps"):
        export_rotating_gif(surface, tmp_path / "bad-fps.gif", backend="matplotlib", frames=2, fps=0)

    with pytest.raises(ValueError, match="axis"):
        export_rotating_gif(
            surface,
            tmp_path / "bad-axis.gif",
            backend="matplotlib",
            frames=2,
            fps=1,
            axis="bad",
        )


def test_transparent_gif_skips_pyvista_and_uses_matplotlib(tmp_path, monkeypatch):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=3, phi_count=5)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("PyVista GIF path should be skipped for transparent backgrounds")

    monkeypatch.setattr("crystal_elastic_workbench.visualization.render_surface_gif", fail_if_called)
    gif_path = tmp_path / "transparent.gif"

    export_rotating_gif(
        surface,
        gif_path,
        backend="auto",
        frames=2,
        fps=1,
        dpi=40,
        transparent_background=True,
    )

    assert gif_path.exists()
    assert gif_path.stat().st_size > 0


def test_transparent_gif_rejects_explicit_pyvista_backend(tmp_path):
    tensor = ElasticTensor(isotropic_cubic_matrix(), crystal_system="cubic")
    surface = sample_sphere(tensor, property_name="young", theta_count=3, phi_count=5)

    with pytest.raises(ValueError, match="transparent"):
        export_rotating_gif(
            surface,
            tmp_path / "pyvista-transparent.gif",
            backend="pyvista",
            frames=2,
            fps=1,
            transparent_background=True,
        )
