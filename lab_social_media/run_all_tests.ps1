
# Script para Ejecución Automática de Pruebas de Rendimiento
# -------------------------------------------------------------
Write-Host "🚀 INICIANDO SUITE DE PRUEBAS AUTOMÁTICAS PARA LAB SOCIAL MEDIA" -ForegroundColor Green
Write-Host "================================================================"

# Definir parámetros de prueba
$Query = "Computacion Paralela"
$Posts = 3
$Comments = 2

# Verificar directorio correct
if (-not (Test-Path "master_scraper.py")) {
    Write-Host "⚠️  No se encontró master_scraper.py. Cambiando directorio..." -ForegroundColor Yellow
    Set-Location "c:\Users\EleXc\Music\limpieza_scratching\lab_social_media"
}

# 1. Ejecutar Comparación de Rendimiento (Secuencial vs Paralelo)
Write-Host "`n[TEST 1] Ejecutando Benchmark Completo (Secuencial vs Paralelo)..." -ForegroundColor Cyan
python master_scraper.py --compare --query "$Query" --posts $Posts --comments $Comments

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ [TEST 1] COMPLETADO EXITOSAMENTE" -ForegroundColor Green
} else {
    Write-Host "`n❌ [TEST 1] FALLÓ CON CÓDIGO DE SALIDA $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

# 2. Verificar que se generó la muestra de validación
Write-Host "`n[TEST 2] Verificando generación de archivos de log..." -ForegroundColor Cyan
$ValidationFile = Get-ChildItem logs/validation_sample_*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($ValidationFile) {
    Write-Host "✅ Muestra de validación encontrada: $($ValidationFile.Name)" -ForegroundColor Green
} else {
    Write-Host "❌ No se encontró archivo de validación en logs/" -ForegroundColor Red
}

$MetricsFile = Get-ChildItem logs/metrics_report_*.txt | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($MetricsFile) {
    Write-Host "✅ Reporte de métricas encontrado: $($MetricsFile.Name)" -ForegroundColor Green
} else {
    Write-Host "❌ No se encontró reporte de métricas" -ForegroundColor Red
}

Write-Host "`n================================================================"
Write-Host "🎉 TODAS LAS PRUEBAS FINALIZADAS" -ForegroundColor Green
Write-Host "Presione Enter para salir..."
Read-Host
