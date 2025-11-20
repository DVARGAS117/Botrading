# Script para limpiar cache de Python
# Útil cuando haces cambios en el código y Python no los refleja

Write-Host "🧹 Limpiando cache de Python..." -ForegroundColor Cyan

# Eliminar todos los directorios __pycache__
$pycacheDirs = Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue
$count = $pycacheDirs.Count

if ($count -gt 0) {
    $pycacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Eliminados $count directorios __pycache__" -ForegroundColor Green
} else {
    Write-Host "✅ No hay cache para limpiar" -ForegroundColor Green
}

# Eliminar archivos .pyc sueltos
$pycFiles = Get-ChildItem -Path . -Recurse -Filter *.pyc -ErrorAction SilentlyContinue
$pycCount = $pycFiles.Count

if ($pycCount -gt 0) {
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Eliminados $pycCount archivos .pyc" -ForegroundColor Green
}

Write-Host "🎉 Cache limpiado completamente" -ForegroundColor Green
