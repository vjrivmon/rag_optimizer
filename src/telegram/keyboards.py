"""
Telegram Keyboards - Inline keyboards para feedback y quick replies.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_feedback_keyboard(message_id: int) -> InlineKeyboardMarkup:
    """
    Teclado inline para feedback de respuestas del bot.

    Args:
        message_id: Database message ID para tracking

    Returns:
        InlineKeyboardMarkup con botones 👍/👎
    """
    keyboard = [
        [
            InlineKeyboardButton("👍 Útil", callback_data=f"feedback_positive_{message_id}"),
            InlineKeyboardButton("👎 No útil", callback_data=f"feedback_negative_{message_id}"),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_quick_replies_keyboard(project: str = "general") -> InlineKeyboardMarkup:
    """
    Teclado con preguntas sugeridas según proyecto DNI.

    Args:
        project: Proyecto DNI detectado (desayunos, resis, coles, etc.)

    Returns:
        InlineKeyboardMarkup con preguntas rápidas
    """
    # Preguntas por proyecto
    quick_replies = {
        "desayunos": [
            "¿Qué día son los desayunos?",
            "¿Dónde es el punto de encuentro?",
            "¿Qué necesito llevar?",
        ],
        "resis": [
            "¿Cuándo son las charlas con abuelitos?",
            "¿Hay transporte a la residencia?",
            "¿Cuántas personas van?",
        ],
        "coles": [
            "¿Qué días es el refuerzo escolar?",
            "¿Qué asignaturas se dan?",
            "¿Dónde se imparten las clases?",
        ],
        "general": [
            "¿Qué proyectos tiene DNI?",
            "¿Cómo me apunto a DNI?",
            "¿Dónde están ubicados?",
        ],
    }

    questions = quick_replies.get(project.lower(), quick_replies["general"])

    keyboard = [
        [InlineKeyboardButton(q, callback_data=f"quickreply_{i}")]
        for i, q in enumerate(questions)
    ]

    return InlineKeyboardMarkup(keyboard)


def get_consent_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para consentimiento GDPR.

    Returns:
        InlineKeyboardMarkup con opciones de consentimiento
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Acepto", callback_data="consent_accept"),
            InlineKeyboardButton("❌ Rechazar", callback_data="consent_reject"),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    Teclado genérico de confirmación.

    Args:
        action: Acción a confirmar (ej: "delete_data", "reset_context")

    Returns:
        InlineKeyboardMarkup con Sí/No
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ No", callback_data=f"cancel_{action}"),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
