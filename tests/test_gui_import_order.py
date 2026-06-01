import os
import subprocess
import sys


def test_gui_import_initializes_pyside_before_matplotlib_qt_backend():
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from crystal_elastic_workbench.gui import MainWindow; print('gui import ok')",
        ],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "gui import ok" in completed.stdout


def test_anisoscope_module_entrypoint_imports_gui():
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import anisoscope; from anisoscope.__main__ import main; print('anisoscope import ok')",
        ],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "anisoscope import ok" in completed.stdout
