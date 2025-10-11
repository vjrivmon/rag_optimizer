#!/bin/bash

echo "🔧 FIX Y TEST DE P25: Para-Mira-Ayuda"
echo "===================================="
echo ""
echo "Este script:"
echo "  1️⃣  Mejora los chunks del vector store para P25"
echo "  2️⃣  Ejecuta test específico de P25"
echo "  3️⃣  Muestra resultados comparativos"
echo ""
echo "⏱️  Tiempo estimado: 2-3 minutos"
echo ""

cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
source venv/bin/activate

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PASO 1: Mejorar chunking del vector store"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python fix_p25_chunks.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error al mejorar el vector store"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PASO 2: Ejecutar test de P25"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python test_p25_only.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error al ejecutar test"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ FIX Y TEST COMPLETADOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Revisa los resultados arriba"
echo "📁 Archivo JSON guardado en results/"
echo ""
echo "💡 Si el score de P25 es >= 0.80, puedes ejecutar:"
echo "   python benchmark_ensemble.py"
echo ""

