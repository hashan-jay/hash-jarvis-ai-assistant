# HASH-JARVIS - Windows setup helper
$ErrorActionPreference = "Stop"

Write-Host "== HASH-JARVIS Setup ==" -ForegroundColor Cyan

# Ensure virtual environment
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    py -m venv .venv
}

Write-Host "Installing Python dependencies..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Ensure Ollama is installed
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    $defaultPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $defaultPath) {
        $env:Path = "$env:LOCALAPPDATA\Programs\Ollama;$env:Path"
        $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    }
}

if (-not $ollama) {
    Write-Host "Ollama not found. Installing via winget..." -ForegroundColor Yellow
    winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    $env:Path = "$env:LOCALAPPDATA\Programs\Ollama;$env:Path"
}

Write-Host "Starting Ollama (if needed)..."
Start-Process -FilePath "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

$defaultModel = "llama3.2:3b"
$embedModel = "nomic-embed-text"
Write-Host "Pulling default chat model: $defaultModel"
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull $defaultModel
Write-Host "Pulling embedding model for memory: $embedModel"
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull $embedModel

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Run the app with:  .\run.ps1"
