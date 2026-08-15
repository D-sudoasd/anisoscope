@echo off
setlocal

cd /d "%~dp0"
set "APP_NAME=AnisoScope"
set "QT_API=pyside6"
set "PYTHON_CMD="

for %%V in (3.13 3.12 3.11) do (
    if not defined PYTHON_CMD (
        py -%%V -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -%%V"
    )
)

if not defined PYTHON_CMD (
    for %%V in (313 312 311) do (
        if not defined PYTHON_CMD if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
            set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        )
    )
)

if not defined PYTHON_CMD (
    python -c "import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] < (3, 14) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo Python 3.11, 3.12, or 3.13 is required.
    exit /b 1
)

if /I "%~1"=="--check" (
    echo Checking %APP_NAME% launcher...
    echo Project directory: %cd%
    %PYTHON_CMD% -c "from PySide6.QtCore import Qt; from crystal_elastic_workbench.gui import MainWindow; import anisoscope; print('GUI import check ok')"
    if errorlevel 1 exit /b 1
    exit /b 0
)

echo Starting %APP_NAME%...
%PYTHON_CMD% -m anisoscope
set "APP_EXIT=%errorlevel%"
if not "%APP_EXIT%"=="0" (
    echo.
    echo %APP_NAME% exited with an error.
    echo Please check that dependencies are installed:
    echo   %PYTHON_CMD% -m pip install -e .
    echo.
    pause
)

exit /b %APP_EXIT%
