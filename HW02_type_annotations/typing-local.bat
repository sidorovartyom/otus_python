@echo off
echo Running type checking with mypy (local installation)...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.11 or later.
    exit /b 1
)

REM Check if mypy is installed
mypy --version >nul 2>&1
if errorlevel 1 (
    echo mypy not found. Installing mypy...
    pip install mypy==1.16.1
)

REM Run type checking
mypy basic/ intermediate/
if errorlevel 1 (
    echo Type checking failed!
    exit /b 1
) else (
    echo Type checking passed!
) 