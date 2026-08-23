import numpy as np
import pytest

from crystal_elastic_workbench.plot_styles import (
    DEFAULT_3D_PALETTE_NAME,
    DEFAULT_PALETTE_NAME,
    DEFAULT_THEME_NAME,
    get_palette,
    list_3d_palette_names,
    get_theme,
    list_palette_names,
    surface_color_limits,
)


EXPECTED_PALETTES = {
    "Nature White",
    "Nature Muted",
    "Science High Contrast",
    "Okabe-Ito",
    "Tol Bright",
    "Cividis",
    "Viridis Refined",
    "Gray Print",
}

EXPECTED_3D_PALETTES = {
    "Nature Surface",
    "Nature Thermal",
    "Blue-Gold",
    "Teal-Amber",
    "Deep Ocean",
    "Blue-White-Red",
    "Purple-Green",
    "Brown-Blue",
    "Graphite",
}


def test_expected_scientific_palettes_are_registered():
    names = set(list_palette_names())

    assert EXPECTED_PALETTES.union(EXPECTED_3D_PALETTES).issubset(names)
    assert DEFAULT_PALETTE_NAME == "Nature White"
    assert DEFAULT_3D_PALETTE_NAME == "Nature Surface"
    for name in EXPECTED_PALETTES.union(EXPECTED_3D_PALETTES):
        palette = get_palette(name)
        assert palette.name == name
        assert len(palette.colors) >= 5
        assert all(color.startswith("#") and len(color) == 7 for color in palette.colors)
    assert list_3d_palette_names()[: len(EXPECTED_3D_PALETTES)] == [
        "Nature Surface",
        "Nature Thermal",
        "Blue-Gold",
        "Teal-Amber",
        "Deep Ocean",
        "Blue-White-Red",
        "Purple-Green",
        "Brown-Blue",
        "Graphite",
    ]
    assert get_palette("Nature Surface").category == "sequential"
    assert get_palette("Blue-White-Red").category == "diverging"
    assert get_palette("Graphite").category == "print_safe"


def test_default_nature_white_theme_uses_publication_defaults():
    theme = get_theme()

    assert theme.name == DEFAULT_THEME_NAME == "Nature White"
    assert theme.figure_dpi == 150
    assert theme.export_dpi == 300
    assert theme.line_width <= 1.5
    assert 0.0 < theme.grid_alpha <= 0.25
    assert theme.axes_facecolor == "#ffffff"
    assert theme.figure_facecolor == "#ffffff"
    assert theme.font_size <= 9


def test_unknown_theme_and_palette_raise_clear_errors():
    with pytest.raises(ValueError, match="Unknown plotting theme"):
        get_theme("not-a-theme")

    with pytest.raises(ValueError, match="Unknown palette"):
        get_palette("not-a-palette")


def test_surface_color_limits_center_diverging_zero_only_when_needed():
    assert surface_color_limits((-2.0, -0.5, 1.0), "Blue-White-Red") == pytest.approx((-2.0, 2.0))
    assert surface_color_limits((-2.0, -0.5, 1.0), "Nature Surface") == pytest.approx((-2.0, 1.0))
    assert surface_color_limits((1.0, 2.0, 3.0), "Blue-White-Red") == pytest.approx((1.0, 3.0))
    assert surface_color_limits((-3.0, -1.0, 0.0), "Blue-White-Red") == pytest.approx((-3.0, 0.0))
    assert surface_color_limits((value for value in (-2.0, 0.5)), "Blue-White-Red") == pytest.approx((-2.0, 2.0))


def test_surface_color_limits_reject_values_without_finite_samples():
    with pytest.raises(ValueError, match="finite"):
        surface_color_limits((np.nan, np.inf), "Nature Surface")
