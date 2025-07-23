Write-Host "Running type checking with mypy..." -ForegroundColor Green

try {
    docker run --rm -v "${PWD}:/app" -w /app python:3.11-slim bash -c "pip install mypy==1.16.1 && mypy basic/ intermediate/"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Type checking passed!" -ForegroundColor Green
    } else {
        Write-Host "Type checking failed!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error running type checking: $_" -ForegroundColor Red
    exit 1
} 