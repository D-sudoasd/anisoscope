"""Rotating 3D animation export services with standard manifests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import shutil
import tempfile

from crystal_elastic_workbench.atomic_publish import publish_staged_files
from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.exporting import (
    sampled_data_manifest_parameters,
    write_export_manifest,
)
from crystal_elastic_workbench.plot_styles import DEFAULT_3D_PALETTE_NAME, get_palette
from crystal_elastic_workbench.render3d import MATPLOTLIB_HONORED_RENDER_KEYS
from crystal_elastic_workbench.sampling import DirectionalSurface
from crystal_elastic_workbench.visualization import (
    export_rotating_gif,
    export_rotating_mp4,
)


@dataclass(frozen=True)
class AnimationExportOptions:
    frames: int = 72
    dpi: int = 120
    theme_name: str = "Nature White"
    palette_name: str = DEFAULT_3D_PALETTE_NAME
    axis: str = "z"
    transparent_background: bool = False
    lighting_intensity: float = 1.0
    surface_smoothing: float = 0.0
    surface_subdivision: int = 1
    show_edges: bool = False
    scalar_range: tuple[float, float] | None = None
    edge_color: str = "#404040"
    edge_line_width: float = 0.4
    radius_mode: Literal["physical", "normalized"] = "physical"
    radius_scale: float = 1.0
    title_font_size: int = 18
    label_font_size: int = 12
    colorbar_title_size: int = 12
    colorbar_tick_size: int = 10
    ambient: float = 0.28
    diffuse: float = 0.74
    specular: float = 0.32
    specular_power: float = 28.0
    fps: int | None = None


def _render_style_parameters(
    options: AnimationExportOptions,
    *,
    backend: str = "pyvista",
    fallback_reason: str | None = None,
) -> dict[str, object]:
    palette = get_palette(options.palette_name)
    requested: dict[str, object] = {
        "compose_annotations": False,
        "annotation_backend": "pyvista",
        "title_font_size": options.title_font_size,
        "label_font_size": options.label_font_size,
        "colorbar_title_size": options.colorbar_title_size,
        "colorbar_tick_size": options.colorbar_tick_size,
        "lighting_intensity": options.lighting_intensity,
        "surface_smoothing": options.surface_smoothing,
        "surface_subdivision": options.surface_subdivision,
        "scalar_range": options.scalar_range,
        "show_edges": options.show_edges,
        "edge_color": options.edge_color,
        "edge_line_width": options.edge_line_width,
        "radius_mode": options.radius_mode,
        "radius_scale": options.radius_scale,
        "ambient": options.ambient,
        "diffuse": options.diffuse,
        "specular": options.specular,
        "specular_power": options.specular_power,
    }
    parameters: dict[str, object] = {
        "palette_category": palette.category,
        "backend": backend,
        "requested_render_style": requested,
    }
    if backend == "pyvista":
        parameters.update(requested)
        parameters["ignored_render_options"] = []
    else:
        ignored = [key for key in requested if key not in MATPLOTLIB_HONORED_RENDER_KEYS]
        effective = {
            key: requested[key]
            for key in requested
            if key in MATPLOTLIB_HONORED_RENDER_KEYS
        }
        parameters.update(
            {
                "compose_annotations": True,
                "annotation_backend": "matplotlib",
                **effective,
                "ignored_render_options": ignored,
            }
        )
    if fallback_reason is not None:
        parameters["fallback_reason"] = fallback_reason
    return parameters


def _gif_manifest_parameters(
    surface: DirectionalSurface,
    options: AnimationExportOptions,
    *,
    fps: int,
    backend: str = "pyvista",
    fallback_reason: str | None = None,
) -> dict[str, object]:
    return {
        "frames": options.frames,
        "fps": fps,
        "dpi": options.dpi,
        "theme": options.theme_name,
        "palette": options.palette_name,
        "axis": options.axis,
        **sampled_data_manifest_parameters(surface),
        "transparent_background": options.transparent_background,
        **_render_style_parameters(
            options, backend=backend, fallback_reason=fallback_reason
        ),
    }


def _mp4_manifest_parameters(
    surface: DirectionalSurface,
    options: AnimationExportOptions,
    *,
    fps: int,
    backend: str = "pyvista",
    fallback_reason: str | None = None,
) -> dict[str, object]:
    return {
        "frames": options.frames,
        "fps": fps,
        "dpi": options.dpi,
        "theme": options.theme_name,
        "palette": options.palette_name,
        "axis": options.axis,
        "transparent_background": options.transparent_background,
        **sampled_data_manifest_parameters(surface),
        **_render_style_parameters(
            options, backend=backend, fallback_reason=fallback_reason
        ),
    }


def _render_kwargs(options: AnimationExportOptions, *, fps: int) -> dict[str, object]:
    return {
        "frames": options.frames,
        "fps": fps,
        "dpi": options.dpi,
        "theme_name": options.theme_name,
        "palette_name": options.palette_name,
        "axis": options.axis,
        "transparent_background": options.transparent_background,
        "lighting_intensity": options.lighting_intensity,
        "surface_smoothing": options.surface_smoothing,
        "surface_subdivision": options.surface_subdivision,
        "show_edges": options.show_edges,
        "edge_color": options.edge_color,
        "edge_line_width": options.edge_line_width,
        "value_range": options.scalar_range,
        "radius_mode": options.radius_mode,
        "radius_scale": options.radius_scale,
        "title_font_size": options.title_font_size,
        "label_font_size": options.label_font_size,
        "colorbar_title_size": options.colorbar_title_size,
        "colorbar_tick_size": options.colorbar_tick_size,
        "ambient": options.ambient,
        "diffuse": options.diffuse,
        "specular": options.specular,
        "specular_power": options.specular_power,
    }


def _export_with_backend_fallback(
    exporter: Callable[..., Path],
    surface: DirectionalSurface,
    output: Path,
    options: AnimationExportOptions,
    *,
    fps: int,
    force_matplotlib_reason: str | None = None,
) -> tuple[str, str | None]:
    render_kwargs = _render_kwargs(options, fps=fps)
    if force_matplotlib_reason is not None:
        exporter(surface, output, backend="matplotlib", **render_kwargs)
        return "matplotlib", force_matplotlib_reason
    try:
        exporter(surface, output, backend="pyvista", **render_kwargs)
    except Exception as exc:
        fallback_reason = str(exc).strip() or exc.__class__.__name__
        exporter(surface, output, backend="matplotlib", **render_kwargs)
        return "matplotlib", fallback_reason
    return "pyvista", None


def export_surface_gif_animation(
    tensor: ElasticTensor,
    surface: DirectionalSurface,
    output_path: str | Path,
    *,
    options: AnimationExportOptions | None = None,
) -> Path:
    opts = options or AnimationExportOptions()
    fps = 12 if opts.fps is None else opts.fps
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    staged_output = staging_dir / output.name
    try:
        backend, fallback_reason = _export_with_backend_fallback(
            export_rotating_gif,
            surface,
            staged_output,
            opts,
            fps=fps,
            force_matplotlib_reason=(
                "transparent_background requires Matplotlib GIF export"
                if opts.transparent_background
                else None
            ),
        )
        staged_manifest = write_export_manifest(
            tensor,
            staged_output,
            export_type="gif",
            parameters=_gif_manifest_parameters(
                surface,
                opts,
                fps=fps,
                backend=backend,
                fallback_reason=fallback_reason,
            ),
        )
        publish_staged_files(
            (
                (staged_output, output),
                (staged_manifest, output.with_name(f"{output.name}.manifest.json")),
            )
        )
        return output
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


def export_surface_mp4_animation(
    tensor: ElasticTensor,
    surface: DirectionalSurface,
    output_path: str | Path,
    *,
    options: AnimationExportOptions | None = None,
) -> Path:
    opts = options or AnimationExportOptions()
    if opts.transparent_background:
        raise ValueError(
            "MP4 export does not support transparent backgrounds; use GIF or PNG instead."
        )
    output = Path(output_path)
    fps = 24 if opts.fps is None else opts.fps
    output.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    staged_output = staging_dir / output.name
    try:
        backend, fallback_reason = _export_with_backend_fallback(
            export_rotating_mp4,
            surface,
            staged_output,
            opts,
            fps=fps,
        )
        staged_manifest = write_export_manifest(
            tensor,
            staged_output,
            export_type="mp4",
            parameters=_mp4_manifest_parameters(
                surface,
                opts,
                fps=fps,
                backend=backend,
                fallback_reason=fallback_reason,
            ),
        )
        publish_staged_files(
            (
                (staged_output, output),
                (staged_manifest, output.with_name(f"{output.name}.manifest.json")),
            )
        )
        return output
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
