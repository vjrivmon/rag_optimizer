"""
Conversation Service - Manage conversations grouped by DNI project.

Handles conversation creation, retrieval, and project context detection.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from src.database.base import get_session_context
from src.database.models import Conversation, ProjectContextEnum, Message


class ConversationService:
    """Service for managing conversations."""

    async def create_conversation(
        self,
        user_id: int,
        project_context: ProjectContextEnum = ProjectContextEnum.UNKNOWN,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: Database user ID
            project_context: DNI project context (desayunos, resis, coles, etc.)

        Returns:
            Conversation: The newly created conversation

        Raises:
            ValueError: If user_id is invalid
        """
        if user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")

        with get_session_context() as session:
            conversation = Conversation(
                user_id=user_id,
                project_context=project_context,
                is_active=True,
            )

            session.add(conversation)
            session.commit()
            session.refresh(conversation)

            return conversation

    async def get_active_conversation(
        self,
        user_id: int,
        project_context: Optional[ProjectContextEnum] = None,
    ) -> Optional[Conversation]:
        """
        Get user's active conversation (optionally filtered by project).

        Args:
            user_id: Database user ID
            project_context: Optional project filter

        Returns:
            Active conversation if found, None otherwise
        """
        with get_session_context() as session:
            stmt = select(Conversation).where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.is_active == True,
                )
            )

            if project_context:
                stmt = stmt.where(Conversation.project_context == project_context)

            stmt = stmt.order_by(Conversation.updated_at.desc())

            result = session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_or_create_conversation(
        self,
        user_id: int,
        project_context: ProjectContextEnum = ProjectContextEnum.UNKNOWN,
    ) -> Conversation:
        """
        Get active conversation or create new one if doesn't exist.

        Args:
            user_id: Database user ID
            project_context: DNI project context

        Returns:
            Conversation: Existing or newly created conversation
        """
        # Try to get existing active conversation
        existing = await self.get_active_conversation(user_id, project_context)

        if existing:
            return existing

        # Create new conversation
        return await self.create_conversation(user_id, project_context)

    async def update_conversation_timestamp(self, conversation_id: int) -> None:
        """
        Update conversation's updated_at timestamp.

        Args:
            conversation_id: Database conversation ID
        """
        with get_session_context() as session:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.updated_at = datetime.now(timezone.utc)
                session.commit()

    async def update_project_context(
        self,
        conversation_id: int,
        project_context: ProjectContextEnum,
    ) -> None:
        """
        Update conversation's project context.

        Args:
            conversation_id: Database conversation ID
            project_context: New project context
        """
        with get_session_context() as session:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.project_context = project_context
                conversation.updated_at = datetime.now(timezone.utc)
                session.commit()

    async def end_conversation(self, conversation_id: int) -> None:
        """
        End (deactivate) a conversation.

        Args:
            conversation_id: Database conversation ID
        """
        with get_session_context() as session:
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.is_active = False
                conversation.updated_at = datetime.now(timezone.utc)
                session.commit()

    async def get_user_conversations(
        self,
        user_id: int,
        limit: int = 10,
        include_inactive: bool = False,
    ) -> List[Conversation]:
        """
        Get user's conversations (most recent first).

        Args:
            user_id: Database user ID
            limit: Maximum number of conversations to return
            include_inactive: Whether to include inactive conversations

        Returns:
            List of conversations
        """
        with get_session_context() as session:
            stmt = select(Conversation).where(Conversation.user_id == user_id)

            if not include_inactive:
                stmt = stmt.where(Conversation.is_active == True)

            stmt = (
                stmt.order_by(Conversation.updated_at.desc())
                .limit(limit)
                .options(joinedload(Conversation.messages))
            )

            result = session.execute(stmt)
            return list(result.scalars().unique().all())

    async def get_conversation_message_count(self, conversation_id: int) -> int:
        """
        Get count of messages in conversation.

        Args:
            conversation_id: Database conversation ID

        Returns:
            Number of messages
        """
        with get_session_context() as session:
            stmt = select(Message).where(Message.conversation_id == conversation_id)
            result = session.execute(stmt)
            return len(result.all())
