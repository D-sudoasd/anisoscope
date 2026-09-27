"""Reproducible publication graphics; no experimental measurements are synthesized."""

from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

INK = "#142C3D"
MUTED = "#516570"
RULE = "#CCD7DC"
ACCENT = "#087F8C"
LIGHT = "#EFF7F8"
WARM = "#B86B20"


def style():
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": RULE,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.5,
            "svg.fonttype": "none",
            "svg.hashsalt": "publication-20260927",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def canvas(height=4.6):
    fig = plt.figure(figsize=(7.2, height), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    return fig, ax


def label(ax, x, y, text, size=10, weight="normal", color=INK, ha="left", va="center"):
    return ax.text(
        x,
        y,
        text,
        fontsize=size,
        fontweight=weight,
        color=color,
        ha=ha,
        va=va,
        linespacing=1.45,
    )


def panel(ax, x, y, letter, title):
    label(ax, x, y, letter, 12, "bold", ACCENT)
    label(ax, x + 0.038, y, title, 11, "bold")


def box(ax, x, y, w, h, title, body="", accent=None, face=None, size=9.5):
    accent = ACCENT if accent is None else accent
    face = LIGHT if face is None else face
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=0.012",
            linewidth=0.7,
            edgecolor=RULE,
            facecolor=face,
        )
    )
    ax.plot(
        [x + 0.015, x + 0.015],
        [y + 0.02, y + h - 0.02],
        color=accent,
        lw=2.1,
        solid_capstyle="round",
    )
    label(ax, x + 0.034, y + h - 0.037, title, 10, "bold", accent, va="top")
    if body:
        label(ax, x + 0.034, y + h - 0.099, body, size, va="top")


def arrow(ax, a, b, color=MUTED, style="-"):
    ax.add_patch(
        FancyArrowPatch(
            a,
            b,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1,
            color=color,
            linestyle=style,
            shrinkA=2,
            shrinkB=2,
        )
    )


def save(fig, folder, stem, formats=("png", "svg", "pdf")):
    folder.mkdir(parents=True, exist_ok=True)
    for ext in formats:
        meta = (
            {"Date": None}
            if ext == "svg"
            else ({"CreationDate": None, "ModDate": None} if ext == "pdf" else {})
        )
        fig.savefig(folder / f"{stem}.{ext}", dpi=450, metadata=meta)
    plt.close(fig)


def clean_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=3, width=0.6, color=RULE)
    ax.grid(axis="y", color=RULE, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)


ACCENT = "#655083"
LIGHT = "#F5F2FA"


def main():
    style()
    fig, ax = canvas(5.0)
    panel(ax, 0.035, 0.95, "a", "Tensor input and numerical analysis")
    box(
        ax,
        0.035,
        0.66,
        0.26,
        0.21,
        "Supplied stiffness",
        "6 × 6 Cij in GPa\nVoigt order + shear\nCrystal-system label",
        size=9.2,
    )
    box(
        ax,
        0.36,
        0.66,
        0.27,
        0.21,
        "Numerical core",
        "Compliance: inverse of Cij\nTensor conversion",
        size=9.2,
    )
    box(
        ax,
        0.695,
        0.66,
        0.27,
        0.21,
        "Diagnostics",
        "Symmetry / conditioning\nPositive definiteness\nApplicable Born criteria",
        size=8.9,
    )
    arrow(ax, (0.295, 0.765), (0.36, 0.765), ACCENT)
    # The diagnostic branch inspects the supplied input, independently of inversion.
    ax.plot([0.165, 0.165, 0.83], [0.87, 0.90, 0.90], color=MUTED, lw=0.8, ls="--")
    arrow(ax, (0.83, 0.90), (0.83, 0.87), style="--")
    box(
        ax,
        0.10,
        0.365,
        0.35,
        0.205,
        "Scalar averages",
        "Voigt · Reuss · Hill\nBulk, shear and Young moduli",
        size=9.2,
    )
    box(
        ax,
        0.53,
        0.365,
        0.435,
        0.205,
        "Directional properties",
        "Young · compressibility · shear · Poisson\nSample paths, planes or spheres",
        size=9.2,
    )
    arrow(ax, (0.455, 0.66), (0.275, 0.57), ACCENT)
    arrow(ax, (0.535, 0.66), (0.75, 0.57), ACCENT)
    ax.plot([0.035, 0.965], [0.31, 0.31], color=RULE, lw=0.8)
    panel(ax, 0.035, 0.255, "b", "Inspect and export")
    label(
        ax,
        0.035,
        0.183,
        "Enter → confirm → analyze → inspect → export",
        11,
        "bold",
        ACCENT,
    )
    label(
        ax, 0.035, 0.117, "Tables · sampled data · figures · animation · manifest", 10
    )
    label(
        ax,
        0.035,
        0.059,
        "Record input tensor, units, conventions, sampling and applicable rendering settings.",
        8.9,
        color=MUTED,
    )
    save(fig, Path(__file__).resolve().parent, "architecture_workflow")


if __name__ == "__main__":
    main()
