from pathlib import Path
import tomllib

import anisoscope
import crystal_elastic_workbench


def test_public_and_distribution_versions_match():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    distribution_version = metadata["project"]["version"]

    assert anisoscope.__version__ == distribution_version
    assert crystal_elastic_workbench.__version__ == distribution_version


def test_project_urls_use_the_canonical_repository():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    urls = metadata["project"]["urls"]

    assert urls["Repository"] == "https://github.com/D-sudoasd/anisoscope"
    assert urls["Issues"] == "https://github.com/D-sudoasd/anisoscope/issues"
