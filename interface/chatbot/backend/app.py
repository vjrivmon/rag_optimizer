"""
FastAPI Backend - Chatbot RAG Interactivo
=========================================

Servidor backend que maneja:
- Carga de modelos LLM
- Inicialización de engines RAG y Ensemble
- Endpoints REST y WebSocket
- Streaming de estados de procesamiento
"""

import sys
import os
from pathlib import Path

# Añadir path del proyecto al PYTHONPATH
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

# Imports del proyecto
from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.ensemble.ensemble_engine import EnsembleRAGEngine

# Imports locales
from model_profiles import get_all_profiles
from chat_handler import InteractiveChatHandler


# ============================================================================
# CONFIGURACIÓN DE LA APP
# ============================================================================

app = FastAPI(
    title="Chatbot RAG Interactivo",
    description="Sistema de chatbot con múltiples modelos LLM y estrategias ensemble",
    version="1.0.0"
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")


# ============================================================================
# ESTADO GLOBAL
# ============================================================================

class AppState:
    """Estado global de la aplicación"""
    def __init__(self):
        self.models = {}
        self.rag_engines = {}
        self.ensemble_engine = None
        self.chat_handler = None
        self.server_status = "disconnected"

state = AppState()


# ============================================================================
# INICIALIZACIÓN DE MODELOS
# ============================================================================

def load_models_config():
    """Carga configuración de modelos desde YAML"""
    config_path = project_root / "config" / "models_config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config['models']


def check_server_connectivity():
    """Verifica conectividad con servidor UPV"""
    try:
        import requests
        import warnings
        from urllib3.exceptions import InsecureRequestWarning
        
        # Suprimir warnings de HTTPS sin verificar
        warnings.filterwarnings('ignore', category=InsecureRequestWarning)
        
        endpoint = "https://ollama.gti-ia.upv.es:443/api/generate"
        
        # Timeout más largo (15s) para conexiones SSH/VPN
        response = requests.post(
            endpoint,
            json={"model": "gemma2:27b", "prompt": "test", "stream": False},
            timeout=15,
            verify=False
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error conectando al servidor UPV: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Inicializa modelos y engines al arrancar"""
    print("\n" + "="*80)
    print("🚀 INICIANDO CHATBOT RAG INTERACTIVO")
    print("="*80 + "\n")
    
    # Verificar conectividad
    print("📡 Verificando conectividad con servidor UPV...")
    is_connected = check_server_connectivity()
    
    if is_connected:
        state.server_status = "connected"
        print("✅ Servidor UPV ONLINE - Conectado correctamente\n")
    else:
        state.server_status = "offline"
        print("❌ Servidor UPV OFFLINE - Sin conexión\n")
        print("⚠️  NOTA: Los modelos NO funcionarán sin conexión al servidor\n")
    
    # Cargar configuración
    print("📂 Cargando configuración de modelos...")
    models_config = load_models_config()
    print(f"   ✓ {len(models_config)} modelos configurados\n")
    
    # Inicializar modelos
    print("🤖 Inicializando modelos LLM...")
    
    DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"
    VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"
    
    for config in models_config:
        model_name = config['name']
        print(f"   • Cargando {model_name}...")
        
        try:
            # Crear wrapper del modelo
            model = LLMWrapper(
                model_name=model_name,
                api_endpoint=DEFAULT_API_ENDPOINT
            )
            state.models[model_name] = model
            
            # Crear RAG engine para el modelo
            rag_engine = EnhancedRAGEngineNew(
                vector_store_path=str(VECTOR_STORE_PATH),
                model=model
            )
            state.rag_engines[model_name] = rag_engine
            
            print(f"     ✓ {model_name} listo")
            
        except Exception as e:
            print(f"     ✗ Error cargando {model_name}: {e}")
    
    print(f"\n✅ {len(state.rag_engines)} modelos inicializados correctamente\n")
    
    # Inicializar Ensemble Engine
    print("🎲 Inicializando Ensemble Engine...")
    
    try:
        state.ensemble_engine = EnsembleRAGEngine(
            rag_engines=state.rag_engines,
            enabled_strategies=['voting', 'weighted', 'routing', 'consensus']
        )
        print("   ✓ Ensemble Engine listo\n")
    except Exception as e:
        print(f"   ✗ Error inicializando Ensemble: {e}\n")
    
    # Inicializar Chat Handler
    print("💬 Inicializando Chat Handler...")
    
    try:
        state.chat_handler = InteractiveChatHandler(
            ensemble_engine=state.ensemble_engine,
            rag_engines=state.rag_engines
        )
        print("   ✓ Chat Handler listo\n")
    except Exception as e:
        print(f"   ✗ Error inicializando Chat Handler: {e}\n")
    
    print("="*80)
    print("✅ SISTEMA LISTO - Servidor disponible en http://localhost:8000")
    print("="*80 + "\n")


# ============================================================================
# ENDPOINTS REST
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Sirve la página principal del chatbot"""
    index_path = frontend_path / "templates" / "index.html"
    
    if not index_path.exists():
        return HTMLResponse(
            content="<h1>Error: index.html not found</h1>",
            status_code=404
        )
    
    with open(index_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.get("/api/models")
async def get_models():
    """
    Retorna perfiles de todos los modelos y estrategias disponibles.
    
    Returns:
        Dict con perfiles completos (pros, contras, scores, etc.)
    """
    profiles = get_all_profiles()
    
    return {
        "server_status": state.server_status,
        "models": profiles
    }


@app.get("/api/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "server_status": state.server_status,
        "models_loaded": len(state.rag_engines),
        "ensemble_ready": state.ensemble_engine is not None
    }


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket para chat interactivo con streaming de estados.
    
    Recibe: {"question": str, "model": str}
    Envía:
        - {"type": "status", "status": str} - Estados intermedios
        - {"type": "complete", "response": {...}} - Respuesta final
        - {"type": "error", "error": str} - Error
    """
    await websocket.accept()
    
    try:
        # Recibir pregunta del cliente
        data = await websocket.receive_json()
        
        question = data.get('question', '')
        model = data.get('model', 'gemma2:27b')
        
        if not question:
            await websocket.send_json({
                "type": "error",
                "error": "Pregunta vacía"
            })
            await websocket.close()
            return
        
        # Procesar pregunta con chat handler
        response = await state.chat_handler.process_question(
            question=question,
            selected_option=model,
            websocket=websocket
        )
        
        # Enviar respuesta completa
        await websocket.send_json({
            "type": "complete",
            "response": response
        })
        
    except WebSocketDisconnect:
        print("   🔌 Cliente desconectado")
    
    except Exception as e:
        print(f"   ❌ Error en WebSocket: {e}")
        
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
    
    finally:
        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

