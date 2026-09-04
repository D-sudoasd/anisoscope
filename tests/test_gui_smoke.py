import os
import json

import numpy as np
import pandas as pd
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _flush_qt_deferred_deletes(app) -> None:
    from PySide6.QtCore import QEvent

    app.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


def test_main_window_loads_example_and_analyzes(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.load_example_by_name("Si cubic")
    window.analyze_current_matrix()

    assert window.windowTitle() == "AnisoScope"
    assert window.current_tensor is not None
    assert window.example_combo.currentText() == "Si cubic"
    assert window.current_summary is not None
    assert window.summary_table.rowCount() > 0
    assert window.model_table.rowCount() == 4
    assert window.export_model_table_button.text() == "Export Model Table"
    assert "Overall stability: PASS" in window.stability_text.toPlainText()
    assert "overall_stable" not in window.stability_text.toPlainText()
    assert window.summary_table.item(0, 0).text() == "Bulk modulus (Voigt) [GPa]"
    assert window.model_table.horizontalHeaderItem(2).text() == "B [GPa]"
    assert "Sampled-grid extrema" in window.surface_extrema_label.text()
    assert "refine theta/phi" in window.surface_extrema_label.text()
    window.close()
    app.processEvents()


def test_summary_save_and_copy_use_readable_labels_with_numeric_values(tmp_path, monkeypatch, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QFileDialog

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    assert window.analyze_current_matrix() is True
    output = tmp_path / "summary.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args, **_kwargs: (str(output), "CSV (*.csv)"))

    window.save_summary()
    exported = pd.read_csv(output)
    assert "Bulk modulus (Voigt) [GPa]" in exported.columns
    assert "bulk_voigt_gpa" not in exported.columns
    assert pd.api.types.is_numeric_dtype(exported["Bulk modulus (Voigt) [GPa]"])

    window.copy_summary()
    copied = QApplication.clipboard().text()
    assert "Bulk modulus (Voigt) [GPa]" in copied
    assert "bulk_voigt_gpa" not in copied

    window.close()
    app.processEvents()


def test_long_material_name_is_compact_in_status_chip_and_available_in_tooltip(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    material_name = "Very long research material identifier with processing condition"

    window.material_edit.setText(material_name)

    assert window.material_status_chip.text().endswith("...")
    assert len(window.material_status_chip.text()) <= len("Material: ") + 28
    assert window.material_status_chip.toolTip() == f"Material: {material_name}"

    window.close()
    app.processEvents()


def test_input_panel_scrolls_on_laptop_height_instead_of_forcing_a_tall_window(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1280, 720)
    window.show()
    app.processEvents()

    assert window.minimumSizeHint().height() <= 720
    assert window.minimumSizeHint().width() <= 1280
    assert window.width() <= 1280
    assert window.height() <= 720
    assert window.input_scroll.verticalScrollBar().maximum() > 0
    assert window.input_scroll.isAncestorOf(window.analyze_workflow_button) is False
    assert window.analyze_workflow_button.isVisible() is True

    window.close()
    app.processEvents()


def test_narrow_window_stacks_input_and_results_to_keep_controls_reachable(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1024, 768)
    window.show()
    app.processEvents()

    assert window.main_splitter.orientation() == Qt.Vertical
    assert window.width() <= 1024
    assert window.analyze_workflow_button.isVisible() is True
    assert window.tabs.isVisible() is True
    assert window.input_scroll.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded

    window.resize(1280, 720)
    app.processEvents()
    assert window.main_splitter.orientation() == Qt.Horizontal

    window.close()
    app.processEvents()


def test_main_window_exposes_publication_plot_controls(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow
    from crystal_elastic_workbench.plot_styles import list_palette_names

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.theme_combo.currentText() == "Nature White"
    assert set(list_palette_names()).issuperset(
        {window.theme_combo.itemText(index) for index in range(window.theme_combo.count())}
    )
    assert set(list_palette_names()).issuperset(
        {window.palette_combo.itemText(index) for index in range(window.palette_combo.count())}
    )
    assert window.export_dpi_spin.value() == 300
    assert window.transparent_background_checkbox.isChecked() is False
    assert window.lighting_spin.value() == 100
    assert window.surface_smoothing_spin.value() == 0
    assert window.show_edges_checkbox.isChecked() is False
    assert window.show_edges_checkbox.text() == "Subtle edges"
    assert window.lock_color_range_checkbox.isChecked() is False
    assert window.color_vmin_spin.isEnabled() is False
    assert window.color_vmax_spin.isEnabled() is False
    assert window.radius_mode_combo.currentText() == "Physical"
    assert window.cmap_combo.currentText() == "Nature Surface"
    assert window.cmap_combo.itemText(0) == "Nature Surface"
    assert window.cmap_combo.findText("Blue-White-Red") >= 0

    window.close()
    app.processEvents()


def test_main_window_exposes_scientific_dashboard_controls(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtWidgets import QHeaderView

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.tabs.tabText(0) == "Dashboard"
    assert "Ready" in window.workflow_status_label.text()
    assert "Material" in window.material_status_chip.text()
    assert "Crystal" in window.crystal_status_chip.text()
    assert "Unit" in window.unit_status_chip.text()
    assert window.unit_edit.isReadOnly()
    assert "3D backend" in window.pyvista_status_chip.text()
    assert len(window.findChildren(QWidget, "metricCard")) == 4
    assert window.analyze_workflow_button.text() == "Analyze + Update Figures"
    assert window.paste_matrix_button.text() == "Paste Matrix"
    assert window.cij_table.horizontalHeader().sectionResizeMode(0) == QHeaderView.Stretch
    assert window.export_paper_figures_button.text() == "Export Paper Figures"
    assert window.export_full_package_button.text() == "Export Full Package"

    window.close()
    app.processEvents()


def test_surface_plot_uses_high_quality_image_preview_when_pyvista_available(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow
    from crystal_elastic_workbench.render3d import pyvista_status

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.load_example_by_name("Si cubic")
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    window.update_surface_plot()

    assert window.current_surface is not None
    if pyvista_status().available:
        assert window.surface_pane.preview_mode == "image"
    else:
        assert window.surface_pane.preview_mode == "figure"

    window.close()
    app.processEvents()


def test_analyze_workflow_updates_dashboard_and_default_figures(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow
    from crystal_elastic_workbench.render3d import pyvista_status

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.load_example_by_name("Si cubic")
    window.analyze_current_matrix()

    assert window.current_tensor is not None
    assert window.current_summary is not None
    assert window.current_line_data is not None
    assert window.current_polar_data is not None
    assert window.current_surface is not None
    assert "Si cubic" in window.material_status_chip.text()
    assert "cubic" in window.crystal_status_chip.text()
    assert "GPa" in window.unit_status_chip.text()
    assert window.workflow_status_label.text() == "Checks passed: analysis complete"
    assert "updated" in window.figure_status_label.text().lower()
    assert "Recommended model: Hill" in window.anisotropy_summary_label.text()
    assert window.model_table.item(0, 0).text() == "Voigt"
    assert window.model_table.item(2, 0).text() == "Hill"
    assert window.metric_labels["B_H"].text() != "-"
    assert window.metric_labels["G_H"].text() != "-"
    assert window.metric_labels["E_H"].text() != "-"
    assert window.metric_labels["A_U"].text() != "-"
    assert window.export_full_package_button.isEnabled() is True
    assert window.export_paper_figures_button.isEnabled() is True
    assert window.save_summary_button.isEnabled() is True
    assert window.line_save_button.isEnabled() is True
    assert window.mp4_button.isEnabled() is True
    if pyvista_status().available:
        assert window.surface_pane.preview_mode == "image"
    else:
        assert window.surface_pane.preview_mode == "figure"

    window.close()
    app.processEvents()


def test_startup_banners_agree_and_exports_start_disabled(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.workflow_status_label.text() == "Ready for analysis"
    assert window.dashboard_stability_banner.text() == "No analysis yet"
    assert window.export_full_package_button.isEnabled() is False
    assert window.export_paper_figures_button.isEnabled() is False
    assert window.save_summary_button.isEnabled() is False
    assert window.line_save_button.isEnabled() is False
    assert window.mp4_button.isEnabled() is False

    window.close()
    app.processEvents()


def test_material_rename_keeps_cached_analysis(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.analyze_current_matrix()
    summary = window.current_summary
    tensor = window.current_tensor

    window.material_edit.setText("Renamed silicon")

    assert window.current_summary is summary
    assert window.current_tensor is tensor
    assert window.current_tensor.material_name == "Renamed silicon"
    assert "Renamed silicon" in window.material_status_chip.text()
    assert window.export_full_package_button.isEnabled() is True

    window.close()
    app.processEvents()


def test_theta_change_invalidates_surface_but_keeps_tensor(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.analyze_current_matrix()

    assert window.current_surface is not None
    window.theta_spin.setValue(max(7, window.theta_spin.value() - 2))

    assert window.current_tensor is not None
    assert window.current_surface is None
    assert window.surface_save_button.isEnabled() is False
    assert window.export_paper_figures_button.isEnabled() is True
    assert "incomplete" in window.figure_status_label.text().lower()

    window.close()
    app.processEvents()


def test_transparent_background_disables_mp4_export(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.analyze_current_matrix()

    assert window.mp4_button.isEnabled() is True
    window.transparent_background_checkbox.setChecked(True)
    assert window.mp4_button.isEnabled() is False

    window.close()
    app.processEvents()


def test_input_changes_invalidate_cached_analysis(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.analyze_current_matrix()

    assert window.current_tensor is not None
    assert window.current_summary is not None
    assert window.current_line_data is not None

    window.load_example_by_name("MgO cubic")

    assert window.current_tensor is None
    assert window.current_summary is None
    assert window.current_stability is None
    assert window.current_line_data is None
    assert window.current_polar_data is None
    assert window.current_surface is None
    assert "analyze" in window.workflow_status_label.text().lower()
    assert window.export_full_package_button.isEnabled() is False
    assert window.save_summary_button.isEnabled() is False

    window.close()
    app.processEvents()


def test_manual_matrix_edit_invalidates_cached_analysis(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.analyze_current_matrix()

    window.cij_table.item(0, 0).setText("999")

    assert window.current_tensor is None
    assert window.current_summary is None
    assert window.current_line_data is None

    window.close()
    app.processEvents()


def test_unstable_matrix_keeps_stability_diagnostics_when_summary_fails(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.populate_matrix(np.diag([1.0, 1.0, 1.0, -1.0, -1.0, -0.5]))
    seen = {}
    window.show_error = lambda title, exc: seen.update(title=title, error=str(exc))

    window.analyze_current_matrix()

    assert window.current_stability is not None
    assert window.current_stability.overall_stable is False
    assert window.current_summary is None
    assert "Overall stability: FAIL" in window.stability_text.toPlainText()
    assert seen["title"] == "Derived analysis failed"
    assert "Reuss shear modulus" in seen["error"]
    assert window.export_model_table_button.isEnabled() is False
    assert window.export_paper_figures_button.isEnabled() is False
    assert window.export_full_package_button.isEnabled() is False

    window.close()
    app.processEvents()


@pytest.mark.parametrize(
    ("method_name", "reader_name", "error_title"),
    [
        ("import_csv", "read_csv", "CSV import failed"),
        ("import_excel", "read_excel", "Excel import failed"),
    ],
)
def test_tabular_import_read_errors_are_reported(
    method_name, reader_name, error_title, monkeypatch, qtbot=None
):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    seen = {}
    window.show_error = lambda title, exc: seen.update(title=title, error=str(exc))
    monkeypatch.setattr(
        gui_module.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: ("broken-input", "All files (*)"),
    )
    monkeypatch.setattr(
        gui_module.pd,
        reader_name,
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("cannot read")),
    )

    getattr(window, method_name)()

    assert seen == {"title": error_title, "error": "cannot read"}

    window.close()
    app.processEvents()


def test_paste_matrix_from_clipboard_populates_cij_table(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.examples import EXAMPLE_MATERIALS
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    matrix = EXAMPLE_MATERIALS["Si cubic"].matrix
    clipboard_text = "\n".join("\t".join(f"{value:.8g}" for value in row) for row in matrix)
    QApplication.clipboard().setText(clipboard_text)

    window.populate_matrix(np.zeros((6, 6)))
    window.paste_matrix_from_clipboard()

    assert np.allclose(window.read_matrix(), matrix)

    window.close()
    app.processEvents()


def test_non_numeric_cij_cell_is_reported_and_highlighted(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.cij_table.item(2, 4).setText("not-a-number")

    with pytest.raises(ValueError, match="C33-C13"):
        window.read_matrix()

    assert window.cij_table.item(2, 4).background().color() == QColor("#ffd6d6")

    window.close()
    app.processEvents()


def test_json_import_rejects_non_gpa_without_changing_interface(tmp_path, monkeypatch, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.load_example_by_name("Si cubic")
    original_matrix = window.read_matrix().copy()
    original_material = window.material_edit.text()
    original_system = window.system_combo.currentText()
    input_path = tmp_path / "non_gpa.json"
    input_path.write_text(
        json.dumps(
            {
                "stiffness_matrix": (np.eye(6) * 1000.0).tolist(),
                "material_name": "Should not load",
                "unit": "MPa",
                "crystal_system": "hexagonal",
            }
        ),
        encoding="utf-8",
    )
    seen = {}

    monkeypatch.setattr(
        gui_module.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(input_path), "JSON (*.json)"),
    )
    monkeypatch.setattr(window, "show_error", lambda title, exc: seen.update(title=title, error=str(exc)))

    window.import_json()

    assert seen["title"] == "JSON import failed"
    assert "converted to GPa before import" in seen["error"]
    assert np.array_equal(window.read_matrix(), original_matrix)
    assert window.material_edit.text() == original_material
    assert window.system_combo.currentText() == original_system
    assert window.unit_edit.text() == "GPa"

    window.close()
    app.processEvents()


def test_json_import_rejects_nonfinite_matrix_without_changing_interface(tmp_path, monkeypatch, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.load_example_by_name("Si cubic")
    original_matrix = window.read_matrix().copy()
    original_material = window.material_edit.text()
    original_system = window.system_combo.currentText()
    input_path = tmp_path / "nonfinite.json"
    payload = json.dumps(
        {
            "stiffness_matrix": (np.eye(6) * 1000.0).tolist(),
            "material_name": "Should not load",
            "unit": "GPa",
            "crystal_system": "hexagonal",
        }
    ).replace("1000.0", "1e309", 1)
    input_path.write_text(payload, encoding="utf-8")
    seen = {}

    monkeypatch.setattr(
        gui_module.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(input_path), "JSON (*.json)"),
    )
    monkeypatch.setattr(window, "show_error", lambda title, exc: seen.update(title=title, error=str(exc)))

    window.import_json()

    assert seen["title"] == "JSON import failed"
    assert "only finite values" in seen["error"]
    assert np.array_equal(window.read_matrix(), original_matrix)
    assert window.material_edit.text() == original_material
    assert window.system_combo.currentText() == original_system
    assert window.unit_edit.text() == "GPa"

    window.close()
    app.processEvents()


def test_batch_paper_figure_export_writes_pngs_and_manifests(tmp_path, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.load_example_by_name("Si cubic")
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    window.analyze_current_matrix()

    exported = window.export_paper_figures_to_directory(tmp_path)

    assert set(exported) == {"line_png", "polar_png", "surface_png"}
    for path in exported.values():
        assert path.exists()
        assert path.stat().st_size > 1000
        manifest = json.loads(path.with_name(f"{path.name}.manifest.json").read_text(encoding="utf-8"))
        assert manifest["parameters"]["theme"] == "Nature White"
        assert manifest["parameters"]["dpi"] == 300
    surface_manifest = json.loads(
        exported["surface_png"].with_name(f"{exported['surface_png'].name}.manifest.json").read_text(encoding="utf-8")
    )
    assert surface_manifest["parameters"]["backend"] in {"pyvista", "matplotlib"}

    window.close()
    app.processEvents()


def test_gui_current_figure_sidecar_records_sampling_parameters(tmp_path, monkeypatch, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.load_example_by_name("Si cubic")
    window.update_line_plot()
    output = tmp_path / "line.png"
    monkeypatch.setattr(
        gui_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output), "PNG (*.png)"),
    )

    window.save_current_figure(window.line_pane, window.current_line_data)

    manifest = json.loads((tmp_path / "line.png.manifest.json").read_text(encoding="utf-8"))
    assert manifest["parameters"]["property"] == "young"
    assert "transverse_mode" not in manifest["parameters"]
    assert "transverse_samples" not in manifest["parameters"]
    assert manifest["parameters"]["angle_count"] == 361

    window.close()
    app.processEvents()


def test_gui_mp4_export_forwards_surface_style_options(tmp_path, monkeypatch, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.core import ElasticTensor
    from crystal_elastic_workbench.examples import EXAMPLE_MATERIALS
    from crystal_elastic_workbench.gui import MainWindow
    from crystal_elastic_workbench.sampling import sample_sphere

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    example = EXAMPLE_MATERIALS["Si cubic"]
    tensor = ElasticTensor(
        example.matrix,
        crystal_system=example.crystal_system,
        unit=example.unit,
        material_name=example.name,
    )
    window.current_tensor = tensor
    window.current_surface = sample_sphere(tensor, property_name="young", theta_count=5, phi_count=9)
    window.lighting_spin.setValue(77)
    window.surface_smoothing_spin.setValue(35)
    window.show_edges_checkbox.setChecked(True)
    window.lock_color_range_checkbox.setChecked(True)
    window.color_vmin_spin.setValue(100.0)
    window.color_vmax_spin.setValue(300.0)
    window.radius_mode_combo.setCurrentText("Normalized shape")
    palette_index = window.cmap_combo.findText("Blue-Gold")
    assert palette_index >= 0
    window.cmap_combo.setCurrentIndex(palette_index)
    output = tmp_path / "surface.mp4"
    seen = {}

    def fake_get_save_file_name(*args, **kwargs):
        return str(output), "MP4 (*.mp4)"

    def fake_export(tensor_arg, surface_arg, output_path, *, options):
        seen["tensor"] = tensor_arg
        seen["surface"] = surface_arg
        seen["path"] = output_path
        seen["options"] = options
        output.write_bytes(b"mp4 bytes")
        return output

    monkeypatch.setattr(gui_module.QFileDialog, "getSaveFileName", fake_get_save_file_name)
    monkeypatch.setattr(gui_module.QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(gui_module, "export_surface_mp4_animation", fake_export)

    window.export_mp4()

    assert seen["tensor"] is tensor
    assert seen["surface"] is window.current_surface
    assert seen["path"] == str(output)
    assert seen["options"].palette_name == "Blue-Gold"
    assert seen["options"].lighting_intensity == pytest.approx(0.77)
    assert seen["options"].surface_smoothing == pytest.approx(0.35)
    assert seen["options"].show_edges is True
    assert seen["options"].scalar_range == (100.0, 300.0)
    assert seen["options"].radius_mode == "normalized"

    window.close()
    app.processEvents()


def test_render3d_options_forward_locked_range_and_radius_mode(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.lock_color_range_checkbox.setChecked(True)
    window.color_vmin_spin.setValue(100.0)
    window.color_vmax_spin.setValue(300.0)
    window.radius_mode_combo.setCurrentText("Normalized shape")
    options = window._render3d_options()

    assert window.color_vmin_spin.isEnabled() is True
    assert window.color_vmax_spin.isEnabled() is True
    assert options.scalar_range == (100.0, 300.0)
    assert options.radius_mode == "normalized"
    assert options.radius_scale == 1.0
    assert options.ambient == pytest.approx(0.28)

    window.close()
    app.processEvents()


def test_style_changes_clear_previews_but_keep_sampled_data_and_data_exports(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    assert window.analyze_current_matrix() is True
    original_data = (window.current_line_data, window.current_polar_data, window.current_surface)

    # Any style change makes the visible previews stale, but sampled arrays remain
    # valid for data/animation export and can be re-rendered explicitly.
    window.theme_combo.setCurrentText("Gray Print")
    for pane in (window.line_pane, window.polar_pane, window.surface_pane):
        assert pane.preview_mode == "empty"
    assert (window.current_line_data, window.current_polar_data, window.current_surface) == original_data
    assert window.line_save_button.isEnabled() is False
    assert window.polar_save_button.isEnabled() is False
    assert window.surface_save_button.isEnabled() is False
    assert window.line_save_data_button.isEnabled() is True
    assert window.polar_save_data_button.isEnabled() is True
    assert window.surface_save_data_button.isEnabled() is True
    assert window.gif_button.isEnabled() is True
    assert window.mp4_button.isEnabled() is True

    # Re-render so the remaining style controls exercise the same invalidation
    # contract without discarding the analysis itself.
    assert window.update_line_plot() is True
    assert "incomplete" in window.figure_status_label.text().lower()
    assert window.update_polar_plot() is True
    assert "incomplete" in window.figure_status_label.text().lower()
    assert window.update_surface_plot() is True
    assert "updated" in window.figure_status_label.text().lower()
    assert "analysis complete" in window.workflow_status_label.text().lower()
    window.palette_combo.setCurrentText("Nature Muted")
    assert window.line_pane.preview_mode == "empty"
    assert window.polar_pane.preview_mode == "empty"
    assert window.surface_pane.preview_mode == "empty"
    assert window.line_save_data_button.isEnabled() is True
    assert window.polar_save_data_button.isEnabled() is True
    assert window.surface_save_data_button.isEnabled() is True
    assert window.gif_button.isEnabled() is True
    assert window.mp4_button.isEnabled() is True

    assert window.update_line_plot() is True
    assert window.update_polar_plot() is True
    assert window.update_surface_plot() is True
    window.export_dpi_spin.setValue(window.export_dpi_spin.value() + 1)
    assert window.line_pane.preview_mode == "empty"
    assert window.polar_pane.preview_mode == "empty"
    assert window.surface_pane.preview_mode == "empty"
    assert window.line_save_data_button.isEnabled() is True
    assert window.polar_save_data_button.isEnabled() is True
    assert window.surface_save_data_button.isEnabled() is True
    assert window.gif_button.isEnabled() is True
    assert window.mp4_button.isEnabled() is True

    assert window.update_line_plot() is True
    assert window.update_polar_plot() is True
    assert window.update_surface_plot() is True
    window.transparent_background_checkbox.setChecked(True)
    assert window.line_pane.preview_mode == "empty"
    assert window.polar_pane.preview_mode == "empty"
    assert window.surface_pane.preview_mode == "empty"
    assert window.line_save_data_button.isEnabled() is True
    assert window.polar_save_data_button.isEnabled() is True
    assert window.surface_save_data_button.isEnabled() is True
    assert window.gif_button.isEnabled() is True
    assert window.mp4_button.isEnabled() is False

    window.close()
    app.processEvents()


def test_3d_cmap_change_clears_only_surface_preview_and_forwards_new_cmap(monkeypatch, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    assert window.analyze_current_matrix() is True
    assert window.line_pane.preview_mode == "figure"
    assert window.polar_pane.preview_mode == "figure"
    original_surface = window.current_surface
    palette_index = window.cmap_combo.findText("Blue-Gold")
    assert palette_index >= 0
    window.cmap_combo.setCurrentIndex(palette_index)

    assert window.current_surface is original_surface
    assert window.surface_pane.preview_mode == "empty"
    assert window.line_pane.preview_mode == "figure"
    assert window.polar_pane.preview_mode == "figure"
    assert window.surface_save_button.isEnabled() is False
    assert window.surface_save_data_button.isEnabled() is True
    assert window.gif_button.isEnabled() is True
    assert window.mp4_button.isEnabled() is True

    seen = {}

    def fake_render(surface, *, options):
        seen["palette"] = options.palette_name
        return np.zeros((8, 8, 4), dtype=np.uint8)

    monkeypatch.setattr(gui_module, "render_surface_image", fake_render)
    assert window.update_surface_plot() is True
    assert seen["palette"] == "Blue-Gold"
    assert window.surface_pane.preview_mode == "image"
    assert window.surface_save_button.isEnabled() is True

    window.lighting_spin.setValue(window.lighting_spin.value() - 1)
    assert window.surface_pane.preview_mode == "empty"
    assert window.line_pane.preview_mode == "figure"
    assert window.polar_pane.preview_mode == "figure"
    assert window.surface_save_data_button.isEnabled() is True

    assert window.update_surface_plot() is True
    window.surface_smoothing_spin.setValue(window.surface_smoothing_spin.value() + 1)
    assert window.surface_pane.preview_mode == "empty"

    assert window.update_surface_plot() is True
    window.show_edges_checkbox.setChecked(True)
    assert window.surface_pane.preview_mode == "empty"

    window.close()
    app.processEvents()


def test_analyze_returns_false_and_keeps_scalars_when_one_figure_fails(monkeypatch, qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    seen = {}
    window.show_error = lambda title, exc: seen.setdefault("errors", []).append((title, str(exc)))
    original_render_surface_image = gui_module.render_surface_image

    def fail_render(*_args, **_kwargs):
        raise RuntimeError("render unavailable")

    def fail_fallback(*_args, **_kwargs):
        raise RuntimeError("fallback unavailable")

    # Exercise the real update_surface_plot exception path: sampling succeeds,
    # but the renderer fails after the surface has been computed.
    monkeypatch.setattr(gui_module, "render_surface_image", fail_render)
    monkeypatch.setattr(gui_module, "plot_directional_surface", fail_fallback)
    assert window.analyze_current_matrix() is False
    assert window.current_summary is not None
    assert window.current_line_data is not None
    assert window.current_polar_data is not None
    assert window.current_surface is None
    assert window.line_pane.preview_mode == "figure"
    assert window.polar_pane.preview_mode == "figure"
    assert "partial" in window.workflow_status_label.text().lower()
    assert "warning" in window.workflow_status_label.text().lower()
    assert "3D" in window.figure_status_label.text()
    assert window.metric_labels["B_H"].text() != "-"
    assert seen["errors"] == [
        (
            "3D plot failed",
            "PyVista render failed (render unavailable); "
            "Matplotlib fallback failed (fallback unavailable)",
        )
    ]

    # Restore the renderer and confirm that a single successful re-render
    # recomputes both dashboard and workflow figure state.
    monkeypatch.setattr(gui_module, "render_surface_image", original_render_surface_image)
    monkeypatch.undo()
    assert window.update_surface_plot() is True
    assert window.current_surface is not None
    assert "updated" in window.figure_status_label.text().lower()
    assert "analysis complete" in window.workflow_status_label.text().lower()

    window.close()
    app.processEvents()


def test_gui_falls_back_to_matplotlib_after_generic_pyvista_runtime_error(
    monkeypatch,
    qtbot=None,
):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench import gui as gui_module
    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)

    def fail_render(*_args, **_kwargs):
        raise RuntimeError("VTK context lost")

    monkeypatch.setattr(gui_module, "render_surface_image", fail_render)

    assert window.update_surface_plot() is True
    assert window.current_surface is not None
    assert window.surface_pane.preview_mode == "figure"
    assert "Matplotlib fallback" in window.render3d_status_label.text()
    assert "VTK context lost" in window.render3d_status_label.text()

    window.close()
    app.processEvents()


def test_figure_pane_cleanup_destroys_preview_widgets_without_top_level_orphans(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import FigureCanvas, ImagePreviewLabel, MainWindow, NavigationToolbar

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    assert window.analyze_current_matrix() is True

    # Cover both Matplotlib canvas/toolbar and the image-preview branch.
    window.surface_pane.set_image(np.zeros((8, 8, 4), dtype=np.uint8))
    for theme in ("Gray Print", "Nature White"):
        window.theme_combo.setCurrentText(theme)
        _flush_qt_deferred_deletes(app)
        assert all(pane.preview_mode == "empty" for pane in (window.line_pane, window.polar_pane, window.surface_pane))
        for pane in (window.line_pane, window.polar_pane, window.surface_pane):
            assert pane.findChildren(FigureCanvas) == []
            assert pane.findChildren(NavigationToolbar) == []
            assert pane.findChildren(ImagePreviewLabel) == []
        assert not any(
            isinstance(widget, (FigureCanvas, NavigationToolbar, ImagePreviewLabel))
            for widget in app.topLevelWidgets()
        )
        assert window.analyze_current_matrix() is True

    window.close()
    _flush_qt_deferred_deletes(app)
    assert all(pane.preview_mode == "empty" for pane in (window.line_pane, window.polar_pane, window.surface_pane))
    for pane in (window.line_pane, window.polar_pane, window.surface_pane):
        assert pane.findChildren(FigureCanvas) == []
        assert pane.findChildren(NavigationToolbar) == []
        assert pane.findChildren(ImagePreviewLabel) == []
    assert not any(
        isinstance(widget, (FigureCanvas, NavigationToolbar, ImagePreviewLabel))
        for widget in app.topLevelWidgets()
    )


def test_plot_update_methods_return_success_booleans(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    assert window.update_line_plot() is True
    assert window.update_polar_plot() is True
    assert window.update_surface_plot() is True
    window.close()
    app.processEvents()


def test_mode_specific_sampling_controls_are_visible_only_when_relevant(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.line_mode_combo.setCurrentText("Angle in plane")
    assert window.line_plane_label.isHidden() is False
    assert window.line_plane_combo.isHidden() is False
    assert window.line_path_label.isHidden() is True
    assert window.path_edit.isHidden() is True

    window.line_mode_combo.setCurrentText("High-symmetry path")
    assert window.line_plane_label.isHidden() is True
    assert window.line_plane_combo.isHidden() is True
    assert window.line_path_label.isHidden() is True
    assert window.path_edit.isHidden() is True

    window.line_mode_combo.setCurrentText("Custom path")
    assert window.line_plane_label.isHidden() is True
    assert window.line_plane_combo.isHidden() is True
    assert window.line_path_label.isHidden() is False
    assert window.path_edit.isHidden() is False

    window.polar_plane_combo.setCurrentText("xy")
    assert window.polar_normal_label.isHidden() is True
    assert window.normal_edit.isHidden() is True
    window.polar_plane_combo.setCurrentText("custom normal")
    assert window.polar_normal_label.isHidden() is False
    assert window.normal_edit.isHidden() is False

    window.close()
    app.processEvents()


def test_closing_window_clears_matplotlib_previews(qtbot=None):
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from crystal_elastic_workbench.gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.theta_spin.setValue(7)
    window.phi_spin.setValue(13)
    assert window.analyze_current_matrix() is True
    assert window.line_pane.preview_mode == "figure"
    assert window.polar_pane.preview_mode == "figure"
    window.close()
    app.processEvents()
    assert window.line_pane.preview_mode == "empty"
    assert window.polar_pane.preview_mode == "empty"
    assert window.surface_pane.preview_mode == "empty"
