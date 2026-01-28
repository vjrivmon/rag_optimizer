"""
Context Service - Manage context snapshots for persistent memory.

Handles snapshot creation, retrieval, and historical context analysis.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, desc

from src.database.base import get_session_context
from src.database.models import ContextSnapshot, ProjectContextEnum


class ContextService:
    """Service for managing context snapshots."""

    async def create_snapshot(
        self,
        conversation_id: int,
        user_id: int,
        project_context: ProjectContextEnum,
        detected_topics: List[str],
        message_count: int,
        last_user_query: Optional[str] = None,
        snapshot_data: Optional[Dict[str, Any]] = None,
    ) -> ContextSnapshot:
        """
        Create a context snapshot.

        Args:
            conversation_id: Database conversation ID
            user_id: Database user ID
            project_context: Detected DNI project
            detected_topics: List of detected topics (horarios, ubicacion, etc.)
            message_count: Number of messages in conversation at snapshot time
            last_user_query: Last user query (for reference)
            snapshot_data: Additional context data (confidence, keywords, etc.)

        Returns:
            ContextSnapshot: The created snapshot

        Raises:
            ValueError: If validation fails
        """
        if message_count < 0:
            raise ValueError(f"message_count must be >= 0, got {message_count}")

        with get_session_context() as session:
            snapshot = ContextSnapshot(
                conversation_id=conversation_id,
                user_id=user_id,
                project_context=project_context,
                detected_topics=detected_topics or [],
                message_count=message_count,
                last_user_query=last_user_query,
                snapshot_data=snapshot_data or {},
            )

            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            return snapshot

    async def get_recent_snapshots(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 10,
    ) -> List[ContextSnapshot]:
        """
        Get user's recent context snapshots.

        Args:
            user_id: Database user ID
            days: Number of days to look back
            limit: Maximum number of snapshots to return

        Returns:
            List of recent snapshots (most recent first)
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        with get_session_context() as session:
            stmt = (
                select(ContextSnapshot)
                .where(
                    and_(
                        ContextSnapshot.user_id == user_id,
                        ContextSnapshot.created_at >= cutoff_time,
                    )
                )
                .order_by(desc(ContextSnapshot.created_at))
                .limit(limit)
            )

            result = session.execute(stmt)
            return list(result.scalars().all())

    async def get_snapshots_by_project(
        self,
        user_id: int,
        project_context: ProjectContextEnum,
        days: int = 30,
        limit: int = 20,
    ) -> List[ContextSnapshot]:
        """
        Get snapshots filtered by DNI project.

        Args:
            user_id: Database user ID
            project_context: DNI project to filter by
            days: Number of days to look back
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshots for the specified project
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        with get_session_context() as session:
            stmt = (
                select(ContextSnapshot)
                .where(
                    and_(
                        ContextSnapshot.user_id == user_id,
                        ContextSnapshot.project_context == project_context,
                        ContextSnapshot.created_at >= cutoff_time,
                    )
                )
                .order_by(desc(ContextSnapshot.created_at))
                .limit(limit)
            )

            result = session.execute(stmt)
            return list(result.scalars().all())

    async def get_conversation_snapshots(
        self,
        conversation_id: int,
    ) -> List[ContextSnapshot]:
        """
        Get all snapshots for a conversation.

        Args:
            conversation_id: Database conversation ID

        Returns:
            List of snapshots (chronological order)
        """
        with get_session_context() as session:
            stmt = (
                select(ContextSnapshot)
                .where(ContextSnapshot.conversation_id == conversation_id)
                .order_by(ContextSnapshot.created_at.asc())
            )

            result = session.execute(stmt)
            return list(result.scalars().all())

    async def get_latest_snapshot(
        self,
        conversation_id: int,
    ) -> Optional[ContextSnapshot]:
        """
        Get most recent snapshot for conversation.

        Args:
            conversation_id: Database conversation ID

        Returns:
            Latest snapshot if exists, None otherwise
        """
        with get_session_context() as session:
            stmt = (
                select(ContextSnapshot)
                .where(ContextSnapshot.conversation_id == conversation_id)
                .order_by(desc(ContextSnapshot.created_at))
                .limit(1)
            )

            result = session.execute(stmt)
            return result.scalar_one_or_none()

    async def should_create_snapshot(
        self,
        conversation_id: int,
        current_message_count: int,
        snapshot_interval: int = 5,
    ) -> bool:
        """
        Determine if a new snapshot should be created.

        Snapshots are created every N messages.

        Args:
            conversation_id: Database conversation ID
            current_message_count: Current number of messages
            snapshot_interval: Create snapshot every N messages

        Returns:
            True if snapshot should be created
        """
        # Get latest snapshot
        latest = await self.get_latest_snapshot(conversation_id)

        if not latest:
            # No snapshots yet, create first one if we have enough messages
            return current_message_count >= snapshot_interval

        # Create snapshot if we've added N more messages since last snapshot
        messages_since_last = current_message_count - latest.message_count
        return messages_since_last >= snapshot_interval

    async def get_detected_topics_frequency(
        self,
        user_id: int,
        days: int = 30,
    ) -> Dict[str, int]:
        """
        Get frequency of detected topics for analytics.

        Args:
            user_id: Database user ID
            days: Number of days to analyze

        Returns:
            Dict mapping topic -> count
        """
        snapshots = await self.get_recent_snapshots(user_id, days=days, limit=1000)

        topic_counts: Dict[str, int] = {}
        for snapshot in snapshots:
            for topic in snapshot.detected_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return topic_counts

    async def get_project_distribution(
        self,
        user_id: int,
        days: int = 30,
    ) -> Dict[str, int]:
        """
        Get distribution of DNI projects discussed.

        Args:
            user_id: Database user ID
            days: Number of days to analyze

        Returns:
            Dict mapping project -> count
        """
        snapshots = await self.get_recent_snapshots(user_id, days=days, limit=1000)

        project_counts: Dict[str, int] = {}
        for snapshot in snapshots:
            project = snapshot.project_context.value
            project_counts[project] = project_counts.get(project, 0) + 1

        return project_counts

    async def cleanup_old_snapshots(
        self,
        days: int = 90,
    ) -> int:
        """
        Delete snapshots older than N days (for GDPR/storage management).

        Args:
            days: Delete snapshots older than this

        Returns:
            Number of snapshots deleted
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        with get_session_context() as session:
            stmt = select(ContextSnapshot).where(
                ContextSnapshot.created_at < cutoff_time
            )
            result = session.execute(stmt)
            old_snapshots = result.scalars().all()

            count = len(old_snapshots)
            for snapshot in old_snapshots:
                session.delete(snapshot)

            session.commit()

            return count
