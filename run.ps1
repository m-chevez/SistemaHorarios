# Script de inicio para Sistema de Horarios
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Iniciando Sistema de Horarios        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectDir = $PSScriptRoot
Set-Location $projectDir

$venvPython = Join-Path $projectDir "venv\Scripts\python.exe"

# 1. Verificar o crear entorno virtual
if (-not (Test-Path $venvPython)) {
    Write-Host "[1/3] Creando entorno virtual (venv)..." -ForegroundColor Yellow
    $basePython = (Get-Command py, python3.12, python -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    if (-not $basePython) {
        $basePython = "C:\Users\DELL\.local\bin\python3.12.exe"
    }
    & $basePython -m venv venv
    Write-Host "  -> Instalando dependencias desde requirements.txt..." -ForegroundColor Yellow
    & $venvPython -m pip install -r requirements.txt
} else {
    Write-Host "[1/3] Entorno virtual detectado." -ForegroundColor Green
}

# 2. Aplicar migraciones pendientes
Write-Host "[2/3] Aplicando migraciones de base de datos..." -ForegroundColor Yellow
& $venvPython manage.py migrate

# 3. Iniciar servidor de desarrollo
Write-Host "[3/3] Levantando servidor Django en http://127.0.0.1:8000/ ..." -ForegroundColor Green
Write-Host "Presiona CTRL + C para detener el servidor." -ForegroundColor DarkGray
& $venvPython manage.py runserver 127.0.0.1:8000

