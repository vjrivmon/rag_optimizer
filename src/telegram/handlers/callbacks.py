"""
Telegram Callback Query Handler - Procesa clicks en botones inline.

Maneja:
- Feedback buttons (👍/👎)
- Confirmaciones (delete_data, reset_context)
- Quick replies (preguntas sugeridas)
"""

from telegram import Update
from telegram.ext import ContextTypes

from ...services import UserService, MessageService
from ...database.models import Feedback, FeedbackRatingEnum
from ...database.base import get_session_context


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler para callback queries (botones inline).
    """
    query = update.callback_query
    user = update.effective_user

    # Parse callback data
    callback_data = query.data

    # ============================================================================
    # FEEDBACK BUTTONS (👍/👎)
    # ============================================================================

    if callback_data.startswith("feedback_"):
        await handle_feedback(query, user, callback_data)

    # ============================================================================
    # QUICK REPLIES (preguntas sugeridas)
    # ============================================================================

    elif callback_data.startswith("quickreply_"):
        await handle_quick_reply(query, user, callback_data, context)

    # ============================================================================
    # CONFIRMACIONES (delete_data, reset_context)
    # ============================================================================

    elif callback_data.startswith("confirm_"):
        await handle_confirmation(query, user, callback_data, context)

    elif callback_data.startswith("cancel_"):
        await handle_cancellation(query, user, callback_data)

    # ============================================================================
    # CONSENT (GDPR)
    # ============================================================================

    elif callback_data == "consent_accept":
        await handle_consent_accept(query, user)

    elif callback_data == "consent_reject":
        await handle_consent_reject(query, user)

    # ============================================================================
    # UNKNOWN CALLBACK
    # ============================================================================

    else:
        await query.answer("❌ Acción desconocida", show_alert=True)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


async def handle_feedback(query, user, callback_data: str) -> None:
    """
    Procesa feedback (👍/👎) de respuestas del bot.

    Callback format: "feedback_{positive|negative}_{message_id}"
    """
    try:
        parts = callback_data.split("_")
        rating_str = parts[1]  # "positive" or "negative"
        message_id = int(parts[2])

        # Determine rating
        if rating_str == "positive":
            rating = FeedbackRatingEnum.POSITIVE
            emoji = "👍"
            message = "¡Gracias por tu feedback positivo!"
        else:
            rating = FeedbackRatingEnum.NEGATIVE
            emoji = "👎"
            message = "Gracias por tu feedback. Trabajaremos para mejorar."

        # Services
        user_service = UserService()
        message_service = MessageService()

        # Get user
        db_user = await user_service.get_user_by_telegram_id(user.id)

        if not db_user:
            await query.answer("❌ Error: usuario no encontrado", show_alert=True)
            return

        # Get message
        db_message = await message_service.get_message_by_id(message_id)

        if not db_message:
            await query.answer("❌ Error: mensaje no encontrado", show_alert=True)
            return

        # Save feedback
        with get_session_context() as session:
            feedback = Feedback(
                user_id=db_user.id,
                message_id=message_id,
                rating=rating,
                comment=None,  # Could add comment modal later
            )

            session.add(feedback)

        # Answer callback query
        await query.answer(message)

        # Edit message to show feedback was received
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"{emoji} {message}")

    except Exception as e:
        print(f"❌ Feedback error: {e}")
        await query.answer("❌ Error al guardar feedback", show_alert=True)


async def handle_quick_reply(query, user, callback_data: str, context) -> None:
    """
    Procesa quick replies (preguntas sugeridas).

    Callback format: "quickreply_{index}"
    """
    # Quick replies mapping (should match keyboards.py)
    quick_replies = {
        0: "¿Qué día son los desayunos?",
        1: "¿Dónde es el punto de encuentro?",
        2: "¿Qué necesito llevar?",
    }

    try:
        index = int(callback_data.split("_")[1])
        question = quick_replies.get(index, "¿Qué proyectos tiene DNI?")

        # Answer callback
        await query.answer()

        # Send question as if user typed it
        # This will be processed by message_handler
        await query.message.reply_text(question)

    except Exception as e:
        print(f"❌ Quick reply error: {e}")
        await query.answer("❌ Error", show_alert=True)


async def handle_confirmation(query, user, callback_data: str, context) -> None:
    """
    Procesa confirmaciones (Sí).

    Callback format: "confirm_{action}"
    """
    action = callback_data.replace("confirm_", "")

    if action == "delete_data":
        # Delete all user data (GDPR)
        try:
            user_service = UserService()

            # Get user
            db_user = await user_service.get_user_by_telegram_id(user.id)

            if db_user:
                # Deactivate user (soft delete)
                # Cascade will handle conversations, messages, snapshots, etc.
                await user_service.deactivate_user(db_user.id)

                await query.answer()
                await query.edit_message_text(
                    "✅ **Datos eliminados correctamente**\n\n"
                    "Todos tus datos han sido eliminados de nuestra base de datos.\n\n"
                    "Si quieres volver a usar el bot, usa /start para crear una nueva cuenta."
                )
            else:
                await query.answer("❌ Usuario no encontrado", show_alert=True)

        except Exception as e:
            print(f"❌ Delete data error: {e}")
            await query.answer("❌ Error al eliminar datos", show_alert=True)

    else:
        await query.answer(f"✅ Confirmado: {action}")
        await query.edit_message_text(f"✅ Acción confirmada: {action}")


async def handle_cancellation(query, user, callback_data: str) -> None:
    """
    Procesa cancelaciones (No).

    Callback format: "cancel_{action}"
    """
    action = callback_data.replace("cancel_", "")

    await query.answer()
    await query.edit_message_text(
        f"❌ **Acción cancelada**\n\nNo se realizó ninguna acción."
    )


async def handle_consent_accept(query, user) -> None:
    """
    Procesa aceptación de consentimiento GDPR.
    """
    # TODO: Implement consent storage if needed

    await query.answer()
    await query.edit_message_text(
        "✅ **Consentimiento aceptado**\n\n"
        "Gracias por aceptar. Tus datos serán tratados según nuestra política de privacidad."
    )


async def handle_consent_reject(query, user) -> None:
    """
    Procesa rechazo de consentimiento GDPR.
    """
    await query.answer()
    await query.edit_message_text(
        "❌ **Consentimiento rechazado**\n\n"
        "Respetamos tu decisión. No podrás usar el bot sin aceptar el tratamiento de datos."
    )
