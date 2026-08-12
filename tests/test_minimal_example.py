import importlib.util
from pathlib import Path

import pytest


def test_minimal_example_runs_and_matches_isotropic_limit(tmp_path):
    example_path = Path("examples/minimal_analysis.py")
    spec = importlib.util.spec_from_file_location("minimal_analysis", example_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.run(tmp_path)

    assert result["stable"] is True
    assert result["bulk_hill_gpa"] == pytest.approx(140.0)
    assert result["shear_hill_gpa"] == pytest.approx(60.0)
    assert result["plane_young_min_gpa"] == pytest.approx(result["plane_young_max_gpa"])
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "example_summary.json").is_file()
