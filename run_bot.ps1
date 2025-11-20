# Script para ejecutar el bot INTRADAY con configuración correcta
# Uso: .\run_bot.ps1 [--single-cycle] [--save-prompts]

param(
    [switch]$SingleCycle,
    [switch]$SavePrompts
)

Write-Host "🚀 Iniciando Bot INTRADAY..." -ForegroundColor Cyan

# Configurar encoding UTF-8
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Limpiar cache de Python
Write-Host "🧹 Limpiando cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Construir comando
$cmd = "python -m src.bots.strategies.intraday.gemini_3_pro.bot_1.main"
if ($SingleCycle) {
    $cmd += " --single-cycle"
}
if ($SavePrompts) {
    $cmd += " --save-prompts"
}

Write-Host "▶️  Ejecutando: $cmd" -ForegroundColor Green
Write-Host ""

# Ejecutar bot
Invoke-Expression $cmd
