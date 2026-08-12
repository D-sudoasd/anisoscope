from pathlib import Path


def test_readme_documents_merge_gate_relevant_workflows():
    text = Path("README.md").read_text(encoding="utf-8")

    required_sections = [
        "## Install and run",
        "## Detailed installation and launch",
        "## GUI Workflow",
        "## Cij Input Convention",
        "## Exported Files",
        "## 3D Rendering and Palettes",
        "## Testing",
        "## Known Limits",
    ]
    for section in required_sections:
        assert section in text
    assert text.startswith("# AnisoScope")
    assert "python -m anisoscope" in text
    assert ".\\start_anisoscope.bat" in text
    assert "python -m pytest -q" in text
    assert "Voigt order" in text
    assert "sidecar" in text
    assert "paper/figures/anisoscope_interface.png" in text
    assert "0.1.0` release candidate" in text
    assert "actions/workflows/tests.yml/badge.svg" in text
    assert "\ufffd" not in text
