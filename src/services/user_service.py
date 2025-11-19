"""
User Service - Manage Telegram users in the database.

Handles user creation, retrieval, and updates.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.database.base import get_session_context
from src.database.models import User


class UserService:
    """Service for managing Telegram users."""

    async def get_or_create_user(
        self,
        telegram_user_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> User:
        """
        Get existing user or create new one if doesn't exist.

        Args:
            telegram_user_id: Telegram's unique user ID
            first_name: User's first name
            last_name: User's last name (optional)
            username: Telegram username (optional)
            language_code: User's language code (e.g., 'es', 'en')

        Returns:
            User: The user object (existing or newly created)

        Raises:
            ValueError: If telegram_user_id is invalid
            SQLAlchemyError: If database operation fails
        """
        if telegram_user_id <= 0:
            raise ValueError(f"Invalid telegram_user_id: {telegram_user_id}")

        with get_session_context() as session:
            # Try to get existing user
            stmt = select(User).where(User.telegram_user_id == telegram_user_id)
            result = session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Update last_interaction_at
                user.last_interaction_at = datetime.now(timezone.utc)

                # Update user info if changed
                if user.first_name != first_name:
                    user.first_name = first_name
                if user.last_name != last_name:
                    user.last_name = last_name
                if user.username != username:
                    user.username = username
                if user.language_code != language_code:
                    user.language_code = language_code

                session.commit()
                session.refresh(user)
                return user

            # Create new user
            new_user = User(
                telegram_user_id=telegram_user_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                language_code=language_code,
                is_active=True,
            )

            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            return new_user

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """
        Get user by Telegram ID.

        Args:
            telegram_user_id: Telegram's unique user ID

        Returns:
            User if found, None otherwise
        """
        with get_session_context() as session:
            stmt = select(User).where(User.telegram_user_id == telegram_user_id)
            result = session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_last_interaction(self, user_id: int) -> None:
        """
        Update user's last_interaction_at timestamp.

        Args:
            user_id: Database user ID
        """
        with get_session_context() as session:
            stmt = select(User).where(User.id == user_id)
            result = session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.last_interaction_at = datetime.now(timezone.utc)
                session.commit()

    async def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user (soft delete for GDPR compliance).

        Args:
            user_id: Database user ID

        Returns:
            True if user was deactivated, False if not found
        """
        with get_session_context() as session:
            stmt = select(User).where(User.id == user_id)
            result = session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.is_active = False
                session.commit()
                return True

            return False

    async def get_active_users_count(self) -> int:
        """
        Get count of active users.

        Returns:
            Number of active users
        """
        with get_session_context() as session:
            stmt = select(User).where(User.is_active == True)
            result = session.execute(stmt)
            return len(result.all())
