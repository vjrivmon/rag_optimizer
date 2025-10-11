#!/bin/bash
#
# 🚀 RAG Optimizer Dashboard v3 - Script de Ejecución Rápida
#
# Uso:
#   ./run_dashboard_v3.sh
#
# O si no tiene permisos:
#   bash run_dashboard_v3.sh
#

echo "🚀 Iniciando RAG Optimizer Dashboard v3..."
echo ""
echo "📊 Dashboard Profesional para Evaluación RAG"
echo "   - Análisis Cualitativo y Cuantitativo"
echo "   - Comparación con Respuestas Esperadas"
echo "   - Métricas RAGAs Explicadas"
echo "   - Exportación Profesional"
echo ""
echo "⏳ Iniciando Streamlit..."
echo ""

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source venv/bin/activate
fi

# Ejecutar Streamlit
streamlit run interface/app_v3.py

# Desactivar entorno virtual al salir
if [ -d "venv" ]; then
    deactivate
fi

