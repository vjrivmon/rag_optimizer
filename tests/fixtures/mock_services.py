"""
Mock services for testing without external dependencies (Ollama, PostgreSQL).

Provides:
- MockModelWrapper: Returns predefined responses without calling Ollama
- MockRAGEngine: Returns predefined results without ChromaDB or Ollama
- Service factories for database-backed services with injected sessions
"""

from typing import Dict, Any, Optional
from unittest.mock import MagicMock

from tests.fixtures.sample_data import SAMPLE_RAG_RESPONSE, SAMPLE_CHUNKS


# ---------------------------------------------------------------------------
# Mock LLM Wrapper
# ---------------------------------------------------------------------------

class MockModelWrapper:
    """
    Mock LLMWrapper that returns predefined responses.

    Mimics the interface of src.core.model_wrapper.LLMWrapper
    without making any HTTP calls to the Ollama server.
    """

    def __init__(self, model_name: str = "mock-model"):
        self.model_name = model_name
        self.api_endpoint = "http://mock:11434/api/generate"
        self.context_window = 2048
        self._call_count = 0

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        top_p: float = 0.9,
        max_tokens: int = 512,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Return a canned response."""
        self._call_count += 1

        # Simple keyword-based response selection
        prompt_lower = prompt.lower()

        if "desayuno" in prompt_lower:
            answer = (
                "Los Desayunos Solidarios son un proyecto de DNI donde "
                "los voluntarios preparan y reparten desayunos a personas "
                "sin hogar los sábados a las 8 de la mañana."
            )
        elif "resis" in prompt_lower or "abuelito" in prompt_lower:
            answer = (
                "RESIS es el proyecto de Charlas con Abuelitos de DNI, "
                "donde voluntarios visitan la residencia L'Acollida."
            )
        elif "coles" in prompt_lower or "refuerzo" in prompt_lower:
            answer = (
                "COLES es el proyecto de Refuerzo Escolar de DNI, "
                "donde voluntarios ayudan a niños con sus deberes."
            )
        else:
            answer = (
                "DNI (Damos Nuestra Ilusión) es una asociación de jóvenes "
                "voluntarios en Valencia con el lema PARA. MIRA. AYUDA."
            )

        return {
            "response": answer,
            "answer": answer,
            "thinking": None,
            "model": self.model_name,
            "latency": 0.05,
            "success": True,
            "done": True,
            "total_duration": 0.05,
        }


# ---------------------------------------------------------------------------
# Mock RAG Engine
# ---------------------------------------------------------------------------

class MockRAGEngine:
    """
    Mock EnhancedRAGEngineNew that returns predefined results.

    Mimics the interface of src.core.enhanced_rag_engine_new.EnhancedRAGEngineNew
    without requiring ChromaDB vector store or LLM calls.
    """

    def __init__(self):
        self._call_count = 0
        self.model = MockModelWrapper()

    def process_query_with_validation(
        self,
        question: str,
        question_id: int = 0,
        max_attempts: int = 3,
        min_confidence: float = 0.8,
    ) -> Dict[str, Any]:
        """Return a canned RAG result."""
        self._call_count += 1
        return dict(SAMPLE_RAG_RESPONSE)

    def process_query(
        self,
        question: str,
        question_id: int = 0,
    ) -> Dict[str, Any]:
        """Alias for simpler calls."""
        return self.process_query_with_validation(question, question_id)


# ---------------------------------------------------------------------------
# Service factories (inject test session)
# ---------------------------------------------------------------------------

def create_user_service(session):
    """
    Create a UserService that uses the given test session.

    Since the real UserService uses get_session_context(), we
    patch it to use our test session instead.
    """
    from src.services.user_service import UserService

    service = UserService.__new__(UserService)
    service._session = session
    return service


def create_conversation_service(session):
    """Create a ConversationService with injected test session."""
    from src.services.conversation_service import ConversationService

    service = ConversationService.__new__(ConversationService)
    service._session = session
    return service


def create_message_service(session):
    """Create a MessageService with injected test session."""
    from src.services.message_service import MessageService

    service = MessageService.__new__(MessageService)
    service._session = session
    return service


def create_context_service(session):
    """Create a ContextService with injected test session."""
    from src.services.context_service import ContextService

    service = ContextService.__new__(ContextService)
    service._session = session
    return service
