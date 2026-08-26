import json
import os
from pathlib import Path

import pytest

from crystal_elastic_workbench import animation_export as animation_export_module
from crystal_elastic_workbench import atomic_publish as atomic_publish_module
from crystal_elastic_workbench.animation_export import (
    AnimationExportOptions,
    export_surface_gif_animation,
    export_surface_mp4_animation,
)
from crystal_elastic_workbench.core import ElasticTensor
from crystal_elastic_workbench.examples import EXAMPLE_MATERIALS
from crystal_elastic_workbench.render3d import PyVistaUnavailableError
from crystal_elastic_workbench.sampling import sample_sphere


def _si_tensor_and_surface():
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    return tensor, sample_sphere(
        tensor, property_name="young", theta_count=5, phi_count=9
    )


def test_gif_animation_export_writes_manifest_and_forwards_scientific_style_options(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    seen = {}

    def fake_export(surface_arg, output_path, **kwargs):
        seen["surface"] = surface_arg
        seen["kwargs"] = kwargs
        output_path.write_bytes(b"gif bytes")
        return output_path

    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_gif", fake_export
    )

    output = export_surface_gif_animation(
        tensor,
        surface,
        tmp_path / "surface.gif",
        options=AnimationExportOptions(
            frames=11,
            fps=7,
            dpi=150,
            theme_name="Nature White",
            palette_name="Viridis Refined",
            axis="x",
            transparent_background=True,
            lighting_intensity=0.8,
            surface_smoothing=0.25,
            surface_subdivision=2,
            show_edges=True,
            specular=0.4,
        ),
    )

    assert seen["surface"] is surface
    assert seen["kwargs"]["frames"] == 11
    assert seen["kwargs"]["fps"] == 7
    assert seen["kwargs"]["dpi"] == 150
    assert seen["kwargs"]["axis"] == "x"
    assert seen["kwargs"]["transparent_background"] is True
    assert seen["kwargs"]["surface_subdivision"] == 2
    assert seen["kwargs"]["specular"] == 0.4
    assert output.read_bytes() == b"gif bytes"
    manifest = json.loads(
        output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["export_type"] == "gif"
    assert manifest["parameters"]["property"] == "young"
    assert manifest["parameters"]["theta_count"] == 5
    assert manifest["parameters"]["phi_count"] == 9
    assert "transverse_mode" not in manifest["parameters"]
    assert "transverse_samples" not in manifest["parameters"]
    assert manifest["parameters"]["palette"] == "Viridis Refined"
    assert manifest["parameters"]["palette_category"] == "sequential"
    assert manifest["parameters"]["fps"] == 7
    assert manifest["parameters"]["backend"] == "matplotlib"
    assert (
        manifest["parameters"]["fallback_reason"]
        == "transparent_background requires Matplotlib GIF export"
    )
    assert manifest["parameters"]["compose_annotations"] is True
    assert manifest["parameters"]["annotation_backend"] == "matplotlib"
    assert "title_font_size" not in manifest["parameters"]
    assert "surface_subdivision" not in manifest["parameters"]
    assert manifest["parameters"]["requested_render_style"]["title_font_size"] == 18
    assert manifest["parameters"]["requested_render_style"]["surface_subdivision"] == 2
    assert manifest["parameters"]["requested_render_style"]["show_edges"] is True
    assert manifest["parameters"]["requested_render_style"]["specular"] == 0.4
    assert "lighting_intensity" in manifest["parameters"]["ignored_render_options"]
    assert "surface_subdivision" in manifest["parameters"]["ignored_render_options"]
    assert manifest["parameters"]["transparent_background"] is True


def test_mp4_animation_export_writes_manifest_without_requiring_ffmpeg(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    seen = {}

    def fake_export(surface_arg, output_path, **kwargs):
        seen["surface"] = surface_arg
        seen["kwargs"] = kwargs
        output_path.write_bytes(b"mp4 bytes")
        return output_path

    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_mp4", fake_export
    )

    output = export_surface_mp4_animation(
        tensor,
        surface,
        tmp_path / "surface.mp4",
        options=AnimationExportOptions(
            frames=13, fps=19, dpi=180, theme_name="Nature White", axis="y"
        ),
    )

    assert seen["surface"] is surface
    assert seen["kwargs"]["frames"] == 13
    assert seen["kwargs"]["fps"] == 19
    assert seen["kwargs"]["dpi"] == 180
    assert seen["kwargs"]["axis"] == "y"
    assert output.read_bytes() == b"mp4 bytes"
    manifest = json.loads(
        output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["export_type"] == "mp4"
    assert manifest["parameters"]["property"] == "young"
    assert manifest["parameters"]["theta_count"] == 5
    assert manifest["parameters"]["phi_count"] == 9
    assert "transverse_mode" not in manifest["parameters"]
    assert "transverse_samples" not in manifest["parameters"]
    assert manifest["parameters"]["frames"] == 13
    assert manifest["parameters"]["fps"] == 19
    assert manifest["parameters"]["backend"] == "pyvista"
    assert manifest["parameters"]["palette"] == "Nature Surface"
    assert manifest["parameters"]["palette_category"] == "sequential"
    assert manifest["parameters"]["compose_annotations"] is False
    assert manifest["parameters"]["annotation_backend"] == "pyvista"
    assert manifest["parameters"]["title_font_size"] == 18
    assert manifest["parameters"]["colorbar_tick_size"] == 10
    assert manifest["parameters"]["surface_subdivision"] == 1
    assert manifest["parameters"]["specular"] == 0.32
    assert manifest["parameters"]["ignored_render_options"] == []
    assert manifest["parameters"]["requested_render_style"]["specular"] == 0.32
    assert manifest["parameters"]["transparent_background"] is False


def test_animation_exports_preserve_format_specific_default_frame_rates(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    seen = {}

    def fake_gif(_surface, output_path, **kwargs):
        seen["gif_fps"] = kwargs["fps"]
        output_path.write_bytes(b"gif")
        return output_path

    def fake_mp4(_surface, output_path, **kwargs):
        seen["mp4_fps"] = kwargs["fps"]
        output_path.write_bytes(b"mp4")
        return output_path

    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_gif", fake_gif
    )
    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_mp4", fake_mp4
    )

    gif_path = export_surface_gif_animation(tensor, surface, tmp_path / "default.gif")
    mp4_path = export_surface_mp4_animation(tensor, surface, tmp_path / "default.mp4")

    assert seen == {"gif_fps": 12, "mp4_fps": 24}
    gif_manifest = json.loads(
        gif_path.with_name(f"{gif_path.name}.manifest.json").read_text(encoding="utf-8")
    )
    mp4_manifest = json.loads(
        mp4_path.with_name(f"{mp4_path.name}.manifest.json").read_text(encoding="utf-8")
    )
    assert gif_manifest["parameters"]["fps"] == 12
    assert mp4_manifest["parameters"]["fps"] == 24


def test_animation_options_keep_existing_positional_field_order():
    options = AnimationExportOptions(72, 300)

    assert options.frames == 72
    assert options.dpi == 300
    assert options.fps is None


def test_mp4_transparent_background_is_rejected_before_writing(tmp_path):
    tensor, surface = _si_tensor_and_surface()
    output = tmp_path / "transparent.mp4"

    with pytest.raises(ValueError, match="MP4.*transparent"):
        export_surface_mp4_animation(
            tensor,
            surface,
            output,
            options=AnimationExportOptions(transparent_background=True),
        )

    assert not output.exists()
    assert not output.with_name(f"{output.name}.manifest.json").exists()


def test_gif_animation_export_records_matplotlib_fallback_and_reason(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    calls = []

    def fake_export(surface_arg, output_path, **kwargs):
        calls.append(kwargs)
        if kwargs["backend"] == "pyvista":
            raise PyVistaUnavailableError("forced unavailable")
        output_path.write_bytes(b"matplotlib gif bytes")
        return output_path

    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_gif", fake_export
    )

    output = export_surface_gif_animation(
        tensor,
        surface,
        tmp_path / "fallback.gif",
        options=AnimationExportOptions(frames=5, fps=3),
    )

    assert [call["backend"] for call in calls] == ["pyvista", "matplotlib"]
    assert output.read_bytes() == b"matplotlib gif bytes"
    manifest = json.loads(
        output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8")
    )
    parameters = manifest["parameters"]
    assert parameters["backend"] == "matplotlib"
    assert parameters["annotation_backend"] == "matplotlib"
    assert parameters["compose_annotations"] is True
    assert parameters["fallback_reason"] == "forced unavailable"
    assert parameters["fps"] == 3
    assert "lighting_intensity" not in parameters
    assert "lighting_intensity" in parameters["ignored_render_options"]
    assert parameters["requested_render_style"]["lighting_intensity"] == 1.0


def test_transparent_gif_animation_records_matplotlib_backend(tmp_path, monkeypatch):
    tensor, surface = _si_tensor_and_surface()
    seen = {}

    def fake_export(surface_arg, output_path, **kwargs):
        seen.update(kwargs)
        output_path.write_bytes(b"transparent gif bytes")
        return output_path

    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_gif", fake_export
    )

    output = export_surface_gif_animation(
        tensor,
        surface,
        tmp_path / "transparent.gif",
        options=AnimationExportOptions(frames=5, fps=4, transparent_background=True),
    )

    assert seen["backend"] == "matplotlib"
    manifest = json.loads(
        output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8")
    )
    parameters = manifest["parameters"]
    assert parameters["backend"] == "matplotlib"
    assert parameters["annotation_backend"] == "matplotlib"
    assert parameters["compose_annotations"] is True
    assert (
        parameters["fallback_reason"]
        == "transparent_background requires Matplotlib GIF export"
    )
    assert parameters["fps"] == 4


def test_mp4_animation_export_records_matplotlib_fallback_and_reason(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    calls = []

    def fake_export(surface_arg, output_path, **kwargs):
        calls.append(kwargs)
        if kwargs["backend"] == "pyvista":
            raise PyVistaUnavailableError("forced mp4 unavailable")
        output_path.write_bytes(b"matplotlib mp4 bytes")
        return output_path

    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_mp4", fake_export
    )

    output = export_surface_mp4_animation(
        tensor,
        surface,
        tmp_path / "fallback.mp4",
        options=AnimationExportOptions(frames=5, fps=8),
    )

    assert [call["backend"] for call in calls] == ["pyvista", "matplotlib"]
    assert output.read_bytes() == b"matplotlib mp4 bytes"
    manifest = json.loads(
        output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8")
    )
    parameters = manifest["parameters"]
    assert parameters["backend"] == "matplotlib"
    assert parameters["annotation_backend"] == "matplotlib"
    assert parameters["fallback_reason"] == "forced mp4 unavailable"
    assert parameters["fps"] == 8


def test_animation_export_falls_back_after_generic_pyvista_runtime_failure(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    calls = []

    def fake_export(_surface, output_path, **kwargs):
        calls.append(kwargs["backend"])
        if kwargs["backend"] == "pyvista":
            raise RuntimeError("VTK context creation failed")
        output_path.write_bytes(b"matplotlib gif bytes")
        return output_path

    monkeypatch.setattr(
        "crystal_elastic_workbench.animation_export.export_rotating_gif", fake_export
    )

    output = export_surface_gif_animation(
        tensor, surface, tmp_path / "runtime-fallback.gif"
    )

    assert calls == ["pyvista", "matplotlib"]
    manifest = json.loads(
        output.with_name(f"{output.name}.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["parameters"]["backend"] == "matplotlib"
    assert manifest["parameters"]["fallback_reason"] == "VTK context creation failed"


def test_animation_manifest_failure_preserves_existing_pair_and_removes_staging(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    output = tmp_path / "atomic.gif"
    manifest = output.with_name(f"{output.name}.manifest.json")
    output.write_bytes(b"old gif")
    manifest.write_bytes(b"old manifest")

    def fake_export(_surface, output_path, **kwargs):
        output_path.write_bytes(b"new gif")
        return output_path

    def fail_manifest(_tensor, staged_output, **kwargs):
        staged_manifest = Path(staged_output).with_name(
            f"{Path(staged_output).name}.manifest.json"
        )
        staged_manifest.write_bytes(b"partial manifest")
        raise RuntimeError("manifest injection")

    monkeypatch.setattr(animation_export_module, "export_rotating_gif", fake_export)
    monkeypatch.setattr(animation_export_module, "write_export_manifest", fail_manifest)

    with pytest.raises(RuntimeError, match="manifest injection"):
        export_surface_gif_animation(tensor, surface, output)

    assert output.read_bytes() == b"old gif"
    assert manifest.read_bytes() == b"old manifest"
    assert not list(tmp_path.glob(f".{output.name}-*"))


def test_animation_matplotlib_fallback_failure_preserves_existing_pair(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    output = tmp_path / "fallback-failure.gif"
    manifest = output.with_name(f"{output.name}.manifest.json")
    output.write_bytes(b"old gif")
    manifest.write_bytes(b"old manifest")

    def fail_both_backends(_surface, output_path, **kwargs):
        output_path.write_bytes(b"partial gif")
        raise RuntimeError(f"{kwargs['backend']} injection")

    monkeypatch.setattr(
        animation_export_module, "export_rotating_gif", fail_both_backends
    )

    with pytest.raises(RuntimeError, match="matplotlib injection"):
        export_surface_gif_animation(tensor, surface, output)

    assert output.read_bytes() == b"old gif"
    assert manifest.read_bytes() == b"old manifest"
    assert not list(tmp_path.glob(f".{output.name}-*"))


def test_animation_publish_failure_rolls_back_both_entries(tmp_path, monkeypatch):
    tensor, surface = _si_tensor_and_surface()
    output = tmp_path / "commit-failure.gif"
    manifest = output.with_name(f"{output.name}.manifest.json")
    output.write_bytes(b"old gif")
    manifest.write_bytes(b"old manifest")

    def fake_export(_surface, output_path, **kwargs):
        output_path.write_bytes(b"new gif")
        return output_path

    real_replace = atomic_publish_module.os.replace

    def fail_manifest_install(source, destination):
        if (
            Path(destination).parent == tmp_path
            and Path(destination).name == manifest.name
        ):
            raise OSError("manifest commit injection")
        return real_replace(source, destination)

    monkeypatch.setattr(animation_export_module, "export_rotating_gif", fake_export)
    monkeypatch.setattr(atomic_publish_module.os, "replace", fail_manifest_install)

    with pytest.raises(OSError, match="manifest commit injection"):
        export_surface_gif_animation(tensor, surface, output)

    assert output.read_bytes() == b"old gif"
    assert manifest.read_bytes() == b"old manifest"
    assert not list(tmp_path.glob(f".{output.name}-*"))


def test_animation_replaces_hardlink_entry_without_modifying_external_inode(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    output = tmp_path / "hardlink.gif"
    external = tmp_path / "external.gif"
    manifest = output.with_name(f"{output.name}.manifest.json")
    external.write_bytes(b"old external gif")
    try:
        os.link(external, output)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")
    manifest.write_bytes(b"old manifest")

    def fake_export(_surface, output_path, **kwargs):
        output_path.write_bytes(b"new gif")
        return output_path

    monkeypatch.setattr(animation_export_module, "export_rotating_gif", fake_export)
    export_surface_gif_animation(tensor, surface, output)

    assert output.read_bytes() == b"new gif"
    assert external.read_bytes() == b"old external gif"


def test_animation_replaces_symlink_entry_without_modifying_external_target(
    tmp_path, monkeypatch
):
    tensor, surface = _si_tensor_and_surface()
    output = tmp_path / "symlink.gif"
    external = tmp_path / "external.gif"
    manifest = output.with_name(f"{output.name}.manifest.json")
    external.write_bytes(b"old external gif")
    try:
        os.symlink(external, output)
    except OSError as exc:
        pytest.skip(f"symbolic links unavailable: {exc}")
    manifest.write_bytes(b"old manifest")

    def fake_export(_surface, output_path, **kwargs):
        output_path.write_bytes(b"new gif")
        return output_path

    monkeypatch.setattr(animation_export_module, "export_rotating_gif", fake_export)
    export_surface_gif_animation(tensor, surface, output)

    assert output.read_bytes() == b"new gif"
    assert not output.is_symlink()
    assert external.read_bytes() == b"old external gif"


def test_animation_refuses_to_replace_a_directory_target(tmp_path, monkeypatch):
    tensor, surface = _si_tensor_and_surface()
    output = tmp_path / "directory.gif"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_bytes(b"keep")

    def fake_export(_surface, output_path, **kwargs):
        output_path.write_bytes(b"new gif")
        return output_path

    monkeypatch.setattr(animation_export_module, "export_rotating_gif", fake_export)

    with pytest.raises(IsADirectoryError, match="Refusing to replace"):
        export_surface_gif_animation(tensor, surface, output)

    assert marker.read_bytes() == b"keep"
    assert not list(tmp_path.glob(f".{output.name}-*"))
