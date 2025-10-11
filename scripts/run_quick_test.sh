#!/bin/bash

echo "🧪 TEST RÁPIDO - Benchmark Ensemble"
echo "=================================="
echo ""
echo "Probando con 3 preguntas conflictivas:"
echo "  - P11 (COLES): Fallo crítico histórico"
echo "  - P20 (RESIS ubicación): Fallo crítico histórico"
echo "  - P25 (Para-Mira-Ayuda): Fallo filosófico universal"
echo ""
echo "⏱️  Tiempo estimado: 5-8 minutos"
echo ""

cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
source venv/bin/activate

python test_ensemble_quick.py

echo ""
echo "✅ Test completado"

