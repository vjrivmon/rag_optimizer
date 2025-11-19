"""
Database package for Telegram chatbot with PostgreSQL persistence.

This package contains:
- models.py: SQLAlchemy ORM models (7 tables)
- base.py: Declarative base and session management
- connection.py: Database connection and pooling configuration
"""

from .base import Base, get_session, init_db
from .models import (
    User,
    Conversation,
    Message,
    ContextSnapshot,
    Feedback,
    UserConsent,
    AnalyticsEvent,
    ProjectContextEnum,
    MessageRoleEnum,
    FeedbackRatingEnum,
    ConsentTypeEnum,
    EventTypeEnum,
)

__all__ = [
    # Base
    "Base",
    "get_session",
    "init_db",
    # Models
    "User",
    "Conversation",
    "Message",
    "ContextSnapshot",
    "Feedback",
    "UserConsent",
    "AnalyticsEvent",
    # Enums
    "ProjectContextEnum",
    "MessageRoleEnum",
    "FeedbackRatingEnum",
    "ConsentTypeEnum",
    "EventTypeEnum",
]
