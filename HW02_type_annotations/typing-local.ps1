Write-Host "Running type checking with mypy (local installation)..." -ForegroundColor Green

# Проверяем, установлен ли Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Python not found. Please install Python 3.11 or later." -ForegroundColor Red
    exit 1
}

# Проверяем, установлен ли mypy
try {
    $mypyVersion = mypy --version 2>&1
    Write-Host "Found mypy: $mypyVersion" -ForegroundColor Yellow
} catch {
    Write-Host "mypy not found. Installing mypy..." -ForegroundColor Yellow
    pip install mypy==1.16.1
}

# Запускаем проверку типов
try {
    mypy basic/ intermediate/
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