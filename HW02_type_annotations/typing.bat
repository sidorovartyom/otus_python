@echo off
echo Running type checking with mypy...
docker run --rm -v %cd%:/app -w /app python:3.11-slim bash -c "pip install mypy==1.16.1 && mypy basic/ intermediate/"
if %errorlevel% equ 0 (
    echo Type checking passed!
) else (
    echo Type checking failed!
    exit /b 1
) 