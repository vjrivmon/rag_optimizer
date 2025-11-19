"""
Telegram Command Handlers - /start, /help, /reset, /history, /delete_my_data
"""

from telegram import Update
from telegram.ext import ContextTypes

from ...services import UserService, ConversationService, MessageService
from ..keyboards import get_consent_keyboard, get_confirmation_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para /start - Onboarding y bienvenida.

    Crea usuario en DB si no existe y muestra mensaje de bienvenida.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Services
    user_service = UserService()
    conversation_service = ConversationService()

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

    # Welcome message
    welcome_text = f"""
¡Hola {user.first_name}! 👋 Bienvenid@ al Chatbot oficial de DNI (Damos Nuestra Ilusión) 💙

Soy tu asistente virtual para todo sobre nuestros proyectos de voluntariado en Valencia.

**Proyectos DNI:**
🍞 Desayunos Solidarios (sábados, personas sin hogar)
👴 Charlas con Abuelitos (residencia L'Acollida)
📚 Refuerzo Escolar COLES (niños)
🏗️ Rehabilitar Valencia (apoyo DANA - Horta Sud)
🚣 Recogida de Plásticos (kayak en río)

**Comandos disponibles:**
/help - Ver ayuda completa
/reset - Reiniciar conversación
/history - Ver tu historial
/delete_my_data - Eliminar tus datos (GDPR)

**¿En qué puedo ayudarte hoy?**
Pregúntame sobre horarios, ubicaciones, requisitos o cómo participar 😊

PARA. MIRA. AYUDA. ❤️
"""

    await update.message.reply_text(welcome_text, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para /help - Mostrar ayuda completa.
    """
    help_text = """
📖 **Ayuda - Chatbot DNI**

**Cómo usar el bot:**
1. Simplemente escríbeme tu pregunta
2. Te responderé con información de nuestros documentos oficiales
3. Puedes darme feedback con los botones 👍/👎

**Ejemplos de preguntas:**
- "¿Qué día son los desayunos solidarios?"
- "¿Cómo me apunto a RESIS?"
- "¿Dónde está el punto de encuentro?"
- "¿Qué requisitos hay para participar?"
- "¿Cuánto tiempo duran las actividades?"

**Comandos disponibles:**
/start - Iniciar conversación
/help - Mostrar esta ayuda
/reset - Reiniciar contexto (nueva conversación)
/history - Ver tu historial de conversaciones
/delete_my_data - Eliminar todos tus datos (GDPR)

**Contacto directo DNI:**
📧 Email: info@asociaciondni.org
📱 Instagram: @AsociacionDNI
📍 Ubicación: Carrer de Sagunt, 177, Valencia

**Privacidad:**
- Tus conversaciones se guardan para mejorar el servicio
- Puedes eliminar tus datos en cualquier momento con /delete_my_data
- No compartimos tu información con terceros

¿Alguna pregunta? ¡Adelante! 😊
"""

    await update.message.reply_text(help_text, parse_mode='HTML')


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para /reset - Reiniciar contexto conversacional.

    Cierra la conversación actual y crea una nueva.
    """
    user = update.effective_user

    # Services
    user_service = UserService()
    conversation_service = ConversationService()

    # Get user
    db_user = await user_service.get_user_by_telegram_id(user.id)

    if not db_user:
        await update.message.reply_text(
            "❌ No estás registrado. Usa /start primero.",
            parse_mode='HTML'
        )
        return

    # Get active conversation
    active_conversation = await conversation_service.get_active_conversation(db_user.id)

    if active_conversation:
        # End current conversation
        await conversation_service.end_conversation(active_conversation.id)

        # Create new conversation
        new_conversation = await conversation_service.create_conversation(db_user.id)

        await update.message.reply_text(
            "✅ Conversación reiniciada!\n\n"
            "El contexto anterior ha sido guardado y ahora empezamos de cero.\n"
            "¿En qué puedo ayudarte? 😊",
            parse_mode='HTML'
        )
    else:
        # No active conversation, create one
        await conversation_service.create_conversation(db_user.id)

        await update.message.reply_text(
            "✅ Nueva conversación creada!\n\n"
            "¿En qué puedo ayudarte? 😊",
            parse_mode='HTML'
        )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para /history - Mostrar historial de conversaciones.
    """
    user = update.effective_user

    # Services
    user_service = UserService()
    conversation_service = ConversationService()
    message_service = MessageService()

    # Get user
    db_user = await user_service.get_user_by_telegram_id(user.id)

    if not db_user:
        await update.message.reply_text(
            "❌ No estás registrado. Usa /start primero.",
            parse_mode='HTML'
        )
        return

    # Get recent conversations
    conversations = await conversation_service.get_user_conversations(
        user_id=db_user.id,
        limit=5,
        include_inactive=True,
    )

    if not conversations:
        await update.message.reply_text(
            "📭 No tienes conversaciones previas.\n\n"
            "Empieza haciendo una pregunta! 😊",
            parse_mode='HTML'
        )
        return

    # Build history text
    history_text = "📚 **Tu historial reciente:**\n\n"

    for i, conv in enumerate(conversations, 1):
        # Get message count
        msg_count = await conversation_service.get_conversation_message_count(conv.id)

        # Format dates
        created = conv.created_at.strftime("%d/%m/%Y %H:%M")
        updated = conv.updated_at.strftime("%d/%m/%Y %H:%M")

        # Status
        status = "🟢 Activa" if conv.is_active else "⚪ Cerrada"

        # Project
        project = conv.project_context.value.capitalize()

        history_text += f"**{i}. Conversación** ({status})\n"
        history_text += f"   📁 Proyecto: {project}\n"
        history_text += f"   💬 Mensajes: {msg_count}\n"
        history_text += f"   📅 Creada: {created}\n"
        history_text += f"   🔄 Última actividad: {updated}\n\n"

    history_text += "\n💡 Usa /reset para empezar una nueva conversación"

    await update.message.reply_text(history_text, parse_mode='HTML')


async def delete_my_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para /delete_my_data - Eliminar datos del usuario (GDPR).

    Muestra confirmación antes de eliminar.
    """
    user = update.effective_user

    # Services
    user_service = UserService()

    # Get user
    db_user = await user_service.get_user_by_telegram_id(user.id)

    if not db_user:
        await update.message.reply_text(
            "❌ No estás registrado. No hay datos que eliminar.",
            parse_mode='HTML'
        )
        return

    # Show confirmation dialog
    confirmation_text = (
        "⚠️ **Eliminar todos tus datos**\n\n"
        "Esto eliminará permanentemente:\n"
        "- Todas tus conversaciones\n"
        "- Todos tus mensajes\n"
        "- Todos tus snapshots de contexto\n"
        "- Todo tu historial de feedback\n\n"
        "**Esta acción NO se puede deshacer.**\n\n"
        "¿Estás segur@?"
    )

    await update.message.reply_text(
        confirmation_text,
        reply_markup=get_confirmation_keyboard("delete_data"),
        parse_mode='HTML'
    )
