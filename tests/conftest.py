"""
Root conftest.py - Shared fixtures for all test suites.

Provides:
- Database fixtures (SQLite in-memory for tests)
- Service layer fixtures
- RAG/Model mock fixtures
- Telegram mock fixtures
- Security SDK fixtures
- Skip conditions for external dependencies
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Skip conditions
# ---------------------------------------------------------------------------

requires_ollama = pytest.mark.skipif(
    os.getenv("SKIP_OLLAMA", "1") == "1",
    reason="Requires Ollama UPV server (set SKIP_OLLAMA=0 to enable)",
)

requires_postgres = pytest.mark.skipif(
    os.getenv("SKIP_POSTGRES", "1") == "1",
    reason="Requires PostgreSQL (set SKIP_POSTGRES=0 to enable)",
)


# ---------------------------------------------------------------------------
# Database fixtures (SQLite in-memory)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    from sqlalchemy import create_engine

    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Import models to register with Base, then create tables
    from src.database.base import Base
    from src.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """
    Provide a transactional database session that rolls back after each test.

    This ensures test isolation without leaving residual data.
    """
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = Session()
    yield session
    session.rollback()
    session.close()


# ---------------------------------------------------------------------------
# Service layer fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_service(db_session):
    """UserService with test database session."""
    from tests.fixtures.mock_services import create_user_service
    return create_user_service(db_session)


@pytest.fixture
def conversation_service(db_session):
    """ConversationService with test database session."""
    from tests.fixtures.mock_services import create_conversation_service
    return create_conversation_service(db_session)


@pytest.fixture
def message_service(db_session):
    """MessageService with test database session."""
    from tests.fixtures.mock_services import create_message_service
    return create_message_service(db_session)


@pytest.fixture
def context_service(db_session):
    """ContextService with test database session."""
    from tests.fixtures.mock_services import create_context_service
    return create_context_service(db_session)


# ---------------------------------------------------------------------------
# RAG / Model mock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_model_wrapper():
    """Mock LLMWrapper that returns predefined responses without calling Ollama."""
    from tests.fixtures.mock_services import MockModelWrapper
    return MockModelWrapper()


@pytest.fixture
def mock_rag_engine():
    """Mock RAG engine that returns predefined results without ChromaDB or Ollama."""
    from tests.fixtures.mock_services import MockRAGEngine
    return MockRAGEngine()


# ---------------------------------------------------------------------------
# Telegram mock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_telegram_user():
    """Mock Telegram User object."""
    user = MagicMock()
    user.id = 123456789
    user.first_name = "TestUser"
    user.last_name = "Apellido"
    user.username = "testuser"
    user.language_code = "es"
    return user


@pytest.fixture
def mock_telegram_chat():
    """Mock Telegram Chat object."""
    chat = MagicMock()
    chat.id = 123456789
    chat.type = "private"
    chat.send_action = AsyncMock()
    return chat


@pytest.fixture
def mock_telegram_message(mock_telegram_user, mock_telegram_chat):
    """Mock Telegram Message object."""
    message = MagicMock()
    message.from_user = mock_telegram_user
    message.chat = mock_telegram_chat
    message.text = "Hola, quiero saber sobre los desayunos solidarios"
    message.message_id = 42
    message.reply_text = AsyncMock()
    return message


@pytest.fixture
def mock_update(mock_telegram_message):
    """Mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = mock_telegram_message.from_user
    update.effective_chat = mock_telegram_message.chat
    update.message = mock_telegram_message
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    """Mock Telegram CallbackContext."""
    ctx = MagicMock()
    ctx.bot = MagicMock()
    ctx.bot.send_message = AsyncMock()
    ctx.user_data = {}
    ctx.chat_data = {}
    return ctx


# ---------------------------------------------------------------------------
# Security SDK fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def injection_detector():
    """InjectionDetector instance for testing."""
    from vicente_rag.security import InjectionDetector
    return InjectionDetector(debug=False)


@pytest.fixture
def sanitizer():
    """Sanitizer instance for testing."""
    from vicente_rag.security import Sanitizer
    return Sanitizer(debug=False)


@pytest.fixture
def risk_scorer():
    """RiskScorer instance for testing."""
    from vicente_rag.security import RiskScorer
    return RiskScorer(debug=False)
