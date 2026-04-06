@echo off
REM Quick Start Script for Smart Farm Visualization
REM Run this to launch the interactive farm dashboard

echo 🌾 Starting Mini Farm Dashboard...
echo.

REM Check if we're in a virtual environment
if not defined VIRTUAL_ENV (
    echo Activating Python virtual environment...
    call .venv\Scripts\Activate.bat
    if errorlevel 1 (
        echo Warning: Could not activate virtual environment
        echo Continuing with system Python...
    )
)

echo Installing visualization requirements...
pip install -r visualization_requirements.txt >nul 2>&1

echo.
echo 🎮 Choose your visualization:
echo [1] Desktop Application (Interactive Farm with Controls)  
echo [2] Web Dashboard (Beautiful Browser Interface)
echo [3] Both (Desktop + Web)
echo.
set /p choice="Enter your choice (1, 2, or 3): "

if "%choice%"=="1" (
    echo Launching Desktop Farm Visualization...
    python farm_visualization.py
) else if "%choice%"=="2" (
    echo Opening Web Dashboard...
    start farm_dashboard.html
) else if "%choice%"=="3" (
    echo Launching both visualizations...
    start farm_dashboard.html
    python farm_visualization.py
) else (
    echo Invalid choice. Launching web dashboard by default...
    start farm_dashboard.html
)

echo.
echo 🎯 Farm Dashboard launched successfully!
echo.
pause