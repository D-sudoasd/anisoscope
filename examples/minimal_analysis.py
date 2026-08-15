"""Run a compact, reproducible AnisoScope analysis with a synthetic tensor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from crystal_elastic_workbench import ElasticTensor, check_stability
from crystal_elastic_workbench.exporting import export_analysis_package
from crystal_elastic_workbench.sampling import sample_plane


def isotropic_stiffness_matrix(bulk_gpa: float, shear_gpa: float) -> np.ndarray:
    """Return the cubic Voigt matrix for an isotropic elastic solid."""

    c11 = bulk_gpa + 4.0 * shear_gpa / 3.0
    c12 = bulk_gpa - 2.0 * shear_gpa / 3.0
    return np.array(
        [
            [c11, c12, c12, 0.0, 0.0, 0.0],
            [c12, c11, c12, 0.0, 0.0, 0.0],
            [c12, c12, c11, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, shear_gpa, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, shear_gpa, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, shear_gpa],
        ],
        dtype=float,
    )


def run(output_dir: Path) -> dict[str, object]:
    """Execute the example and return a JSON-serializable summary."""

    bulk_gpa = 140.0
    shear_gpa = 60.0
    tensor = ElasticTensor(
        isotropic_stiffness_matrix(bulk_gpa, shear_gpa),
        crystal_system="cubic",
        unit="GPa",
        material_name="Synthetic isotropic example",
    )
    stability = check_stability(tensor.stiffness_matrix, crystal_system="cubic")
    summary = tensor.polycrystalline_summary()
    plane = sample_plane(tensor, property_name="young", plane="xy", angle_count=37)
    manifest = export_analysis_package(
        tensor,
        output_dir,
        plane_angle_count=37,
        sphere_theta_count=7,
        sphere_phi_count=13,
    )

    result = {
        "material_name": tensor.material_name,
        "stable": stability.overall_stable,
        "bulk_hill_gpa": summary.bulk_hill_gpa,
        "shear_hill_gpa": summary.shear_hill_gpa,
        "young_hill_gpa": summary.young_hill_gpa,
        "plane_young_min_gpa": plane.min_value,
        "plane_young_max_gpa": plane.max_value,
        "manifest": str(manifest.resolve()),
    }
    (output_dir / "example_summary.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/minimal-example"),
        help="Dedicated output directory (default: outputs/minimal-example).",
    )
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
