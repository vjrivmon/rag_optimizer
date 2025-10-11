#!/bin/bash

# Script para lanzar el Dashboard Ensemble
# =========================================

echo "🎲 Iniciando Dashboard Ensemble RAG..."
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar dependencias
echo "🔍 Verificando dependencias..."
python3 -c "import streamlit, plotly, pandas, numpy" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Faltan dependencias. Instalando..."
    pip install streamlit plotly pandas numpy
fi

echo ""
echo "🚀 Lanzando dashboard en http://localhost:8501"
echo "   Presiona Ctrl+C para detener"
echo ""

# Lanzar Streamlit
streamlit run interface/app_ensemble.py

