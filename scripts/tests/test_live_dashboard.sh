#!/bin/bash
# Script de prueba para verificar el dashboard en vivo con una sola pregunta

echo "=========================================="
echo "🧪 Test de Dashboard en Tiempo Real"
echo "=========================================="
echo ""
echo "Este script ejecutará:"
echo "1. Dashboard en segundo plano (puerto 8000)"
echo "2. Benchmark con 1 pregunta para verificar streaming"
echo ""
echo "Presiona Ctrl+C cuando termines de verificar"
echo ""

# Iniciar dashboard en background
echo "📊 Iniciando dashboard..."
python dashboard_v2.py &
DASHBOARD_PID=$!

# Esperar a que el dashboard esté listo
sleep 3

echo ""
echo "✅ Dashboard iniciado en: http://localhost:8000"
echo "   Abre esta URL en tu navegador AHORA"
echo ""
echo "Esperando 5 segundos para que abras el navegador..."
sleep 5

echo ""
echo "🚀 Ejecutando benchmark con 1 pregunta..."
echo "   Observa el dashboard para ver eventos en tiempo real"
echo ""

# Ejecutar benchmark con una sola pregunta (solo fase de generación para test rápido)
python benchmark_v2.py --phase generation --max-questions 1

echo ""
echo "✅ Test completado"
echo ""
echo "Presiona Ctrl+C para cerrar el dashboard"
echo "(PID del dashboard: $DASHBOARD_PID)"

# Esperar a que el usuario termine
wait $DASHBOARD_PID

