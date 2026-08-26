"""Batch paper-figure export services independent of the Qt GUI."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from crystal_elastic_workbench.atomic_publish import path_exists, publish_staged_files
from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.exporting import (
    sampled_data_manifest_parameters,
    write_export_manifest,
)
from crystal_elastic_workbench.plot_styles import DEFAULT_3D_PALETTE_NAME
from crystal_elastic_workbench.render3d import (
    PyVistaUnavailableError,
    Render3DOptions,
    render3d_manifest_style_parameters,
)
from crystal_elastic_workbench.sampling import (
    DirectionPath,
    DirectionalSurface,
    PlaneSlice,
)
from crystal_elastic_workbench.visualization import (
    plot_direction_path,
    plot_directional_surface,
    plot_line_slice,
    plot_plane_slice,
)


@dataclass(frozen=True)
class PaperFigureExportOptions:
    dpi: int = 300
    theme_name: str = "Nature White"
    palette_name: str = "Nature White"
    surface_palette_name: str = DEFAULT_3D_PALETTE_NAME
    transparent_background: bool = False
    lighting_intensity: float = 1.0
    surface_smoothing: float = 0.0
    surface_subdivision: int = 1
    show_edges: bool = False
    ambient: float = 0.28
    diffuse: float = 0.74
    specular: float = 0.32
    specular_power: float = 28.0
    render3d_options: Render3DOptions | None = None


def _surface_render_options(options: PaperFigureExportOptions) -> Render3DOptions:
    if options.render3d_options is not None:
        return options.render3d_options
    return Render3DOptions(
        theme_name=options.theme_name,
        palette_name=options.surface_palette_name,
        transparent_background=options.transparent_background,
        lighting_intensity=options.lighting_intensity,
        surface_smoothing=options.surface_smoothing,
        surface_subdivision=options.surface_subdivision,
        show_edges=options.show_edges,
        ambient=options.ambient,
        diffuse=options.diffuse,
        specular=options.specular,
        specular_power=options.specular_power,
    )


def _render_surface_png_isolated(
    surface: DirectionalSurface,
    output_path: Path,
    options: Render3DOptions,
) -> None:
    """Render with PyVista in a child process so VTK cannot poison Qt in this process."""

    with tempfile.TemporaryDirectory(prefix="cij_render3d_") as tmp:
        payload_path = Path(tmp) / "payload.pkl"
        with payload_path.open("wb") as handle:
            pickle.dump({"surface": surface, "options": options}, handle)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "crystal_elastic_workbench.render3d_worker",
                    str(payload_path),
                    str(output_path),
                ],
                cwd=str(Path.cwd()),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            timeout = f" after {exc.timeout} seconds" if exc.timeout is not None else ""
            raise PyVistaUnavailableError(
                f"PyVista worker timed out{timeout}."
            ) from exc
        except OSError as exc:
            reason = str(exc).strip() or exc.__class__.__name__
            raise PyVistaUnavailableError(
                f"PyVista worker could not be started: {reason}"
            ) from exc
    if completed.returncode != 0:
        message = (
            completed.stderr.strip()
            or completed.stdout.strip()
            or f"PyVista worker exited with code {completed.returncode}."
        )
        raise PyVistaUnavailableError(message)


def export_paper_figures(
    tensor: ElasticTensor,
    *,
    line_data: DirectionPath | PlaneSlice,
    polar_data: PlaneSlice,
    surface: DirectionalSurface,
    output_dir: str | Path,
    options: PaperFigureExportOptions | None = None,
) -> dict[str, Path]:
    """Export the default 1D, 2D, and 3D paper PNG set with sidecar manifests."""

    opts = options or PaperFigureExportOptions()
    out = Path(output_dir)
    if path_exists(out) and not out.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{out.name}-", dir=out.parent))
    staged_line_path = staging_dir / "paper_1d.png"
    staged_polar_path = staging_dir / "paper_2d_polar.png"
    staged_surface_path = staging_dir / "paper_3d_surface.png"
    render_options = _surface_render_options(opts)
    effective_surface_options = render_options
    try:
        if isinstance(line_data, DirectionPath):
            line_fig = plot_direction_path(
                line_data, theme_name=opts.theme_name, palette_name=opts.palette_name
            )
        else:
            line_fig = plot_line_slice(
                line_data, theme_name=opts.theme_name, palette_name=opts.palette_name
            )
        try:
            line_fig.savefig(
                staged_line_path, dpi=opts.dpi, transparent=opts.transparent_background
            )
        finally:
            plt.close(line_fig)
        write_export_manifest(
            tensor,
            staged_line_path,
            export_type="paper_figure_1d",
            parameters={
                "dpi": opts.dpi,
                "theme": opts.theme_name,
                "palette": opts.palette_name,
                "transparent_background": opts.transparent_background,
                **sampled_data_manifest_parameters(line_data),
            },
        )

        polar_fig = plot_plane_slice(
            polar_data, theme_name=opts.theme_name, palette_name=opts.palette_name
        )
        try:
            polar_fig.savefig(
                staged_polar_path, dpi=opts.dpi, transparent=opts.transparent_background
            )
        finally:
            plt.close(polar_fig)
        write_export_manifest(
            tensor,
            staged_polar_path,
            export_type="paper_figure_2d",
            parameters={
                "dpi": opts.dpi,
                "theme": opts.theme_name,
                "palette": opts.palette_name,
                "transparent_background": opts.transparent_background,
                **sampled_data_manifest_parameters(polar_data),
            },
        )

        backend = "pyvista"
        fallback_reason: str | None = None
        try:
            _render_surface_png_isolated(surface, staged_surface_path, render_options)
        except Exception as exc:
            backend = "matplotlib"
            fallback_reason = str(exc).strip() or exc.__class__.__name__
            effective_surface_options = replace(render_options, compose_annotations=True)
            surface_fig = plot_directional_surface(
                surface,
                theme_name=effective_surface_options.theme_name,
                palette_name=effective_surface_options.palette_name,
            )
            try:
                surface_fig.savefig(
                    staged_surface_path,
                    dpi=opts.dpi,
                    transparent=effective_surface_options.transparent_background,
                )
            finally:
                plt.close(surface_fig)
        write_export_manifest(
            tensor,
            staged_surface_path,
            export_type="paper_figure_3d",
            parameters={
                "backend": backend,
                **(
                    {"fallback_reason": fallback_reason}
                    if fallback_reason is not None
                    else {}
                ),
                "dpi": opts.dpi,
                "theme": effective_surface_options.theme_name,
                "transparent_background": effective_surface_options.transparent_background,
                **render3d_manifest_style_parameters(
                    render_options,
                    backend=backend,
                ),
                **sampled_data_manifest_parameters(surface),
            },
        )

        line_path = out / "paper_1d.png"
        polar_path = out / "paper_2d_polar.png"
        surface_path = out / "paper_3d_surface.png"
        publish_staged_files(
            [
                (staged_line_path, line_path),
                (
                    staged_line_path.with_name(
                        f"{staged_line_path.name}.manifest.json"
                    ),
                    line_path.with_name(f"{line_path.name}.manifest.json"),
                ),
                (staged_polar_path, polar_path),
                (
                    staged_polar_path.with_name(
                        f"{staged_polar_path.name}.manifest.json"
                    ),
                    polar_path.with_name(f"{polar_path.name}.manifest.json"),
                ),
                (staged_surface_path, surface_path),
                (
                    staged_surface_path.with_name(
                        f"{staged_surface_path.name}.manifest.json"
                    ),
                    surface_path.with_name(f"{surface_path.name}.manifest.json"),
                ),
            ],
        )
        return {
            "line_png": line_path,
            "polar_png": polar_path,
            "surface_png": surface_path,
        }
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
