"""
Message Service - Manage messages with RAG metadata.

Handles message storage, retrieval, and conversation history.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import joinedload

from src.database.base import get_session_context
from src.database.models import Message, MessageRoleEnum


class MessageService:
    """Service for managing messages."""

    async def save_message(
        self,
        conversation_id: int,
        role: MessageRoleEnum,
        content: str,
        telegram_message_id: Optional[int] = None,
        confidence_score: Optional[float] = None,
        retrieval_metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Save a message to the database.

        Args:
            conversation_id: Database conversation ID
            role: Message role (USER, ASSISTANT, SYSTEM)
            content: Message content
            telegram_message_id: Telegram's message ID (optional)
            confidence_score: RAG confidence score (required for ASSISTANT)
            retrieval_metadata: RAG metadata (chunks, sources, latency, etc.)

        Returns:
            Message: The saved message

        Raises:
            ValueError: If validation fails
        """
        # Validation
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

        if role == MessageRoleEnum.ASSISTANT and confidence_score is None:
            raise ValueError("confidence_score required for ASSISTANT messages")

        if confidence_score is not None and not (0.0 <= confidence_score <= 1.0):
            raise ValueError(f"confidence_score must be in [0.0, 1.0], got {confidence_score}")

        with get_session_context() as session:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content.strip(),
                telegram_message_id=telegram_message_id,
                confidence_score=confidence_score,
                retrieval_metadata=retrieval_metadata or {},
            )

            session.add(message)
            session.commit()
            session.refresh(message)

            return message

    async def get_conversation_history(
        self,
        conversation_id: int,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Message]:
        """
        Get conversation history (most recent first by default).

        Args:
            conversation_id: Database conversation ID
            limit: Maximum number of messages to return (None = all)
            offset: Number of messages to skip

        Returns:
            List of messages ordered by created_at DESC
        """
        with get_session_context() as session:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(desc(Message.created_at))
                .offset(offset)
            )

            if limit:
                stmt = stmt.limit(limit)

            result = session.execute(stmt)
            return list(result.scalars().all())

    async def get_recent_messages(
        self,
        conversation_id: int,
        hours: int = 24,
    ) -> List[Message]:
        """
        Get messages from last N hours.

        Args:
            conversation_id: Database conversation ID
            hours: Number of hours to look back

        Returns:
            List of recent messages
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        with get_session_context() as session:
            stmt = (
                select(Message)
                .where(
                    and_(
                        Message.conversation_id == conversation_id,
                        Message.created_at >= cutoff_time,
                    )
                )
                .order_by(Message.created_at.asc())  # Chronological order
            )

            result = session.execute(stmt)
            return list(result.scalars().all())

    async def get_user_message_history(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 100,
    ) -> List[Message]:
        """
        Get user's message history across all conversations.

        Args:
            user_id: Database user ID
            days: Number of days to look back
            limit: Maximum number of messages to return

        Returns:
            List of messages from all user's conversations
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        with get_session_context() as session:
            stmt = (
                select(Message)
                .join(Message.conversation)
                .where(
                    and_(
                        Message.conversation.has(user_id=user_id),
                        Message.created_at >= cutoff_time,
                    )
                )
                .order_by(desc(Message.created_at))
                .limit(limit)
            )

            result = session.execute(stmt)
            return list(result.scalars().all())

    async def search_messages(
        self,
        conversation_id: int,
        query: str,
        limit: int = 20,
    ) -> List[Message]:
        """
        Search messages by content (simple LIKE search).

        Args:
            conversation_id: Database conversation ID
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching messages
        """
        with get_session_context() as session:
            stmt = (
                select(Message)
                .where(
                    and_(
                        Message.conversation_id == conversation_id,
                        Message.content.ilike(f"%{query}%"),
                    )
                )
                .order_by(desc(Message.created_at))
                .limit(limit)
            )

            result = session.execute(stmt)
            return list(result.scalars().all())

    async def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """
        Get message by ID.

        Args:
            message_id: Database message ID

        Returns:
            Message if found, None otherwise
        """
        with get_session_context() as session:
            stmt = select(Message).where(Message.id == message_id)
            result = session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_average_confidence(self, conversation_id: int) -> Optional[float]:
        """
        Calculate average confidence score for ASSISTANT messages.

        Args:
            conversation_id: Database conversation ID

        Returns:
            Average confidence or None if no ASSISTANT messages
        """
        with get_session_context() as session:
            stmt = select(Message).where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.role == MessageRoleEnum.ASSISTANT,
                    Message.confidence_score.isnot(None),
                )
            )

            result = session.execute(stmt)
            messages = result.scalars().all()

            if not messages:
                return None

            total = sum(msg.confidence_score for msg in messages)
            return total / len(messages)

    async def format_history_for_rag(
        self,
        conversation_id: int,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Format conversation history for RAG engine.

        Args:
            conversation_id: Database conversation ID
            limit: Number of recent messages to include

        Returns:
            List of dicts with 'role' and 'content' keys
        """
        messages = await self.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit,
        )

        # Reverse to get chronological order (oldest first)
        messages.reverse()

        return [
            {
                "role": msg.role.value.lower(),  # 'USER' -> 'user'
                "content": msg.content,
            }
            for msg in messages
        ]
