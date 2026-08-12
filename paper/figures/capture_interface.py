"""Capture the bundled Si-cubic regression state from the real Qt interface."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "anisoscope_interface.png"
METADATA = HERE / "anisoscope_interface.capture.json"
FINAL_WIDTH_MM = 183
FINAL_WIDTH_PX = 2400
DPI = round(FINAL_WIDTH_PX / (FINAL_WIDTH_MM / 25.4))
HIGH_DPI_SCALE = 3
LOGICAL_FONT_PX_ESTIMATE = 12
PANEL_A_WIDTH_PX = 800
PANEL_GAP_PX = 54
PANEL_PADDING_PX = 54
PANEL_LABEL_HEIGHT_PX = 64


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["QT_SCALE_FACTOR"] = str(HIGH_DPI_SCALE)
    root = HERE.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from PySide6.QtCore import QCoreApplication, QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
    from PySide6.QtWidgets import QApplication, QGroupBox, QSplitter, QWidget
    from crystal_elastic_workbench.gui import MainWindow

    def grab_physical(widget):
        """Return widget pixels without Qt's device-independent rescaling."""
        captured = widget.grab().toImage().convertToFormat(QImage.Format_ARGB32)
        captured.setDevicePixelRatio(1)
        return captured

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.resize(1200, 720)
    window.show()
    app.processEvents()
    splitter = window.findChild(QSplitter)
    if splitter is None:
        raise RuntimeError("Could not locate the main input/results splitter")
    splitter.setSizes([500, 700])
    app.processEvents()
    window.load_example_by_name("Si cubic")
    window.analyze_current_matrix()
    app.processEvents()
    if window.workflow_status_label.text() != "Checks passed: analysis complete":
        raise RuntimeError(f"Unexpected analysis state: {window.workflow_status_label.text()}")
    if window.material_edit.text() != "Si cubic":
        raise RuntimeError("The bundled Si cubic demonstration did not load")

    window_image = window.grab().toImage().convertToFormat(QImage.Format_ARGB32)
    device_pixel_ratio = window_image.devicePixelRatio()
    if device_pixel_ratio < HIGH_DPI_SCALE:
        raise RuntimeError(f"Expected a {HIGH_DPI_SCALE}x Qt capture; got devicePixelRatio={device_pixel_ratio}")

    groups = window.findChildren(QGroupBox)
    input_group = next(group for group in groups if group.title() == "Input")
    matrix_group = next(group for group in groups if group.title() == "Cij Matrix")
    input_group_image = grab_physical(input_group)
    matrix_group_image = grab_physical(matrix_group)
    status_image = grab_physical(window.dashboard_stability_banner)
    metric_card_images = [
        grab_physical(card) for card in window.findChildren(QWidget, "metricCard")
    ]
    if len(metric_card_images) != 4:
        raise RuntimeError(f"Expected four dashboard metric cards; found {len(metric_card_images)}")

    # Scientific values and interface labels below are copied from real high-DPI
    # Qt widgets. Only panel letters, card backgrounds, and spacing are drawn.
    input_scaled = input_group_image.scaledToWidth(
        PANEL_A_WIDTH_PX, Qt.SmoothTransformation
    )
    matrix_scaled = matrix_group_image.scaledToWidth(
        PANEL_A_WIDTH_PX, Qt.SmoothTransformation
    )
    content_height = input_scaled.height() + PANEL_PADDING_PX + matrix_scaled.height()
    image_height = PANEL_LABEL_HEIGHT_PX + content_height
    dashboard_x = PANEL_A_WIDTH_PX + PANEL_GAP_PX
    dashboard_width = FINAL_WIDTH_PX - dashboard_x
    image = QImage(FINAL_WIDTH_PX, image_height, QImage.Format_ARGB32)
    image.fill("white")
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    panel_font = QFont("Arial", 28, QFont.Bold)
    painter.setFont(panel_font)
    painter.setPen(QColor("#183B56"))
    painter.drawText(8, 42, "a")
    painter.drawText(dashboard_x + 8, 42, "b")

    top = PANEL_LABEL_HEIGHT_PX
    painter.drawImage(0, top, input_scaled)
    painter.drawImage(0, top + input_scaled.height() + PANEL_PADDING_PX, matrix_scaled)
    status_crop = status_image.copy(
        0,
        0,
        min(dashboard_width, status_image.width()),
        status_image.height(),
    )
    painter.drawImage(dashboard_x, top, status_crop)

    card_gap = PANEL_PADDING_PX
    card_width = (dashboard_width - card_gap) // 2
    card_height = 300
    card_top = top + status_crop.height() + PANEL_PADDING_PX
    painter.setPen(QPen(QColor("#AFC3CD"), 2))
    for index, card_image in enumerate(metric_card_images):
        row, column = divmod(index, 2)
        x = dashboard_x + column * (card_width + card_gap)
        y = card_top + row * (card_height + card_gap)
        rect = QRectF(x, y, card_width, card_height)
        painter.setBrush(QColor("#F7FAFC"))
        painter.drawRoundedRect(rect, 12, 12)
        source = card_image.copy(
            0,
            0,
            min(card_image.width(), card_width - 40),
            min(card_image.height(), card_height - 40),
        )
        painter.drawImage(x + 20, y + 20, source)
    painter.end()
    image.setDotsPerMeterX(round(DPI / 0.0254))
    image.setDotsPerMeterY(round(DPI / 0.0254))
    if not image.save(str(OUTPUT)):
        raise RuntimeError(f"Could not write {OUTPUT}")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    METADATA.write_text(json.dumps({
        "capture_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "paper/figures/capture_interface.py",
        "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
        "window_logical_pixels": [window.width(), window.height()],
        "window_physical_pixels": [window_image.width(), window_image.height()],
        "device_pixel_ratio": device_pixel_ratio,
        "image_pixels": [image.width(), image.height()],
        "source_widgets": {
            "input_group_pixels": [input_group_image.width(), input_group_image.height()],
            "matrix_group_pixels": [matrix_group_image.width(), matrix_group_image.height()],
            "dashboard_status_pixels": [status_image.width(), status_image.height()],
            "dashboard_metric_card_pixels": [
                [card.width(), card.height()] for card in metric_card_images
            ],
        },
        "composition": {
            "panel_a": "real Input and Cij Matrix group captures; uniformly scaled to the compact panel width",
            "panel_b": "real dashboard status and four metric-card widget captures arranged in a 2x2 grid",
            "panel_gap_px": PANEL_GAP_PX,
            "dashboard_padding_px": PANEL_PADDING_PX,
            "panel_letters": "layout annotations drawn by QPainter; all scientific labels and values come from Qt widgets",
            "metric_layout": "2x2 with neutral card backgrounds",
            "metric_cell_processing": "top-left content crop from each complete real widget; no values or labels redrawn",
            "panel_a_scale": PANEL_A_WIDTH_PX / input_group_image.width(),
        },
        "final_width_mm": FINAL_WIDTH_MM,
        "logical_font_px_estimate": LOGICAL_FONT_PX_ESTIMATE,
        "physical_font_px_estimate_before_panel_scaling": LOGICAL_FONT_PX_ESTIMATE * device_pixel_ratio,
        "final_font_pt_estimate": (
            LOGICAL_FONT_PX_ESTIMATE
            * device_pixel_ratio
            * (PANEL_A_WIDTH_PX / input_group_image.width())
            / image.width()
            * FINAL_WIDTH_MM
            / 25.4
            * 72
        ),
        "font_estimate_formula": "physical_px / output_width_px * final_width_mm / 25.4 * 72",
        "png_dpi": DPI,
        "example": "Si cubic",
        "stiffness_gpa": {"C11": 165.7, "C12": 63.9, "C44": 79.6},
        "workflow_status": window.workflow_status_label.text(),
        "sha256": digest,
        "note": "All content is from real Qt widgets. The real GUI includes a dynamic Last analysis timestamp; the capture time is recorded here.",
    }, indent=2) + "\n", encoding="utf-8")
    window.close()
    QCoreApplication.processEvents()
    print(f"Wrote {OUTPUT.name} ({image.width()}×{image.height()} px) and {METADATA.name}; sha256={digest}")


if __name__ == "__main__":
    main()
