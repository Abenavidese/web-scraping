# Script de instalación rápida para análisis de sentimientos
# Quick setup script for sentiment analysis

Write-Host "=== Instalando dependencias para análisis de sentimientos ===" -ForegroundColor Cyan
Write-Host ""

# Instalar google-generativeai
Write-Host "Instalando Google Gemini SDK..." -ForegroundColor Yellow
pip install google-generativeai

Write-Host ""
Write-Host "✅ Instalación completada!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Obtén tu API key gratis en: https://aistudio.google.com/app/apikey"
Write-Host "2. Configura la variable de entorno:"
Write-Host "   `$env:GEMINI_API_KEY=`"tu_api_key_aqui`"" -ForegroundColor Yellow
Write-Host "3. Ejecuta el scraper:"
Write-Host "   python main.py --query `"tu_busqueda`" --posts 10 --comments 5" -ForegroundColor Yellow
Write-Host ""
