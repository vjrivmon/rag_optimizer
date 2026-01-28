"""
Chatbot DNI - Backend FastAPI
==============================

Backend simplificado para chatbot con gemma2:27b únicamente.
Integra todos los componentes avanzados del sistema RAG.

Características:
- Solo gemma2:27b (sin ensemble)
- Intent Classifier para mensajes genéricos
- Confidence scores en todas las respuestas
- Feedback system para mejora continua
- Conversational RAG con persistencia de contexto
- Question Suggester para sugerencias dinámicas
- WebSocket para streaming en tiempo real
"""

import sys
import os
from pathlib import Path

# Añadir path del proyecto al PYTHONPATH
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Imports del proyecto
from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.core.intent_classifier import IntentClassifier
from src.core.feedback_system import FeedbackSystem
from src.core.conversational_rag import ConversationalRAGEngine
from src.core.question_suggester import QuestionSuggester

# Security SDK
from vicente_rag.security import InjectionDetector, Sanitizer, RiskScorer


# ============================================================================
# CONFIGURACIÓN DE LA APP
# ============================================================================

app = FastAPI(
    title="Chatbot DNI - gemma2:27b",
    description="Chatbot inteligente con RAG avanzado para DNI Voluntariado",
    version="3.0.0"
)

# CORS - restricted origins
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Security middleware - headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Montar archivos estáticos
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request para enviar feedback"""
    session_id: str
    question: str
    answer: str
    feedback_type: str  # 'positive' o 'negative'
    rating: Optional[int] = None
    confidence: Optional[float] = None
    response_time_ms: Optional[int] = None
    response_id: Optional[str] = None


# ============================================================================
# ESTADO GLOBAL
# ============================================================================

class AppState:
    """Estado global de la aplicación"""
    def __init__(self):
        self.model = None
        self.rag_engine = None
        self.conversational_rag = None
        self.intent_classifier = None
        self.feedback_system = None
        self.question_suggester = None
        self.server_status = "disconnected"
        # Security
        self.injection_detector = InjectionDetector()
        self.sanitizer = Sanitizer(max_length=5000)
        self.risk_scorer = RiskScorer()
        self.question_counter = 0

state = AppState()


# ============================================================================
# INICIALIZACIÓN
# ============================================================================

def check_server_connectivity():
    """Verifica conectividad con servidor UPV"""
    try:
        import requests
        import warnings
        from urllib3.exceptions import InsecureRequestWarning
        
        warnings.filterwarnings('ignore', category=InsecureRequestWarning)
        
        endpoint = "https://ollama.gti-ia.upv.es:443/api/generate"
        
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
    """Inicializa el sistema al arrancar"""
    print("\n" + "="*80)
    print("🚀 INICIANDO CHATBOT DNI - gemma2:27b")
    print("="*80 + "\n")
    
    # Verificar conectividad
    print("📡 Verificando conectividad con servidor UPV...")
    is_connected = check_server_connectivity()
    
    if is_connected:
        state.server_status = "connected"
        print("✅ Servidor UPV ONLINE\n")
    else:
        state.server_status = "offline"
        print("❌ Servidor UPV OFFLINE\n")
        print("⚠️  NOTA: El chatbot NO funcionará sin conexión\n")
    
    # Inicializar componentes
    print("🤖 Inicializando gemma2:27b...")
    
    DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"
    VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"
    
    try:
        # 1. Modelo LLM
        state.model = LLMWrapper(
            model_name="gemma2:27b",
            api_endpoint=DEFAULT_API_ENDPOINT
        )
        print("   ✓ Modelo gemma2:27b cargado")
        
        # 2. RAG Engine
        state.rag_engine = EnhancedRAGEngineNew(
            vector_store_path=str(VECTOR_STORE_PATH),
            model=state.model
        )
        print("   ✓ Enhanced RAG Engine listo")
        
        # 3. Conversational RAG
        state.conversational_rag = ConversationalRAGEngine(
            base_rag_engine=state.rag_engine,
            model_wrapper=state.model
        )
        print("   ✓ Conversational RAG listo")
        
        # 4. Intent Classifier
        state.intent_classifier = IntentClassifier()
        print("   ✓ Intent Classifier listo")
        
        # 5. Feedback System
        state.feedback_system = FeedbackSystem()
        print("   ✓ Feedback System listo")
        
        # 6. Question Suggester
        state.question_suggester = QuestionSuggester()
        print("   ✓ Question Suggester listo")
        
        print("\n✅ SISTEMA COMPLETO INICIALIZADO")
        
    except Exception as e:
        print(f"\n❌ Error inicializando componentes: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*80)
    print("✅ Servidor disponible en http://localhost:8000")
    print("="*80 + "\n")


# ============================================================================
# ENDPOINTS REST
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Sirve la página principal del chatbot"""
    index_path = frontend_path / "index.html"
    
    if not index_path.exists():
        return HTMLResponse(
            content="<h1>Chatbot DNI</h1><p>Frontend no encontrado. Accede via WebSocket en /ws/chat</p>",
            status_code=200
        )
    
    with open(index_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@app.get("/api/health")
async def health_check():
    """Health check del sistema"""
    return {
        "status": "healthy",
        "server_status": state.server_status,
        "model": "gemma2:27b",
        "components": {
            "model": state.model is not None,
            "rag_engine": state.rag_engine is not None,
            "conversational_rag": state.conversational_rag is not None,
            "intent_classifier": state.intent_classifier is not None,
            "feedback_system": state.feedback_system is not None,
            "question_suggester": state.question_suggester is not None
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/suggest-questions")
async def get_suggested_questions(
    category: Optional[str] = None,
    last_answer: Optional[str] = None
):
    """
    Obtiene sugerencias de preguntas.
    
    Query params:
    - category: Categoría específica (opcional)
    - last_answer: Última respuesta para contexto (opcional)
    """
    if not state.question_suggester:
        raise HTTPException(status_code=503, detail="Question suggester no disponible")
    
    if last_answer:
        suggestions = state.question_suggester.suggest_questions(
            last_answer=last_answer,
            num_suggestions=3
        )
    elif category:
        # Sugerencias por categoría (aleatorias)
        import random
        category_suggestions = state.question_suggester.category_suggestions.get(category, [])
        if category_suggestions:
            # Mezclar y seleccionar 3 aleatorias
            shuffled = category_suggestions.copy()
            random.shuffle(shuffled)
            suggestions = shuffled[:3]
        else:
            # Fallback a genéricas aleatorias
            shuffled_generic = state.question_suggester.generic_suggestions.copy()
            random.shuffle(shuffled_generic)
            suggestions = shuffled_generic[:3]
    else:
        # Sugerencias genéricas aleatorias con mix de categorías
        import random
        all_suggestions = []

        # Recopilar sugerencias de todas las categorías
        for cat_suggestions in state.question_suggester.category_suggestions.values():
            all_suggestions.extend(cat_suggestions)

        # Agregar genéricas
        all_suggestions.extend(state.question_suggester.generic_suggestions)

        # Mezclar y seleccionar 3 únicas
        random.shuffle(all_suggestions)
        suggestions = list(dict.fromkeys(all_suggestions))[:3]  # Eliminar duplicados y tomar 3
    
    return {
        "suggestions": suggestions,
        "count": len(suggestions)
    }


@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Recibe y guarda feedback del usuario"""
    if not state.feedback_system:
        raise HTTPException(status_code=503, detail="Feedback system no disponible")
    
    try:
        success = state.feedback_system.add_feedback(
            session_id=feedback.session_id,
            question=feedback.question,
            answer=feedback.answer,
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            confidence=feedback.confidence,
            response_time_ms=feedback.response_time_ms,
            model_used="gemma2:27b",
            response_id=feedback.response_id
        )
        
        if success:
            return {"status": "success", "message": "Feedback guardado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error guardando feedback")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando feedback: {str(e)}")


@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Obtiene estadísticas de feedback"""
    if not state.feedback_system:
        raise HTTPException(status_code=503, detail="Feedback system no disponible")
    
    stats = state.feedback_system.get_stats()
    return stats


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket para chat interactivo con streaming.
    
    Recibe: {"question": str, "session_id": str}
    Envía:
        - {"type": "status", "status": str} - Estados intermedios
        - {"type": "complete", "response": {...}} - Respuesta final
        - {"type": "error", "error": str} - Error
    """
    await websocket.accept()
    
    # Generar session_id si no se proporciona
    session_id = None
    
    try:
        # Recibir pregunta del cliente
        data = await websocket.receive_json()
        
        raw_question = data.get('question', '').strip()
        session_id = data.get('session_id') or f"session_{uuid.uuid4().hex[:12]}"

        if not raw_question:
            await websocket.send_json({
                "type": "error",
                "error": "Pregunta vacía"
            })
            await websocket.close()
            return

        # --- Security: sanitize input ---
        question = state.sanitizer.sanitize_strict(raw_question)

        # --- Security: detect prompt injection ---
        injection_result = state.injection_detector.detect(question, use_semantic=False)
        if injection_result.is_injection:
            print(f"   🛡️ Injection detected: {injection_result.matched_patterns[:3]}")
            await websocket.send_json({
                "type": "complete",
                "response": {
                    "answer": "Lo siento, no puedo procesar esa solicitud. ¿Puedo ayudarte con algo sobre DNI Voluntariado?",
                    "confidence": 0.0,
                    "response_time_ms": 0,
                    "intent": "blocked",
                    "response_id": f"blocked_{uuid.uuid4().hex[:8]}",
                    "suggestions": [],
                    "sources": [],
                }
            })
            await websocket.close()
            return

        # --- Security: risk scoring (log only, don't block medium) ---
        risk_result = state.risk_scorer.calculate(question)
        if risk_result.level in ("high", "critical"):
            print(f"   ⚠️ High risk input: {risk_result.level} ({risk_result.score:.2f}), factors: {risk_result.factors}")

        state.question_counter += 1
        question_id = state.question_counter
        
        # DEBUG: Ver historial de la sesión
        if hasattr(state.conversational_rag, 'session_store'):
            session_history = state.conversational_rag.session_store.get_session_history(session_id)
            num_messages = len(session_history.messages)
            print(f"\n{'='*80}")
            print(f"📥 NUEVA PREGUNTA #{question_id}")
            print(f"{'='*80}")
            print(f"Sesión: {session_id}")
            print(f"Historial previo: {num_messages} mensajes")
            print(f"Pregunta: {question}")
            print(f"{'='*80}\n")
        else:
            print(f"\n{'='*80}")
            print(f"📥 NUEVA PREGUNTA #{question_id}")
            print(f"{'='*80}")
            print(f"Sesión: {session_id}")
            print(f"Pregunta: {question}")
            print(f"{'='*80}\n")
        
        start_time = time.time()
        
        # Estado: Conectando
        await websocket.send_json({
            "type": "status",
            "status": "connecting",
            "log": "🔄 Conectando con el sistema..."
        })
        await asyncio.sleep(0.3)

        # Clasificar intent
        intent_result = state.intent_classifier.classify(question)
        intent = intent_result.intent

        log_intent = f"🎯 Intent detectado: {intent} (confidence: {intent_result.confidence:.2f})"
        print(f"   {log_intent}")

        await websocket.send_json({
            "type": "log",
            "log": log_intent
        })
        
        # Si es un mensaje genérico, responder directamente
        if intent != 'question' and intent_result.predefined_response:
            print(f"   💬 Respondiendo con mensaje predefinido")
            
            # Estado: Pensando (para dar sensación de procesamiento)
            await websocket.send_json({
                "type": "status",
                "status": "thinking"
            })
            await asyncio.sleep(0.8)  # Delay para simular procesamiento
            
            response_time = time.time() - start_time
            response_id = f"{session_id}_{int(time.time()*1000)}"
            
            # Sugerencias basadas en intent
            suggestions = state.question_suggester.suggest_from_intent(intent)
            
            # Enviar respuesta con streaming para mensajes genéricos también
            answer_text = intent_result.predefined_response
            
            # Simular escritura progresiva
            chunk_size = 40
            for i in range(0, len(answer_text), chunk_size):
                chunk = answer_text[i:i+chunk_size]
                await websocket.send_json({
                    "type": "chunk",
                    "chunk": chunk,
                    "is_final": i + chunk_size >= len(answer_text)
                })
                await asyncio.sleep(0.04)  # 40ms entre chunks
            
            await websocket.send_json({
                "type": "complete",
                "response": {
                    "answer": answer_text,
                    "confidence": intent_result.confidence,
                    "intent": intent,
                    "response_time": round(response_time, 2),
                    "response_id": response_id,
                    "suggestions": suggestions,
                    "sources": []
                }
            })
            
        else:
            # Pregunta compleja - usar RAG conversacional
            log_rag = "🔍 Procesando con RAG conversacional..."
            print(f"   {log_rag}")

            await websocket.send_json({
                "type": "log",
                "log": log_rag
            })

            # Estado: Pensando
            await websocket.send_json({
                "type": "status",
                "status": "thinking",
                "log": "🤔 Analizando tu pregunta..."
            })

            await asyncio.sleep(0.5)

            # Estado: Buscando información
            await websocket.send_json({
                "type": "status",
                "status": "searching",
                "log": "📚 Buscando información relevante..."
            })

            # Procesar con conversational RAG
            result = state.conversational_rag.process_query(
                query=question,
                session_id=session_id,
                question_id=question_id
            )

            # Estado: Generando respuesta
            await websocket.send_json({
                "type": "status",
                "status": "processing",
                "log": "✍️ Generando respuesta..."
            })
            
            response_time = time.time() - start_time
            response_id = f"{session_id}_{int(time.time()*1000)}"

            # ✨ NUEVO: Capturar métricas detalladas
            chunks = result.get('contexts', [])  # Para confidence/alerts (strings)
            raw_chunks = result.get('raw_chunks', chunks)  # Para metadata (objetos Document)
            answer = result.get('answer', '')

            print(f"[DEBUG] result keys: {list(result.keys())}")
            print(f"[DEBUG] 'raw_chunks' in result: {'raw_chunks' in result}")
            print(f"[DEBUG] raw_chunks type: {type(raw_chunks)}")
            if raw_chunks:
                print(f"[DEBUG] raw_chunks[0] type: {type(raw_chunks[0])}")
                if isinstance(raw_chunks[0], dict):
                    print(f"[DEBUG] raw_chunks[0] keys: {list(raw_chunks[0].keys())}")

            # 1. Confidence con breakdown detallado
            confidence_data = None
            confidence = None

            if chunks and hasattr(state.rag_engine, 'calculate_confidence_with_breakdown'):
                confidence_data = state.rag_engine.calculate_confidence_with_breakdown(chunks, answer, question)
                confidence = confidence_data['confidence']
                print(f"   ✅ Confidence con breakdown: {confidence:.3f}")
            else:
                # Fallback al método antiguo
                if 'validation' in result and hasattr(result['validation'], 'confidence'):
                    confidence = result['validation'].confidence
                elif 'confidence' in result:
                    confidence = result['confidence']
                elif chunks and hasattr(state.rag_engine, 'calculate_confidence_score'):
                    confidence = state.rag_engine.calculate_confidence_score(chunks, answer, question)
                else:
                    confidence = 0.5
                print(f"   ✅ Confidence (fallback): {confidence:.3f}")

            # 2. Top 3 chunks con información detallada
            top_chunks_info = []
            if raw_chunks and hasattr(state.rag_engine, 'extract_top_chunks_info'):
                top_chunks_info = state.rag_engine.extract_top_chunks_info(raw_chunks, top_n=3)
                print(f"   📚 Top 3 chunks extraídos con detalles")

            # 3. Contexto conversacional detectado
            context_info = None
            if hasattr(state.conversational_rag, 'context_tracker') and hasattr(state.conversational_rag, 'session_store'):
                try:
                    session_history = state.conversational_rag.session_store.get_session_history(session_id)
                    messages = session_history.messages
                    if messages and len(messages) >= 2:
                        context_info = state.conversational_rag.context_tracker.extract_context_from_history(messages)
                        if context_info:
                            print(f"   📍 Contexto: {context_info.get('active_project', 'N/A')} (conf: {context_info.get('confidence', 0):.2f})")
                except Exception as e:
                    print(f"   ⚠️ Error extrayendo contexto: {e}")

            # 4. Detectar alertas automáticas
            alerts = []
            if hasattr(state.rag_engine, 'detect_response_alerts'):
                alerts = state.rag_engine.detect_response_alerts(
                    answer=answer,
                    question=question,
                    confidence=confidence,
                    chunks=chunks,
                    context_info=context_info
                )

                # Log de alertas críticas
                critical_alerts = [a for a in alerts if a['level'] in ['error', 'warning']]
                if critical_alerts:
                    print(f"   ⚠️ {len(critical_alerts)} alertas detectadas:")
                    for alert in critical_alerts:
                        print(f"      [{alert['level'].upper()}] {alert['message']}")
                else:
                    print(f"   ✅ Sin alertas - Sistema OK")
            
            # Preparar answer_text Y LIMPIAR citas [número]
            import re
            answer_text = result['answer']
            answer_text = re.sub(r'\[\d+\]', '', answer_text)  # Eliminar [4], [1], etc.
            answer_text = answer_text.strip()
            
            # Si confidence es muy bajo o respuesta es "no sé", añadir fallback a redes sociales
            if confidence < 0.5 or any(phrase in answer_text.lower() for phrase in ['no sé', 'no tengo información', 'no puedo', 'desconozco', 'no se especifica']):
                print(f"   ℹ️ Confidence bajo ({confidence:.2f}) o respuesta incierta, añadiendo fallback a redes sociales")

                fallback_text = "\n\n📱 **Para más información, puedes contactarnos en:**\n"
                fallback_text += "• **Instagram:** [dnivalenciaa](https://www.instagram.com/dnivalenciaa?igsh=MWRicTFocW5jODN6NQ==)\n"
                fallback_text += "• **WhatsApp:** Únete a nuestro grupo de voluntarios\n"
                fallback_text += "• **Tel. Responsable:** Disponible en redes sociales"

                answer_text += fallback_text

                # Aumentar confidence ligeramente por proporcionar alternativas
                confidence = min(confidence + 0.15, 0.70)
            
            # Generar sugerencias de preguntas
            # NUEVO: Extraer preguntas ya hechas del historial de chat
            asked_questions = []

            # Obtener historial correcto de session_store
            if hasattr(state.conversational_rag, 'session_store'):
                try:
                    session_history = state.conversational_rag.session_store.get_session_history(session_id)
                    messages = session_history.messages

                    # Extraer solo las preguntas del usuario (HumanMessage)
                    for msg in messages:
                        if msg.type == "human":  # HumanMessage
                            content = msg.content if hasattr(msg, 'content') else str(msg)
                            if content and content.strip():
                                asked_questions.append(content.strip())

                    print(f"   🔍 Preguntas previas detectadas: {len(asked_questions)}")
                    if asked_questions:
                        print(f"      → {', '.join([q[:30] + '...' if len(q) > 30 else q for q in asked_questions])}")
                except Exception as e:
                    print(f"   ⚠️ Error obteniendo historial: {e}")
                    asked_questions = []

            suggestions = state.question_suggester.suggest_questions(
                last_answer=answer_text,
                contexts=result.get('contexts', []),
                last_question=question,
                asked_questions=asked_questions,  # NUEVO: Pasar historial de preguntas
                num_suggestions=3
            )
            
            # Preparar sources
            sources = []
            for ctx in result.get('contexts', [])[:3]:  # Top 3 sources
                sources.append({
                    "text": ctx[:200] if isinstance(ctx, str) else str(ctx)[:200],
                    "relevance": "high"
                })
            
            log_response = f"✅ Respuesta generada en {response_time:.2f}s"
            log_confidence = f"📊 Confidence: {confidence:.3f}"
            log_sources = f"📚 Fuentes consultadas: {len(sources)}"
            log_suggestions = f"💡 Sugerencias generadas: {len(suggestions)}"
            log_history = f"🔄 Preguntas previas filtradas: {len(asked_questions)}"

            print(f"\n{log_response}")
            print(f"   {log_confidence}")
            print(f"   {log_sources}")
            print(f"   {log_suggestions}")
            print(f"   {log_history}")

            # Enviar logs finales al frontend
            await websocket.send_json({
                "type": "log",
                "log": log_response
            })
            await websocket.send_json({
                "type": "log",
                "log": log_confidence
            })
            await websocket.send_json({
                "type": "log",
                "log": log_sources
            })
            
            # Enviar chunks de texto progresivamente
            chunk_size = 50  # Caracteres por chunk
            for i in range(0, len(answer_text), chunk_size):
                chunk = answer_text[i:i+chunk_size]
                await websocket.send_json({
                    "type": "chunk",
                    "chunk": chunk,
                    "is_final": i + chunk_size >= len(answer_text)
                })
                await asyncio.sleep(0.05)  # 50ms entre chunks para efecto de escritura
            
            # Enviar respuesta completa al final con métricas detalladas
            await websocket.send_json({
                "type": "complete",
                "response": {
                    "answer": answer_text,
                    "confidence": confidence,
                    "intent": "question",
                    "response_time": round(response_time, 2),
                    "response_id": response_id,
                    "suggestions": suggestions,
                    "sources": sources,
                    # ✨ NUEVOS CAMPOS DETALLADOS
                    "confidence_breakdown": confidence_data,  # Breakdown completo del confidence
                    "top_chunks": top_chunks_info,  # Top 3 chunks con scores y fuentes
                    "context_info": context_info,  # Contexto conversacional detectado
                    "alerts": alerts,  # Alertas automáticas del sistema
                    "question_original": question,  # Pregunta original para referencia
                    "chunks_count": len(chunks)  # Total de chunks consultados
                }
            })
        
        print(f"{'='*80}\n")
        
    except WebSocketDisconnect:
        print(f"   🔌 Cliente desconectado (sesión: {session_id})")
    
    except Exception as e:
        print(f"   ❌ Error en WebSocket: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"Error procesando pregunta: {str(e)}"
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
        reload=False,  # Desactivar reload para producción
        log_level="info"
    )

