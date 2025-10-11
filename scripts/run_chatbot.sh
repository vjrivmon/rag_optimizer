#!/bin/bash

# Script de Lanzamiento - Chatbot RAG Interactivo
# ===============================================

echo "🤖 Iniciando Chatbot RAG Interactivo..."
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar dependencias
echo "🔍 Verificando dependencias..."
python3 -c "import fastapi, uvicorn, websockets, yaml" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Faltan dependencias. Instalando..."
    pip install fastapi uvicorn websockets pyyaml python-multipart aiofiles
    echo ""
fi

# Verificar estructura de directorios
if [ ! -d "interface/chatbot" ]; then
    echo "❌ Error: Directorio interface/chatbot no encontrado"
    echo "   Asegúrate de ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Mensaje de información
echo ""
echo "================================================================================
"
echo "🚀 CHATBOT RAG INTERACTIVO"
echo "================================================================================
"
echo ""
echo "El servidor se iniciará en:"
echo "   → http://localhost:8000"
echo ""
echo "Características:"
echo "   • 4 modelos LLM individuales (Gemma, Llama, Qwen, DeepSeek)"
echo "   • 4 estrategias ensemble (Voting, Weighted, Routing, Consensus)"
echo "   • Streaming de estados en tiempo real"
echo "   • Citación de fuentes"
echo "   • Interfaz mobile-first"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""
echo "================================================================================
"
echo ""

# Lanzar servidor FastAPI
cd interface/chatbot/backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

