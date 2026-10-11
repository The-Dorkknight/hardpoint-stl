@echo off
rem Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
rem Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
rem Hardpoint STL 0.1.0-wip (WORK IN PROGRESS). Double-click to install the FreeCAD workbench and Fusion
rem add-in and check the example files.
cd /d "%~dp0"
where py >nul 2>nul && (py -3 src\install.py) || (where python >nul 2>nul && (python src\install.py) || (echo Python 3 was not found. Install it from python.org and try again.))
echo.
pause
