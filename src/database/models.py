"""
SQLAlchemy ORM models for Telegram chatbot with persistent memory.

This module defines 7 tables:
1. users - Telegram users registered in the system
2. conversations - Grouped conversations by topic/project
3. messages - All messages (user ↔ assistant) with RAG metadata
4. context_snapshots - Periodic snapshots of conversational context
5. feedback - User feedback (👍/👎) on bot responses
6. user_consents - GDPR consent management
7. analytics_events - Usage analytics events (optional)

All models include:
- Proper constraints (CHECK, UNIQUE, FK)
- Indexes for query optimization
- Relationships with cascade behavior
- Comprehensive docstrings
"""

from sqlalchemy import (
    Column, BigInteger, String, Text, Boolean, DateTime, Integer, Float,
    ForeignKey, CheckConstraint, Index, ARRAY, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .base import Base


# ============================================================================
# ENUMS
# ============================================================================

class ProjectContextEnum(str, enum.Enum):
    """Project context detected by ContextTracker."""
    DESAYUNOS = "desayunos"  # Desayunos Solidarios
    RESIS = "resis"          # Charlas con Abuelitos
    COLES = "coles"          # Refuerzo Escolar
    DANA = "dana"            # Rehabilitar Valencia (DANA support)
    KAYAK = "kayak"          # Recogida de Plásticos
    GENERAL = "general"      # General questions about DNI
    UNKNOWN = "unknown"      # Not detected yet


class MessageRoleEnum(str, enum.Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackRatingEnum(str, enum.Enum):
    """User feedback rating."""
    POSITIVE = "positive"  # 👍
    NEGATIVE = "negative"  # 👎


class ConsentTypeEnum(str, enum.Enum):
    """GDPR consent types."""
    DATA_STORAGE = "data_storage"
    ANALYTICS = "analytics"
    MARKETING = "marketing"


class EventTypeEnum(str, enum.Enum):
    """Analytics event types."""
    BOT_STARTED = "bot_started"
    COMMAND_USED = "command_used"
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    CONTEXT_RETRIEVED = "context_retrieved"
    ERROR_OCCURRED = "error_occurred"


# ============================================================================
# MODEL 1: USERS
# ============================================================================

class User(Base):
    """
    Telegram users registered in the system.

    A user is created on first interaction (/start command) and persists
    across sessions. Soft-delete via is_active=FALSE for GDPR compliance.

    Attributes:
        id (int): Internal primary key
        telegram_user_id (int): Telegram's unique user ID (from update.effective_user.id)
        first_name (str): User's first name (required)
        last_name (str): User's last name (optional)
        username (str): Telegram @username (optional, not all users have it)
        language_code (str): User's language code (es, en, ca, etc.)
        created_at (datetime): Registration timestamp
        last_interaction_at (datetime): Last message timestamp (updated on every message)
        is_active (bool): FALSE if user requested data deletion (GDPR)

    Relationships:
        conversations: List of conversations (cascade delete)
        context_snapshots: List of context snapshots (cascade delete)
        feedback: List of feedback entries (cascade delete)
        user_consents: List of GDPR consents (cascade delete)
        analytics_events: List of analytics events (set null on delete)

    Example:
        ```python
        user = User(
            telegram_user_id=123456789,
            first_name="María",
            last_name="García",
            username="maria_g",
            language_code="es"
        )
        session.add(user)
        session.commit()
        ```
    """

    __tablename__ = "users"

    # Columns
    id = Column(BigInteger, primary_key=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255))
    username = Column(String(255))
    language_code = Column(String(10))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_interaction_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Constraints
    __table_args__ = (
        CheckConstraint('telegram_user_id > 0', name='chk_telegram_user_id_positive'),
        Index('idx_users_last_interaction', 'last_interaction_at', postgresql_where=(is_active == True)),
        Index('idx_users_created_at', 'created_at'),
    )

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    context_snapshots = relationship("ContextSnapshot", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    user_consents = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_user_id}, username={self.username}, active={self.is_active})>"


# ============================================================================
# MODEL 2: CONVERSATIONS
# ============================================================================

class Conversation(Base):
    """
    Conversations grouped by topic/project DNI.

    A conversation groups related messages about a specific DNI project.
    Only 1 active conversation per user at a time (enforced by application logic).
    New conversation created if: (a) >7 days inactive, or (b) project changed.

    Attributes:
        id (int): Internal primary key
        user_id (int): Foreign key to users.id
        project_context (ProjectContextEnum): Detected project (desayunos, resis, etc.)
        is_active (bool): Only 1 active conversation per user
        created_at (datetime): Conversation start timestamp
        updated_at (datetime): Last message timestamp (auto-updated via trigger)

    Relationships:
        user: User who owns this conversation
        messages: List of messages (cascade delete)
        context_snapshots: List of snapshots (cascade delete)

    Example:
        ```python
        conversation = Conversation(
            user_id=1,
            project_context=ProjectContextEnum.DESAYUNOS,
            is_active=True
        )
        session.add(conversation)
        session.commit()
        ```
    """

    __tablename__ = "conversations"

    # Columns
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_context = Column(
        SQLEnum(ProjectContextEnum, name='project_context_enum'),
        nullable=False,
        default=ProjectContextEnum.UNKNOWN,
        index=True
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_conversations_active', 'user_id', 'is_active', postgresql_where=(is_active == True)),
        Index('idx_conversations_updated_at', 'updated_at'),
    )

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    context_snapshots = relationship("ContextSnapshot", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, project={self.project_context.value}, active={self.is_active})>"


# ============================================================================
# MODEL 3: MESSAGES
# ============================================================================

class Message(Base):
    """
    Messages exchanged in conversations (user ↔ assistant) with RAG metadata.

    Stores all messages with complete metadata from RAG pipeline:
    confidence scores, chunks used, sources, latency, etc.

    Attributes:
        id (int): Internal primary key
        conversation_id (int): Foreign key to conversations.id
        role (MessageRoleEnum): Sender role (user/assistant/system)
        content (str): Message text content
        telegram_message_id (int): Telegram's message ID (for edit/delete)
        confidence_score (float): Confidence score (0.0-1.0), required for assistant
        retrieval_metadata (dict): JSONB with RAG metadata
        created_at (datetime): Message timestamp

    Relationships:
        conversation: Conversation this message belongs to
        feedback: Feedback entry (if any)

    Example:
        ```python
        message = Message(
            conversation_id=1,
            role=MessageRoleEnum.ASSISTANT,
            content="Los Desayunos Solidarios son todos los sábados...",
            telegram_message_id=10002,
            confidence_score=0.87,
            retrieval_metadata={
                "chunks_used": 10,
                "latency_ms": 2100,
                "model_used": "gemma2:27b"
            }
        )
        session.add(message)
        session.commit()
        ```
    """

    __tablename__ = "messages"

    # Columns
    id = Column(BigInteger, primary_key=True)
    conversation_id = Column(BigInteger, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    role = Column(SQLEnum(MessageRoleEnum, name='message_role_enum'), nullable=False)
    content = Column(Text, nullable=False)
    telegram_message_id = Column(BigInteger)
    confidence_score = Column(Float)
    retrieval_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(TRIM(content)) > 0", name='chk_content_not_empty'),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)",
            name='chk_confidence_range'
        ),
        CheckConstraint(
            "role != 'assistant' OR confidence_score IS NOT NULL",
            name='chk_assistant_has_confidence'
        ),
        CheckConstraint(
            "telegram_message_id IS NULL OR telegram_message_id > 0",
            name='chk_telegram_message_id_positive'
        ),
        Index('idx_messages_conversation_id', 'conversation_id', 'created_at'),
        Index('idx_messages_created_at', 'created_at'),
        Index('idx_messages_role', 'role', postgresql_where=(role == 'user')),
        Index('idx_messages_confidence', 'confidence_score', postgresql_where=(role == 'assistant')),
        # GIN indexes will be added manually in migration (autogenerate doesn't support them well)
        # Full-text search: to_tsvector('spanish', content)
        # JSONB search: retrieval_metadata
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", uselist=False)

    def __repr__(self):
        return f"<Message(id={self.id}, conv_id={self.conversation_id}, role={self.role.value}, confidence={self.confidence_score})>"


# ============================================================================
# MODEL 4: CONTEXT_SNAPSHOTS
# ============================================================================

class ContextSnapshot(Base):
    """
    Periodic snapshots of conversational context (every 5 messages).

    Snapshots optimize historical context retrieval by storing pre-computed
    context state every N messages instead of re-analyzing entire history.

    Attributes:
        id (int): Internal primary key
        conversation_id (int): Foreign key to conversations.id
        user_id (int): Foreign key to users.id (redundant for cross-conversation queries)
        project_context (ProjectContextEnum): Detected project at snapshot time
        detected_topics (list[str]): Array of detected topics (["horarios", "ubicacion"])
        message_count (int): Number of messages at snapshot time
        last_user_query (str): Last user query (for context)
        snapshot_data (dict): JSONB with complete context state
        created_at (datetime): Snapshot timestamp

    Relationships:
        conversation: Conversation this snapshot belongs to
        user: User who owns this snapshot

    Example:
        ```python
        snapshot = ContextSnapshot(
            conversation_id=1,
            user_id=1,
            project_context=ProjectContextEnum.DESAYUNOS,
            detected_topics=["horarios", "ubicacion"],
            message_count=5,
            last_user_query="¿Dónde quedamos?",
            snapshot_data={
                "project_confidence": 0.92,
                "keywords": ["desayunos", "sábado"]
            }
        )
        session.add(snapshot)
        session.commit()
        ```
    """

    __tablename__ = "context_snapshots"

    # Columns
    id = Column(BigInteger, primary_key=True)
    conversation_id = Column(BigInteger, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_context = Column(
        SQLEnum(ProjectContextEnum, name='project_context_enum'),
        nullable=False
    )
    detected_topics = Column(ARRAY(Text))
    message_count = Column(Integer, nullable=False, default=0)
    last_user_query = Column(Text)
    snapshot_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint('message_count >= 0', name='chk_message_count_positive'),
        Index('idx_snapshots_conversation_id', 'conversation_id'),
        Index('idx_snapshots_user_id', 'user_id', 'created_at'),
        Index('idx_snapshots_created_at', 'created_at'),
        Index('idx_snapshots_project', 'project_context'),
        # GIN index for array will be added manually in migration
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="context_snapshots")
    user = relationship("User", back_populates="context_snapshots")

    def __repr__(self):
        return f"<ContextSnapshot(id={self.id}, user_id={self.user_id}, project={self.project_context.value}, msg_count={self.message_count})>"


# ============================================================================
# MODEL 5: FEEDBACK
# ============================================================================

class Feedback(Base):
    """
    User feedback (👍/👎) on bot responses for quality evaluation.

    Each message can have at most 1 feedback entry (enforced by UNIQUE constraint).

    Attributes:
        id (int): Internal primary key
        user_id (int): Foreign key to users.id
        message_id (int): Foreign key to messages.id (unique)
        rating (FeedbackRatingEnum): positive or negative
        comment (str): Optional user comment (max 500 chars)
        created_at (datetime): Feedback timestamp

    Relationships:
        user: User who submitted feedback
        message: Message being rated

    Example:
        ```python
        feedback = Feedback(
            user_id=1,
            message_id=2,
            rating=FeedbackRatingEnum.POSITIVE,
            comment="Respuesta muy clara, gracias!"
        )
        session.add(feedback)
        session.commit()
        ```
    """

    __tablename__ = "feedback"

    # Columns
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    message_id = Column(BigInteger, ForeignKey('messages.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    rating = Column(SQLEnum(FeedbackRatingEnum, name='feedback_rating_enum'), nullable=False, index=True)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("comment IS NULL OR LENGTH(comment) <= 500", name='chk_comment_length'),
    )

    # Relationships
    user = relationship("User", back_populates="feedback")
    message = relationship("Message", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback(id={self.id}, message_id={self.message_id}, rating={self.rating.value})>"


# ============================================================================
# MODEL 6: USER_CONSENTS
# ============================================================================

class UserConsent(Base):
    """
    GDPR consent management (data_storage, analytics, marketing).

    Tracks when consents were granted/revoked for compliance.
    Each user can have at most 1 consent per type (enforced by UNIQUE constraint).

    Attributes:
        id (int): Internal primary key
        user_id (int): Foreign key to users.id
        consent_type (ConsentTypeEnum): Type of consent
        granted (bool): TRUE if consent active, FALSE if revoked
        granted_at (datetime): When consent was granted
        revoked_at (datetime): When consent was revoked

    Relationships:
        user: User who gave/revoked consent

    Example:
        ```python
        consent = UserConsent(
            user_id=1,
            consent_type=ConsentTypeEnum.DATA_STORAGE,
            granted=True,
            granted_at=datetime.utcnow()
        )
        session.add(consent)
        session.commit()
        ```
    """

    __tablename__ = "user_consents"

    # Columns
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    consent_type = Column(SQLEnum(ConsentTypeEnum, name='consent_type_enum'), nullable=False)
    granted = Column(Boolean, nullable=False, default=False)
    granted_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(granted = TRUE AND granted_at IS NOT NULL) OR (granted = FALSE AND revoked_at IS NOT NULL)",
            name='chk_granted_logic'
        ),
        Index('idx_consents_type', 'consent_type', 'granted'),
    )

    # Unique constraint: one consent per user per type
    __table_args__ = __table_args__ + (
        Index('idx_consents_unique', 'user_id', 'consent_type', unique=True),
    )

    # Relationships
    user = relationship("User", back_populates="user_consents")

    def __repr__(self):
        return f"<UserConsent(id={self.id}, user_id={self.user_id}, type={self.consent_type.value}, granted={self.granted})>"


# ============================================================================
# MODEL 7: ANALYTICS_EVENTS
# ============================================================================

class AnalyticsEvent(Base):
    """
    Analytics events for usage tracking (optional, out of MVP scope).

    Records user interactions for analytics and monitoring.

    Attributes:
        id (int): Internal primary key
        user_id (int): Foreign key to users.id (nullable, SET NULL on delete)
        event_type (EventTypeEnum): Type of event
        event_data (dict): JSONB with event-specific data
        created_at (datetime): Event timestamp

    Relationships:
        user: User who triggered event (nullable)

    Example:
        ```python
        event = AnalyticsEvent(
            user_id=1,
            event_type=EventTypeEnum.COMMAND_USED,
            event_data={"command": "/start"}
        )
        session.add(event)
        session.commit()
        ```
    """

    __tablename__ = "analytics_events"

    # Columns
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), index=True)
    event_type = Column(SQLEnum(EventTypeEnum, name='event_type_enum'), nullable=False, index=True)
    event_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # No __table_args__ needed for this model
    # Partial index will be added in migration if needed

    # Relationships
    user = relationship("User", back_populates="analytics_events")

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, user_id={self.user_id}, type={self.event_type.value})>"
