"""
Test data factories for creating database objects.

Usage:
    user = create_test_user(session)
    conversation = create_test_conversation(session, user_id=user.id)
    message = create_test_message(session, conversation_id=conversation.id)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from src.database.models import (
    User,
    Conversation,
    Message,
    ContextSnapshot,
    Feedback,
    ProjectContextEnum,
    MessageRoleEnum,
    FeedbackRatingEnum,
)


def create_test_user(
    session,
    telegram_user_id: int = 123456789,
    first_name: str = "TestUser",
    last_name: Optional[str] = "Apellido",
    username: Optional[str] = "testuser",
    language_code: str = "es",
    is_active: bool = True,
) -> User:
    """Create and persist a test User."""
    user = User(
        telegram_user_id=telegram_user_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        language_code=language_code,
        is_active=is_active,
    )
    session.add(user)
    session.flush()
    return user


def create_test_conversation(
    session,
    user_id: int,
    project_context: ProjectContextEnum = ProjectContextEnum.GENERAL,
    is_active: bool = True,
) -> Conversation:
    """Create and persist a test Conversation."""
    conversation = Conversation(
        user_id=user_id,
        project_context=project_context,
        is_active=is_active,
    )
    session.add(conversation)
    session.flush()
    return conversation


def create_test_message(
    session,
    conversation_id: int,
    role: MessageRoleEnum = MessageRoleEnum.USER,
    content: str = "Hola, quiero información sobre los desayunos solidarios",
    telegram_message_id: Optional[int] = None,
    confidence_score: Optional[float] = None,
    retrieval_metadata: Optional[Dict[str, Any]] = None,
) -> Message:
    """Create and persist a test Message."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        telegram_message_id=telegram_message_id,
        confidence_score=confidence_score,
        retrieval_metadata=retrieval_metadata,
    )
    session.add(message)
    session.flush()
    return message


def create_test_context_snapshot(
    session,
    conversation_id: int,
    user_id: int,
    project_context: ProjectContextEnum = ProjectContextEnum.DESAYUNOS,
    detected_topics: Optional[List[str]] = None,
    message_count: int = 5,
    last_user_query: Optional[str] = "¿A qué hora son los desayunos?",
    snapshot_data: Optional[Dict[str, Any]] = None,
) -> ContextSnapshot:
    """Create and persist a test ContextSnapshot."""
    snapshot = ContextSnapshot(
        conversation_id=conversation_id,
        user_id=user_id,
        project_context=project_context,
        detected_topics=detected_topics or ["horarios"],
        message_count=message_count,
        last_user_query=last_user_query,
        snapshot_data=snapshot_data or {"confidence": 0.85},
    )
    session.add(snapshot)
    session.flush()
    return snapshot


def create_test_feedback(
    session,
    user_id: int,
    message_id: int,
    rating: FeedbackRatingEnum = FeedbackRatingEnum.POSITIVE,
    comment: Optional[str] = None,
) -> Feedback:
    """Create and persist a test Feedback."""
    feedback = Feedback(
        user_id=user_id,
        message_id=message_id,
        rating=rating,
        comment=comment,
    )
    session.add(feedback)
    session.flush()
    return feedback


def create_conversation_with_messages(
    session,
    user_id: int,
    project_context: ProjectContextEnum = ProjectContextEnum.DESAYUNOS,
    num_turns: int = 3,
) -> Conversation:
    """Create a conversation with several user/assistant message pairs."""
    conversation = create_test_conversation(
        session, user_id=user_id, project_context=project_context
    )

    sample_exchanges = [
        ("¿Qué son los desayunos solidarios?", "Los desayunos solidarios son un proyecto de DNI..."),
        ("¿A qué hora son?", "Los desayunos son los sábados a las 8 de la mañana."),
        ("¿Dónde nos encontramos?", "El punto de encuentro es Carrer de Sagunt, 177, Valencia."),
        ("¿Quién compra los alimentos?", "DNI compra los alimentos con donaciones de la asociación."),
        ("¿Puedo llevar a un amigo?", "Sí, cualquier persona puede participar como voluntario."),
    ]

    for i in range(min(num_turns, len(sample_exchanges))):
        user_q, assistant_a = sample_exchanges[i]
        create_test_message(
            session,
            conversation_id=conversation.id,
            role=MessageRoleEnum.USER,
            content=user_q,
        )
        create_test_message(
            session,
            conversation_id=conversation.id,
            role=MessageRoleEnum.ASSISTANT,
            content=assistant_a,
            confidence_score=0.85,
        )

    return conversation
