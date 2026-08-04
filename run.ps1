# Launch HASH-JARVIS
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Virtual environment missing. Run .\setup.ps1 first." -ForegroundColor Yellow
    exit 1
}

# Prefer local Ollama install path when not already on PATH
$ollamaDir = "$env:LOCALAPPDATA\Programs\Ollama"
if (Test-Path "$ollamaDir\ollama.exe") {
    $env:Path = "$ollamaDir;$env:Path"
}

# Best-effort start of Ollama server
try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -UseBasicParsing -TimeoutSec 2
} catch {
    if (Test-Path "$ollamaDir\ollama.exe") {
        Start-Process -FilePath "$ollamaDir\ollama.exe" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }
}

.\.venv\Scripts\python.exe .\main.py
