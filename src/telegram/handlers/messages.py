"""
Telegram Message Handler - Procesa mensajes del usuario e integra con RAG.

Este es el handler principal que:
1. Recibe mensaje del usuario
2. Recupera contexto persistente (reciente + histórico)
3. Enriquece query con contexto
4. Llama al RAG engine para generar respuesta
5. Guarda mensaje + respuesta en DB
6. Crea snapshot si es necesario
7. Envía respuesta con feedback buttons
"""

import os
import asyncio
import html
import re
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from langchain_core.messages import HumanMessage, AIMessage

from ...services import UserService, ConversationService, MessageService, ContextService
from ...core.persistent_context_tracker import PersistentContextTracker
from ...core.conversational_rag import ConversationalRAGEngine
from ...core.model_wrapper import LLMWrapper
from ...core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from ...core.intent_classifier import IntentClassifier
from ...database.models import MessageRoleEnum
from ..keyboards import get_feedback_keyboard

# Security SDK
from vicente_rag.security import InjectionDetector, Sanitizer

# Module-level security instances
_injection_detector = InjectionDetector()
_sanitizer = Sanitizer(max_length=5000)


# ============================================================================
# UTILIDADES DE FORMATO TELEGRAM
# ============================================================================

def _validate_url(url: str) -> bool:
    """Only allow http:// and https:// URLs."""
    return url.startswith("http://") or url.startswith("https://")


def markdown_to_html(text: str) -> str:
    """
    Convierte markdown básico a HTML para Telegram.

    Security: escapa HTML del contenido antes de convertir markdown,
    y valida URLs para prevenir javascript: y data: injection.

    Telegram con parse_mode='HTML' soporta:
    - <b>negrita</b>
    - <i>cursiva</i>
    - <a href="url">texto</a>
    - <code>código</code>

    Args:
        text: Texto con markdown (**negrita**, *cursiva*, [texto](url))

    Returns:
        Texto con HTML seguro
    """
    # Security: escape HTML entities first to prevent injection
    text = html.escape(text, quote=False)

    # 1. Convertir **negrita** → <b>negrita</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # 2. Convertir [texto](url) → <a href="url">texto</a> (only safe URLs)
    def _safe_link(match):
        link_text = match.group(1)
        url = match.group(2)
        if _validate_url(url):
            return f'<a href="{url}">{link_text}</a>'
        return link_text  # strip unsafe link, keep text

    text = re.sub(r'\[(.+?)\]\((.+?)\)', _safe_link, text)

    # 3. Convertir `código` → <code>código</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

    # 4. Convertir *cursiva* → <i>cursiva</i>
    # IMPORTANTE: NO convertir asteriscos en listas de viñetas
    text = re.sub(r'^(\* )', r'<<<BULLET>>>', text, flags=re.MULTILINE)
    text = re.sub(r'\n(\* )', r'\n<<<BULLET>>>', text)

    # Ahora convertir TODAS las cursivas restantes
    text = re.sub(r'(?<!\*)\*([^\*\n]+?)\*(?!\*)', r'<i>\1</i>', text)

    # Restaurar las viñetas
    text = text.replace('<<<BULLET>>>', '* ')

    return text


# ============================================================================
# INICIALIZACIÓN GLOBAL DEL RAG ENGINE (Una sola vez)
# ============================================================================

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VECTOR_STORE_PATH = PROJECT_ROOT / "data" / "vectorstore" / "chroma_db"

# Inicializar LLM Wrapper
_model = LLMWrapper(
    model_name=os.getenv('OLLAMA_MODEL', 'gemma2:27b'),
    api_endpoint=os.getenv('OLLAMA_API_URL', 'https://ollama.gti-ia.upv.es:443/api/generate')
)

# Inicializar Enhanced RAG Engine
_base_rag_engine = EnhancedRAGEngineNew(
    vector_store_path=str(VECTOR_STORE_PATH),
    model=_model
)

# Inicializar Conversational RAG Engine (GLOBAL - reutilizado en cada mensaje)
_conversational_rag = ConversationalRAGEngine(
    base_rag_engine=_base_rag_engine,
    model_wrapper=_model
)

print("✅ RAG Engine inicializado globalmente para Telegram bot")
print(f"   ✓ Vector Store: {VECTOR_STORE_PATH}")
print(f"   ✓ Modelo: {_model.model_name}")
print(f"   ✓ Endpoint: {_model.api_endpoint}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler principal para mensajes de usuario.

    Flujo optimizado:
    1. Clasificar intent (greeting/goodbye/thanks/help/question)
    2. Si es greeting/goodbye/thanks/help → Responder inmediatamente (SIN RAG, SIN contexto)
    3. Si es question → Aplicar contexto + RAG
    """
    user = update.effective_user
    raw_text = update.message.text

    if not raw_text or not raw_text.strip():
        await update.message.reply_text("Por favor envía un mensaje válido.")
        return

    # ============================================================================
    # 0. SECURITY: SANITIZE + INJECTION DETECTION
    # ============================================================================

    message_text = _sanitizer.sanitize_strict(raw_text)

    injection_result = _injection_detector.detect(message_text, use_semantic=False)
    if injection_result.is_injection:
        print(f"   [SECURITY] Injection detected from user {user.id}: {injection_result.matched_patterns[:3]}")
        await update.message.reply_text(
            "Lo siento, no puedo procesar esa solicitud. "
            "¿Puedo ayudarte con algo sobre DNI Voluntariado?"
        )
        return

    # ============================================================================
    # 1. CLASIFICACIÓN DE INTENT (ANTES DE TODO)
    # ============================================================================

    intent_classifier = IntentClassifier()
    intent_result = intent_classifier.classify(message_text)
    intent_type = intent_result.intent  # ← IntentResult es un dataclass, usar .intent no ['intent']

    # ============================================================================
    # 2. SETUP SERVICES
    # ============================================================================

    user_service = UserService()
    conversation_service = ConversationService()
    message_service = MessageService()
    context_service = ContextService()

    # Get or create user
    db_user = await user_service.get_or_create_user(
        telegram_user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
    )

    # Get or create conversation
    conversation = await conversation_service.get_or_create_conversation(
        user_id=db_user.id,
    )

    # ============================================================================
    # 3. MANEJO RÁPIDO DE GREETINGS/GOODBYES (SIN RAG)
    # ============================================================================

    if intent_type in ['greeting', 'goodbye', 'thanks', 'help']:
        # Respuesta predefinida inmediata (NO usar RAG)
        response_text = markdown_to_html(intent_result.predefined_response)

        # Guardar mensaje del usuario
        await message_service.save_message(
            conversation_id=conversation.id,
            role=MessageRoleEnum.USER,
            content=message_text,
            telegram_message_id=update.message.message_id,
        )

        # Guardar respuesta del bot
        await message_service.save_message(
            conversation_id=conversation.id,
            role=MessageRoleEnum.ASSISTANT,
            content=intent_result.predefined_response,
            confidence_score=1.0,  # Máxima confianza para respuestas predefinidas
            retrieval_metadata={'intent': intent_type, 'fast_response': True},
        )

        # Enviar respuesta inmediata
        await update.message.reply_text(
            response_text,
            parse_mode='HTML'
        )

        # Log success
        print(f"✅ Fast response ({intent_type}) | User: {user.id}")
        return  # ← SALIR AQUÍ, NO continuar con RAG

    # ============================================================================
    # 4. RECUPERAR CONTEXTO CONVERSACIONAL (SOLO PARA PREGUNTAS REALES)
    # ============================================================================
    # Si llegamos aquí, es una PREGUNTA REAL que necesita RAG

    # Get recent messages (últimas 8 mensajes = 4 interacciones)
    recent_messages = await message_service.get_conversation_history(
        conversation_id=conversation.id,
        limit=8,
    )

    # Reverse para orden cronológico (más antiguo primero)
    recent_messages.reverse()

    # Convert to LangChain format
    langchain_history = []
    for msg in recent_messages:
        if msg.role == MessageRoleEnum.USER:
            langchain_history.append(HumanMessage(content=msg.content))
        elif msg.role == MessageRoleEnum.ASSISTANT:
            langchain_history.append(AIMessage(content=msg.content))

    # Initialize persistent context tracker
    persistent_tracker = PersistentContextTracker(
        context_service=context_service,
        window_size=4,
        history_days=7,
        decay_half_life_days=3.0,
        snapshot_interval=5,
    )

    # Get active context (combines recent + historical with exponential decay)
    context_info = await persistent_tracker.get_active_context(
        conversation_history=langchain_history,
        current_query=message_text,
        user_id=db_user.id,
        conversation_id=conversation.id,
    )

    enriched_query = context_info['enriched_query']

    # ============================================================================
    # 5. PROCESAR CON RAG ENGINE (con indicador de progreso)
    # ============================================================================

    # Función helper para mantener "typing..." activo durante procesamiento largo
    async def keep_typing(chat, stop_event):
        """Mantiene el indicador typing activo cada 4 segundos"""
        while not stop_event.is_set():
            try:
                await chat.send_action("typing")
                await asyncio.sleep(4)  # Telegram typing dura ~5s, renovar cada 4s
            except Exception:
                break

    # Iniciar typing indicator
    typing_stop = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(update.message.chat, typing_stop))

    try:
        # Usar RAG engine global (ya inicializado)
        rag_engine = _conversational_rag

        # Process query with RAG (using enriched query)
        # process_query es sync, usamos to_thread para no bloquear event loop
        rag_result = await asyncio.to_thread(
            rag_engine.process_query,
            query=enriched_query,
            session_id=f"telegram_{user.id}",
            question_id=0  # Forzar RAG avanzado siempre
        )

        # Detener typing indicator
        typing_stop.set()
        await typing_task

        answer = rag_result.get('answer', 'Lo siento, no pude generar una respuesta.')
        confidence = rag_result.get('confidence', 0.5)
        sources = rag_result.get('sources', [])
        retrieval_metadata = rag_result.get('metadata', {})

    except Exception as e:
        # Detener typing indicator en caso de error
        typing_stop.set()
        if typing_task and not typing_task.done():
            await typing_task

        # Error handling - fallback response
        answer = (
            "❌ Lo siento, ocurrió un error al procesar tu pregunta.\n\n"
            "Por favor intenta de nuevo o contacta directamente:\n"
            "📧 info@asociaciondni.org\n"
            "📱 @AsociacionDNI"
        )
        confidence = 0.0
        sources = []
        retrieval_metadata = {'error': str(e)}

        # Log error
        print(f"❌ RAG Error: {e}")

    # ============================================================================
    # 6. GUARDAR MENSAJES EN BASE DE DATOS
    # ============================================================================

    # Save user message
    user_msg = await message_service.save_message(
        conversation_id=conversation.id,
        role=MessageRoleEnum.USER,
        content=message_text,
        telegram_message_id=update.message.message_id,
    )

    # Save assistant response
    assistant_msg = await message_service.save_message(
        conversation_id=conversation.id,
        role=MessageRoleEnum.ASSISTANT,
        content=answer,
        confidence_score=confidence,
        retrieval_metadata={
            'sources': sources,
            'enriched_query': enriched_query,
            'context_info': context_info,
            **retrieval_metadata,
        },
    )

    # Update conversation timestamp
    await conversation_service.update_conversation_timestamp(conversation.id)

    # ============================================================================
    # 7. CREAR SNAPSHOT SI ES NECESARIO
    # ============================================================================

    # Get current message count
    message_count = await conversation_service.get_conversation_message_count(
        conversation.id
    )

    # Create snapshot if needed (every 5 messages, high confidence, or project change)
    snapshot_created = await persistent_tracker.create_snapshot_if_needed(
        conversation_id=conversation.id,
        user_id=db_user.id,
        context_info=context_info,
        message_count=message_count,
        last_user_query=message_text,
    )

    # ============================================================================
    # 8. ENVIAR RESPUESTA AL USUARIO
    # ============================================================================

    # Build response text (sin emojis de debug ni info de contexto)
    response_text = answer

    # Add sources if available (opcional - comentar si no se quiere mostrar)
    if sources and len(sources) > 0:
        response_text += f"\n\n📚 <i>Fuentes: {', '.join(sources[:3])}</i>"

    # Convertir markdown a HTML para Telegram
    response_text = markdown_to_html(response_text)

    # Send response with feedback keyboard
    # Usar parse_mode='HTML' para formato correcto en Telegram
    await update.message.reply_text(
        response_text,
        reply_markup=get_feedback_keyboard(assistant_msg.id),
        parse_mode='HTML'  # ← CRÍTICO: Permite <b>, <i>, <a href="...">
    )

    # Log success
    print(f"✅ Response sent | User: {user.id} | Confidence: {confidence:.2f} | Snapshot: {snapshot_created}")
