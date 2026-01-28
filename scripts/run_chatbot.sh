#!/bin/bash

# Script de Lanzamiento - Chatbot DNI con gemma2:27b
# ==================================================

echo "💙 Iniciando Chatbot DNI..."
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar dependencias
echo "🔍 Verificando dependencias..."
python3 -c "import fastapi, uvicorn, websockets, yaml, langchain, chromadb" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Faltan dependencias. Instalando..."
    pip install fastapi uvicorn websockets pyyaml python-multipart aiofiles langchain langchain-community chromadb
    echo ""
fi

# Verificar estructura de directorios
if [ ! -d "interface/chatbot_dni" ]; then
    echo "❌ Error: Directorio interface/chatbot_dni no encontrado"
    echo "   Asegúrate de ejecutar este script desde la raíz del proyecto"
    exit 1
fi

# Verificar vector store
if [ ! -d "data/vectorstore/chroma_db" ]; then
    echo "⚠️  Advertencia: Vector store no encontrado"
    echo "   Ejecuta: python scripts/02_create_faq_aware_chunks.py"
    echo ""
fi

# Mensaje de información
echo ""
echo "================================================================================"
echo "💙 CHATBOT DNI - Asistente Virtual de Voluntariado"
echo "================================================================================"
echo ""
echo "El servidor se iniciará en:"
echo "   → http://localhost:8000"
echo ""
echo "🎯 Características:"
echo "   • Modelo: gemma2:27b (UPV Ollama)"
echo "   • RAG Avanzado con 343 chunks de documentación"
echo "   • Intent Classification (saludos, despedidas, preguntas)"
echo "   • Streaming de texto en tiempo real"
echo "   • Confidence scores en cada respuesta"
echo "   • Contexto conversacional persistente"
echo "   • Sugerencias de preguntas dinámicas"
echo "   • Sistema de feedback integrado"
echo "   • Exportar conversaciones en TXT"
echo ""
echo "📊 Dataset:"
echo "   • 15 documentos (desayunos, COLES, RESIS, kayak, DANA)"
echo "   • 343 chunks optimizados con FAQ-aware chunking"
echo "   • Embeddings multilingües (español)"
echo ""
echo "🛠️  Componentes activos:"
echo "   ✓ EnhancedRAGEngineNew (hybrid search BM25 + semantic)"
echo "   ✓ ConversationalRAG (contexto por sesión)"
echo "   ✓ IntentClassifier (5 intents)"
echo "   ✓ QuestionSuggester (8 categorías)"
echo "   ✓ FeedbackSystem (JSONL storage)"
echo ""
echo "⚠️  Requisitos:"
echo "   • Conexión a red UPV (o VPN activa)"
echo "   • Puerto 8000 disponible"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""
echo "================================================================================"
echo ""

# Lanzar servidor FastAPI
cd interface/chatbot_dni/backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

