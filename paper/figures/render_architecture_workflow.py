"""Render the publication figure describing AnisoScope's data flow.

The figure is drawn and exported entirely with Matplotlib.  SVG is the
editable source of record; PDF and PNG are generated from the same figure.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle


HERE = Path(__file__).resolve().parent
SVG = HERE / "architecture_workflow.svg"
PDF = HERE / "architecture_workflow.pdf"
PNG = HERE / "architecture_workflow.png"
WIDTH_MM = 183
HEIGHT_MM = 96
DPI = 450

INK = "#202A30"
MUTED = "#68777D"
RULE = "#9EACB1"
BLUE = "#2F6678"
BLUE_LIGHT = "#E8F0F2"
OCHRE = "#B47B3C"
OCHRE_LIGHT = "#F4EEE5"
WHITE = "#FFFFFF"


def configure_matplotlib() -> None:
    """Use journal-safe fonts and preserve text in vector exports."""

    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7.4,
            "text.color": INK,
            "axes.edgecolor": INK,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": WHITE,
            "savefig.transparent": False,
        }
    )


def label(
    ax: plt.Axes,
    x: float,
    y: float,
    value: str,
    *,
    size: float = 6.5,
    weight: str = "normal",
    color: str = INK,
    ha: str = "left",
    va: str = "center",
    linespacing: float = 1.25,
    style: str = "normal",
    zorder: int = 5,
) -> None:
    ax.text(
        x,
        y,
        value,
        fontsize=size,
        fontweight=weight,
        color=color,
        ha=ha,
        va=va,
        linespacing=linespacing,
        fontstyle=style,
        transform=ax.transAxes,
        zorder=zorder,
    )


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = INK,
    lw: float = 0.9,
    style: str = "-",
    connectionstyle: str = "arc3",
    head: bool = True,
    zorder: int = 2,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle="-|>" if head else "-",
            mutation_scale=7.0,
            linewidth=lw,
            linestyle=style,
            color=color,
            connectionstyle=connectionstyle,
            shrinkA=0,
            shrinkB=0,
            capstyle="round",
            joinstyle="round",
            zorder=zorder,
        )
    )


def matrix_glyph(ax: plt.Axes, x: float, y: float, width: float) -> None:
    """Draw a value-free 6 x 6 matrix schema without implying sparsity."""

    height = width * WIDTH_MM / HEIGHT_MM
    ax.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            transform=ax.transAxes,
            facecolor=WHITE,
            edgecolor=INK,
            linewidth=0.8,
            zorder=3,
        )
    )
    for index in range(1, 6):
        xx = x + width * index / 6
        yy = y + height * index / 6
        ax.add_line(
            Line2D(
                [xx, xx],
                [y, y + height],
                transform=ax.transAxes,
                color=RULE,
                linewidth=0.45,
                zorder=4,
            )
        )
        ax.add_line(
            Line2D(
                [x, x + width],
                [yy, yy],
                transform=ax.transAxes,
                color=RULE,
                linewidth=0.45,
                zorder=4,
            )
        )


def sampling_glyphs(ax: plt.Axes, x: float, y: float) -> None:
    """Draw minimal path, plane and sphere sampling schemas."""

    # Direction path
    ax.plot(
        [x, x + 0.018, x + 0.038, x + 0.058],
        [y, y + 0.020, y - 0.004, y + 0.018],
        color=BLUE,
        linewidth=0.9,
        marker="o",
        markersize=1.8,
        transform=ax.transAxes,
        clip_on=False,
        zorder=4,
    )
    # Plane slice
    px = x + 0.092
    ax.add_patch(
        Rectangle(
            (px, y - 0.008),
            0.043,
            0.043 * WIDTH_MM / HEIGHT_MM,
            angle=-22,
            transform=ax.transAxes,
            facecolor=BLUE_LIGHT,
            edgecolor=BLUE,
            linewidth=0.7,
            zorder=3,
        )
    )
    # Sphere / surface sample
    sx = x + 0.180
    radius = 0.025
    ax.add_patch(
        Circle(
            (sx, y + 0.021),
            radius,
            transform=ax.transAxes,
            facecolor=WHITE,
            edgecolor=BLUE,
            linewidth=0.75,
            zorder=3,
        )
    )
    for dx, dy in [(-0.016, 0.010), (0.0, 0.021), (0.015, 0.031), (0.008, 0.005)]:
        ax.plot(
            sx + dx,
            y + dy,
            marker="o",
            markersize=1.5,
            color=BLUE,
            transform=ax.transAxes,
            zorder=4,
        )


def draw_architecture(ax: plt.Axes) -> None:
    """Panel a: the implemented data dependencies, not GUI call order."""

    label(ax, 0.028, 0.955, "a", size=10.5, weight="bold")
    label(ax, 0.052, 0.955, "Data flow", size=9.5, weight="bold")

    # Supplied input contract
    ax.add_patch(
        Rectangle(
            (0.050, 0.500),
            0.178,
            0.375,
            transform=ax.transAxes,
            facecolor=OCHRE_LIGHT,
            edgecolor="none",
            zorder=0,
        )
    )
    ax.add_patch(
        Rectangle(
            (0.050, 0.858),
            0.178,
            0.017,
            transform=ax.transAxes,
            facecolor=OCHRE,
            edgecolor="none",
            zorder=1,
        )
    )
    label(ax, 0.064, 0.827, "Supplied tensor", size=9.0, weight="bold")
    matrix_glyph(ax, 0.064, 0.585, 0.082)
    label(ax, 0.158, 0.745, "Cij", size=9.5, weight="bold", color=OCHRE)
    label(ax, 0.158, 0.700, "6 × 6 stiffness", size=7.4)
    label(ax, 0.158, 0.655, "GPa", size=7.4)
    label(ax, 0.064, 0.548, "Voigt ordering", size=7.4, color=MUTED)
    label(ax, 0.064, 0.516, "engineering shear", size=7.4, color=MUTED)
    label(ax, 0.064, 0.484, "crystal-system label", size=7.4, color=MUTED)

    # Numerical core
    arrow(ax, (0.228, 0.690), (0.278, 0.690), color=OCHRE, lw=1.0)
    ax.add_patch(
        Rectangle(
            (0.278, 0.575),
            0.154,
            0.230,
            transform=ax.transAxes,
            facecolor=BLUE_LIGHT,
            edgecolor="none",
            zorder=0,
        )
    )
    ax.add_patch(
        Rectangle(
            (0.278, 0.575),
            0.010,
            0.230,
            transform=ax.transAxes,
            facecolor=BLUE,
            edgecolor="none",
            zorder=1,
        )
    )
    label(ax, 0.303, 0.766, "Numerical core", size=7.4, weight="bold", color=BLUE)
    label(ax, 0.303, 0.713, "ElasticTensor", size=9.5, weight="bold")
    label(ax, 0.303, 0.657, "Cij  →  Sij = inv(Cij)", size=7.4)
    label(ax, 0.303, 0.610, "tensor conversion", size=7.4, color=MUTED)

    # Independent stability branch: raw input is inspected, not corrected.
    arrow(
        ax,
        (0.228, 0.823),
        (0.468, 0.823),
        color=MUTED,
        lw=0.75,
        style=(0, (3, 2)),
    )
    label(ax, 0.477, 0.850, "Stability diagnostics", size=8.7, weight="bold")
    label(ax, 0.477, 0.808, "symmetry · invertibility · conditioning", size=7.4)
    label(ax, 0.477, 0.772, "positive definiteness · applicable relations", size=7.4)
    label(ax, 0.477, 0.736, "implemented Born criteria", size=7.4)

    # Scalar branch
    arrow(ax, (0.432, 0.690), (0.468, 0.690), color=BLUE, lw=0.9)
    label(ax, 0.477, 0.690, "Scalar averages", size=8.7, weight="bold")
    label(ax, 0.477, 0.648, "Voigt · Reuss · Hill", size=7.4)

    # Directional branch: sampling helpers evaluate the tensor at requested
    # directions; the two headings describe one operation, not two data types.
    arrow(
        ax,
        (0.432, 0.645),
        (0.468, 0.553),
        color=BLUE,
        lw=0.9,
        connectionstyle="angle3,angleA=0,angleB=-90",
    )
    label(ax, 0.477, 0.568, "Directional properties", size=8.7, weight="bold")
    label(ax, 0.477, 0.525, "Young · compressibility", size=7.4)
    label(ax, 0.477, 0.486, "shear · Poisson ratio", size=7.4)

    arrow(ax, (0.628, 0.548), (0.667, 0.548), color=BLUE, lw=0.9)
    label(ax, 0.675, 0.568, "Evaluate at sampled directions", size=8.1, weight="bold")
    sampling_glyphs(ax, 0.675, 0.504)
    label(ax, 0.675, 0.466, "path", size=7.4, color=MUTED)
    label(ax, 0.765, 0.466, "plane", size=7.4, color=MUTED)
    label(ax, 0.842, 0.466, "sphere", size=7.4, color=MUTED)

    # The three analysis branches converge on the same export boundary.
    arrow(ax, (0.817, 0.805), (0.902, 0.805), color=RULE, lw=0.75)
    arrow(ax, (0.612, 0.690), (0.902, 0.690), color=RULE, lw=0.75)
    arrow(ax, (0.855, 0.548), (0.902, 0.548), color=RULE, lw=0.75)
    ax.add_patch(
        Rectangle(
            (0.902, 0.505),
            0.094,
            0.370,
            transform=ax.transAxes,
            facecolor=WHITE,
            edgecolor=BLUE,
            linewidth=0.8,
            zorder=1,
        )
    )
    label(ax, 0.949, 0.833, "Traceable", size=8.2, weight="bold", ha="center")
    label(ax, 0.949, 0.793, "outputs", size=8.2, weight="bold", ha="center")
    ax.add_line(Line2D([0.917, 0.981], [0.767, 0.767], transform=ax.transAxes, color=RULE, linewidth=0.6))
    label(ax, 0.949, 0.727, "tables", size=7.4, ha="center")
    label(ax, 0.949, 0.685, "sampled data", size=7.4, ha="center")
    label(ax, 0.949, 0.643, "figures", size=7.4, ha="center")
    label(ax, 0.949, 0.601, "animation", size=7.4, ha="center")
    ax.add_patch(
        Rectangle(
            (0.912, 0.530),
            0.074,
            0.038,
            transform=ax.transAxes,
            facecolor=BLUE_LIGHT,
            edgecolor="none",
            zorder=2,
        )
    )
    label(ax, 0.949, 0.549, "manifest", size=7.4, weight="bold", color=BLUE, ha="center")

    # Compact provenance rail under the computational graph.
    ax.add_line(Line2D([0.278, 0.980], [0.398, 0.398], transform=ax.transAxes, color=BLUE, linewidth=0.8))
    label(ax, 0.278, 0.370, "Provenance", size=7.4, weight="bold", color=BLUE)
    label(
        ax,
        0.375,
        0.370,
        "input tensor · unit and convention · sampling · rendering when applicable",
        size=7.4,
        color=MUTED,
    )


def draw_workflow(ax: plt.Axes) -> None:
    """Panel b: the desktop interaction loop, without duplicate module cards."""

    label(ax, 0.028, 0.310, "b", size=10.5, weight="bold")
    label(ax, 0.052, 0.310, "Desktop workflow", size=9.5, weight="bold")

    xs = [0.125, 0.365, 0.605, 0.845]
    stages = [
        ("Enter & confirm", "Cij · unit · convention"),
        ("Analyze", "diagnostics + summaries"),
        ("Sample & inspect", "directional views"),
        ("Export", "data · figures · manifest"),
    ]
    ax.add_line(Line2D([xs[0], xs[-1]], [0.205, 0.205], transform=ax.transAxes, color=RULE, linewidth=0.8, zorder=1))
    for index, (x, (title, detail)) in enumerate(zip(xs, stages, strict=True), start=1):
        ax.add_patch(
            Circle(
                (x, 0.205),
                0.014,
                transform=ax.transAxes,
                facecolor=WHITE,
                edgecolor=BLUE,
                linewidth=0.9,
                zorder=3,
            )
        )
        label(ax, x, 0.205, str(index), size=7.4, weight="bold", color=BLUE, ha="center")
        label(ax, x, 0.255, title, size=8.2, weight="bold", ha="center")
        label(ax, x, 0.154, detail, size=7.4, color=MUTED, ha="center")

    ax.add_line(Line2D([0.050, 0.980], [0.083, 0.083], transform=ax.transAxes, color=RULE, linewidth=0.6))
    label(ax, 0.050, 0.050, "Scope", size=7.4, weight="bold", color=OCHRE)
    label(
        ax,
        0.100,
        0.050,
        "Input provenance and physical applicability remain the researcher's responsibility.",
        size=7.4,
        color=MUTED,
    )


def build_figure() -> plt.Figure:
    configure_matplotlib()
    figure = plt.figure(figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4), facecolor=WHITE)
    axes = figure.add_axes([0, 0, 1, 1])
    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)
    axes.axis("off")
    draw_architecture(axes)
    draw_workflow(axes)
    return figure


def render() -> None:
    figure = build_figure()
    metadata = {
        "Title": "AnisoScope data flow and desktop workflow",
        "Author": "AnisoScope contributors",
        "Subject": "Software architecture and traceable elastic-tensor analysis",
    }
    figure.savefig(SVG, format="svg", metadata={"Title": metadata["Title"]})
    # Matplotlib writes multiline path data with trailing spaces. Normalize the
    # editable SVG so repository whitespace checks remain deterministic.
    svg_text = SVG.read_text(encoding="utf-8")
    SVG.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    figure.savefig(PDF, format="pdf", dpi=DPI, metadata=metadata)
    figure.savefig(PNG, format="png", dpi=DPI, metadata={"Software": "Matplotlib"})
    plt.close(figure)


if __name__ == "__main__":
    render()
    print(
        f"Wrote {SVG.name}, {PDF.name}, and {PNG.name} at "
        f"{WIDTH_MM} mm × {HEIGHT_MM} mm ({DPI} dpi PNG)."
    )
