@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON=py -3"
) else (
  set "PYTHON=python"
)
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto failure
%PYTHON% fractal_portal.py --preset aurora --output fractal_aurora.png
if errorlevel 1 goto failure
%PYTHON% fractal_portal.py --preset ember --output fractal_ember.png
if errorlevel 1 goto failure
%PYTHON% -m unittest -v test_fractal
if errorlevel 1 goto failure
echo.
echo Success! Open fractal_aurora.png and fractal_ember.png.
pause
exit /b 0
:failure
echo.
echo ERROR: See the messages above.
pause
exit /b 1
