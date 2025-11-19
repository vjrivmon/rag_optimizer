"""
Telegram Bot Setup - Configuración principal de python-telegram-bot v20+.

Este archivo:
1. Crea la Application (PTB v20+)
2. Registra todos los handlers (commands, messages, callbacks)
3. Configura error handling
4. Inicia el bot (polling para desarrollo, webhook para producción)
"""

import os
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from .handlers import (
    start_command,
    help_command,
    reset_command,
    history_command,
    delete_my_data_command,
    message_handler,
    callback_query_handler,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def create_application() -> Application:
    """
    Crea y configura la Application de python-telegram-bot.

    Returns:
        Application configurada con todos los handlers
    """
    # Get token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token or token == 'your_bot_token_here':
        raise ValueError(
            "❌ TELEGRAM_BOT_TOKEN no configurado.\n"
            "Por favor configura el token en .env"
        )

    # Create application
    app = Application.builder().token(token).build()

    # ============================================================================
    # REGISTER COMMAND HANDLERS
    # ============================================================================

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("delete_my_data", delete_my_data_command))

    # ============================================================================
    # REGISTER MESSAGE HANDLER (texto plano, no comandos)
    # ============================================================================

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    # ============================================================================
    # REGISTER CALLBACK QUERY HANDLER (botones inline)
    # ============================================================================

    app.add_handler(CallbackQueryHandler(callback_query_handler))

    # ============================================================================
    # ERROR HANDLER
    # ============================================================================

    async def error_handler(update, context):
        """Log errors caused by updates."""
        logger.error(f"❌ Update {update} caused error: {context.error}")

    app.add_error_handler(error_handler)

    logger.info("✅ Application creada con todos los handlers registrados")

    return app


def start_bot_polling():
    """
    Inicia el bot en modo polling (bloqueante).

    Usa Application.run_polling() que maneja todo automáticamente:
    - Inicializa la app
    - Inicia polling
    - Se mantiene corriendo hasta Ctrl+C
    - Limpia recursos al cerrar
    """
    app = create_application()

    logger.info("🚀 Iniciando bot en modo POLLING...")
    logger.info("🔄 El bot estará preguntando a Telegram cada X segundos por mensajes nuevos")
    logger.info("✅ Bot activo! Presiona Ctrl+C para detener.")

    # run_polling() es bloqueante - se mantiene corriendo hasta Ctrl+C
    app.run_polling(
        allowed_updates=None,  # Recibir todos los tipos de updates
        drop_pending_updates=False,  # No descartar mensajes pendientes
    )


def main():
    """
    Entry point principal para ejecutar el bot.
    """
    logger.info("=" * 60)
    logger.info("🤖 CHATBOT DNI - TELEGRAM BOT")
    logger.info("=" * 60)

    try:
        # start_bot_polling() es bloqueante hasta Ctrl+C
        start_bot_polling()
    except KeyboardInterrupt:
        logger.info("\n👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        raise


if __name__ == "__main__":
    main()
