"""
Conversational RAG - Sistema RAG con Persistencia de Contexto
=============================================================

Implementa un sistema RAG conversacional que mantiene el historial de chat
por sesión, permitiendo conversaciones multi-turn coherentes.

Características:
- Persistencia de contexto por session_id
- History-aware retriever que reformula queries basándose en el historial
- Memoria en RAM (puede extenderse a Redis/PostgreSQL)
- Compatible con LangChain RunnableWithMessageHistory
"""

from typing import Dict, List, Any, Optional, Tuple
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory


class InMemorySessionStore:
    """
    Almacenamiento en memoria de historiales de chat por sesión.
    
    Para producción, considerar usar:
    - Redis para persistencia distribuida
    - PostgreSQL para almacenamiento permanente
    - MongoDB para documentos flexibles
    """
    
    def __init__(self):
        """Inicializa el store vacío"""
        self.store: Dict[str, ChatMessageHistory] = {}
    
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        Obtiene o crea el historial de una sesión.
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            ChatMessageHistory para esa sesión
        """
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
    
    def clear_session(self, session_id: str):
        """Limpia el historial de una sesión específica"""
        if session_id in self.store:
            del self.store[session_id]
    
    def clear_all(self):
        """Limpia todos los historiales (útil para testing)"""
        self.store.clear()
    
    def get_session_count(self) -> int:
        """Retorna el número de sesiones activas"""
        return len(self.store)
    
    def get_all_session_ids(self) -> List[str]:
        """Retorna lista de todos los session_ids activos"""
        return list(self.store.keys())


class ConversationalRAGEngine:
    """
    Motor RAG conversacional con persistencia de contexto.
    
    Mantiene el historial de conversación por sesión y usa ese contexto
    para reformular preguntas y generar respuestas más coherentes.
    """
    
    def __init__(
        self,
        base_rag_engine,
        model_wrapper,
        system_prompt: Optional[str] = None
    ):
        """
        Inicializa el motor conversacional.
        
        Args:
            base_rag_engine: Engine RAG base (ej: EnhancedRAGEngineNew)
            model_wrapper: Wrapper del modelo LLM
            system_prompt: Prompt del sistema (opcional)
        """
        self.base_rag = base_rag_engine
        self.model = model_wrapper
        self.session_store = InMemorySessionStore()
        
        # System prompt default para DNI
        self.system_prompt = system_prompt or """Eres el asistente virtual de DNI (Damos Nuestra Ilusión), una asociación de voluntariado juvenil en Valencia.

Tu misión es ayudar a los usuarios con información sobre:
- Proyectos de voluntariado (desayunos solidarios, abuelitos, refuerzo escolar, kayak, DANA)
- Cómo participar y requisitos
- Horarios y ubicaciones
- Contacto y redes sociales

Responde de forma amigable, clara y concisa. Si no tienes información específica, indica que pueden contactar por WhatsApp (962 025 978 / 647 440 275) o Instagram [@dnivalenciaa](https://www.instagram.com/dnivalenciaa?igsh=MWRicTFocW5jODN6NQ==).

Basándote en este contexto recuperado, responde a la pregunta del usuario:
{context}"""
        
        # Crear prompts
        self._setup_prompts()
        
        print("✅ Conversational RAG Engine inicializado")
    
    def _setup_prompts(self):
        """Configura los prompts para history-aware retrieval"""
        
        # Prompt para reformular pregunta basándose en historial
        self.contextualize_prompt = ChatPromptTemplate.from_messages([
            ("system", """Dada una conversación y la última pregunta del usuario (que puede referirse al contexto anterior), 
reformula la pregunta para que sea independiente y contenga toda la información necesaria para buscar documentos relevantes.

NO respondas la pregunta, solo reformúlala para que sea auto-contenida.

Ejemplos:
- Si el usuario pregunta "¿y cuándo es?" después de hablar de desayunos, reformula a "¿Cuándo son los desayunos solidarios?"
- Si pregunta "dime más" después de hablar de DNI, reformula a "Dame más información sobre DNI (Damos Nuestra Ilusión)"
- Si pregunta "¿cómo me apunto?" sin contexto previo, déjala igual"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Prompt para generar respuesta final
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
    
    def process_query(
        self,
        query: str,
        session_id: str,
        question_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Procesa una query considerando el historial de conversación.
        
        Args:
            query: Pregunta del usuario
            session_id: ID de la sesión para persistencia de contexto
            question_id: ID opcional para tracking
            
        Returns:
            Dict con respuesta, contexto, confidence, etc.
        """
        # Obtener historial de la sesión
        session_history = self.session_store.get_session_history(session_id)
        messages = session_history.messages
        
        # Añadir contexto conversacional al query (NO reformular, solo añadir contexto)
        query_for_retrieval = query
        if messages and len(messages) >= 2:
            # Obtener el último par pregunta-respuesta para contexto
            last_question = None
            last_answer = None
            
            for msg in reversed(messages):
                if msg.type == 'ai' and last_answer is None:
                    last_answer = str(msg.content)[:150]  # Limitar contexto
                elif msg.type == 'human' and last_question is None:
                    last_question = str(msg.content)
                    
                if last_question and last_answer:
                    break
            
            if last_question and last_answer:
                print(f"   📚 Contexto previo: '{last_question[:50]}...'")
                # Añadir contexto al query sin reformular completamente
                query_for_retrieval = f"Contexto: Estábamos hablando de: {last_question}. Nueva pregunta: {query}"
        
        # Determinar si hay contexto conversacional ANTES de procesar
        has_context = len(messages) > 0

        # DEBUG: Log para verificar detección de contexto
        if has_context:
            print(f"   🔄 Conversación en curso detectada ({len(messages)} mensajes previos)")
        else:
            print(f"   🆕 Primera pregunta de la sesión")

        # SIEMPRE usar el método avanzado del RAG
        if not question_id:
            question_id = 0  # Default para asegurar que se usa el método avanzado

        # Usar el RAG avanzado con validación
        if hasattr(self.base_rag, 'process_query_with_validation'):
            print(f"   🚀 Usando RAG avanzado con validación...")
            result = self.base_rag.process_query_with_validation(
                question=query_for_retrieval,
                question_id=question_id
            )
        else:
            # Fallback: usar proceso_query estándar del RAG base
            print(f"   ⚠️ Fallback a RAG estándar...")

            # Recuperar con TODOS los parámetros del enhanced RAG
            chunks = self.base_rag.base_rag.retrieve(query_for_retrieval)

            # Extraer contenido de chunks
            chunk_contents = []
            for c in chunks:
                if isinstance(c, dict):
                    chunk_contents.append(c.get('content', str(c)))
                elif hasattr(c, 'page_content'):
                    chunk_contents.append(c.page_content)
                else:
                    chunk_contents.append(str(c))

            # Usar MÁS contexto (top 10 chunks en lugar de 5)
            context_str = "\n\n".join(chunk_contents[:10])

            # Prompt mejorado con instrucciones más específicas y saludos variados
            if has_context:
                # Si ya hay conversación, NO usar "Hola" repetidamente
                # Ser más explícito en las instrucciones
                system_prompt = """Eres el asistente virtual de DNI (Damos Nuestra Ilusión).

⚠️⚠️⚠️ REGLA CRÍTICA - PROHIBIDO SALUDAR ⚠️⚠️⚠️
Esta es una conversación en curso. El usuario YA recibió un saludo.
- ABSOLUTAMENTE PROHIBIDO usar: "Hola", "Buenas", "Bienvenido", "¡Hola!", "Qué tal", "Encantado", ni NINGÚN saludo similar
- NO te presentes de nuevo
- COMIENZA DIRECTAMENTE con el contenido de la respuesta
- Usa conectores naturales como: "Sobre", "En cuanto a", "Respecto a", "Claro", "Por supuesto"

EJEMPLOS CORRECTOS de cómo empezar tu respuesta:
✅ "Sobre la edad, DNI está enfocado..."
✅ "Entiendo tu pregunta. DNI es una asociación..."
✅ "En cuanto a la filosofía, nos basamos en..."
✅ "Por supuesto. El voluntariado en DNI..."

EJEMPLOS INCORRECTOS (PROHIBIDOS):
❌ "¡Hola! Sobre la edad..."
❌ "Buenas. DNI es..."
❌ "¡Hola! Entiendo tu pregunta..."

Responde basándote ÚNICAMENTE en el contexto proporcionado.
Si el contexto no contiene la información, di que no tienes esa información específica.
Sé preciso, detallado y cita información relevante del contexto.

Contexto:
{context}

Pregunta: {question}

Respuesta (COMIENZA DIRECTAMENTE con el contenido, SIN NINGÚN SALUDO):"""
            else:
                # Primera pregunta: saludo breve y amigable
                system_prompt = """Eres el asistente virtual de DNI (Damos Nuestra Ilusión).

Esta es la primera pregunta del usuario. Comienza con un saludo breve y amigable, luego responde.

Responde basándote ÚNICAMENTE en el contexto proporcionado.
Si el contexto no contiene la información, di que no tienes esa información específica.
Sé preciso, detallado y cita información relevante del contexto.

Contexto:
{context}

Pregunta: {question}

Respuesta (saludo breve + contenido):"""

            prompt = system_prompt.format(context=context_str, question=query)
            answer = self.model.generate(prompt, temperature=0.2)  # Temperatura más baja para más precisión

            # Calcular confidence correctamente
            if hasattr(self.base_rag, 'calculate_confidence_score'):
                confidence = self.base_rag.calculate_confidence_score(
                    chunks, answer, query
                )
            else:
                # Calcular confidence básico aquí
                confidence = 0.7 if len(answer) > 50 else 0.5

            result = {
                'question': query,
                'answer': answer,
                'contexts': chunk_contents,
                'confidence': confidence
            }

        # POST-PROCESAMIENTO: Eliminar saludos si hay contexto conversacional
        # IMPORTANTE: Aplicar DESPUÉS de obtener result, independientemente del método usado
        if has_context and result and 'answer' in result and result['answer']:
            original_answer = result['answer']
            cleaned_answer = self._remove_unwanted_greetings(original_answer)
            result['answer'] = cleaned_answer

        # Añadir query y respuesta al historial
        session_history.add_user_message(query)
        session_history.add_ai_message(result['answer'])
        
        return result
    
    def _remove_unwanted_greetings(self, answer: str) -> str:
        """
        Elimina saludos no deseados del inicio de la respuesta.

        Args:
            answer: Respuesta generada por el modelo

        Returns:
            Respuesta sin saludos iniciales
        """
        import re

        # Lista de patrones de saludos a eliminar (case-insensitive)
        # Incluye puntuación opcional después del saludo
        greeting_patterns = [
            r'^¡?Hola!?[,.\s]*',
            r'^¡?Buenas!?[,.\s]*',
            r'^¡?Buenos días!?[,.\s]*',
            r'^¡?Buenas tardes!?[,.\s]*',
            r'^¡?Buenas noches!?[,.\s]*',
            r'^¡?Bienvenido!?[,.\s]*',
            r'^¡?Bienvenida!?[,.\s]*',
            r'^¡?Qué tal!?[,.\s]*',
            r'^¡?Encantado!?[,.\s]*',
            r'^¡?Encantada!?[,.\s]*',
            # Frases de apertura que son saludos implícitos
            r'^¡?Me alegra que[^.!?]*[.!?]\s*',
            r'^¡?Qué bien que[^.!?]*[.!?]\s*',
            r'^¡?Genial que[^.!?]*[.!?]\s*',
            r'^¡?Es un placer[^.!?]*[.!?]\s*',
        ]

        cleaned_answer = answer.strip()
        original_answer = cleaned_answer

        # Aplicar cada patrón para eliminar saludos
        for pattern in greeting_patterns:
            cleaned_answer = re.sub(pattern, '', cleaned_answer, flags=re.IGNORECASE)

        # Limpiar puntuación suelta al inicio (., ,, etc.)
        cleaned_answer = re.sub(r'^[,.\s]+', '', cleaned_answer)

        # Limpiar espacios extras
        cleaned_answer = cleaned_answer.strip()

        # Si eliminamos el saludo, capitalizar la primera letra si es necesario
        if cleaned_answer and cleaned_answer != original_answer:
            # Capitalizar primera letra si no lo está
            if cleaned_answer[0].islower():
                cleaned_answer = cleaned_answer[0].upper() + cleaned_answer[1:]

            print(f"   ✂️  Saludo eliminado del inicio de la respuesta")

        return cleaned_answer

    def _reformulate_query(self, query: str, chat_history: List) -> str:
        """
        Reformula una query basándose en el historial de chat.
        
        Args:
            query: Query original
            chat_history: Historial de mensajes
            
        Returns:
            Query reformulada
        """
        # Construir contexto del historial (últimos 4 mensajes)
        history_context = []
        for msg in chat_history[-4:]:
            role = "Usuario" if msg.type == "human" else "Asistente"
            # Asegurar que content es string
            content = str(msg.content) if msg.content else ""
            history_context.append(f"{role}: {content}")
        
        history_str = "\n".join(history_context)
        
        # Prompt para reformular
        reformulation_prompt = f"""Historial de conversación:
{history_str}

Nueva pregunta del usuario: {query}

Reformula la pregunta para que sea independiente y contenga toda la información necesaria.
Si la pregunta ya es independiente, devuélvela sin cambios.

Pregunta reformulada:"""
        
        try:
            reformulated = self.model.generate(reformulation_prompt, temperature=0.1)
            # Limpiar respuesta
            reformulated = str(reformulated).strip()
            
            # Si la reformulación es muy larga o parece una respuesta en lugar de pregunta, usar original
            if len(reformulated) > len(query) * 3 or not any(q in reformulated.lower() for q in ['?', 'cuándo', 'dónde', 'cómo', 'qué', 'quién']):
                return query
            
            return reformulated
        except Exception as e:
            print(f"   ⚠️ Error reformulando query: {e}")
            return query
    
    def clear_session(self, session_id: str):
        """Limpia el historial de una sesión"""
        self.session_store.clear_session(session_id)
        print(f"   🗑️  Sesión {session_id} limpiada")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Obtiene el historial de una sesión en formato legible.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Lista de mensajes con role y content
        """
        session_history = self.session_store.get_session_history(session_id)
        
        messages = []
        for msg in session_history.messages:
            messages.append({
                'role': 'user' if msg.type == 'human' else 'assistant',
                'content': msg.content
            })
        
        return messages
    
    def get_active_sessions(self) -> Dict[str, int]:
        """
        Retorna información sobre sesiones activas.
        
        Returns:
            Dict con session_id y número de mensajes
        """
        sessions_info = {}
        
        for session_id in self.session_store.get_all_session_ids():
            history = self.session_store.get_session_history(session_id)
            sessions_info[session_id] = len(history.messages)
        
        return sessions_info


if __name__ == "__main__":
    # Testing del sistema conversacional
    print("=== TESTING CONVERSATIONAL RAG ===\n")
    
    # Mock de componentes para testing
    class MockRAGEngine:
        def __init__(self):
            self.base_rag = self
        
        def retrieve(self, query):
            return [{'content': f"Información sobre: {query}"}]
    
    class MockModel:
        def generate(self, prompt, temperature=0.3):
            return "Respuesta simulada del modelo"
    
    # Crear engine conversacional
    mock_rag = MockRAGEngine()
    mock_model = MockModel()
    conv_rag = ConversationalRAGEngine(mock_rag, mock_model)
    
    # Simular conversación
    session_id = "test_session_123"
    
    print("Usuario: ¿Qué es DNI?")
    result1 = conv_rag.process_query("¿Qué es DNI?", session_id)
    print(f"Asistente: {result1['answer']}")
    print(f"Confidence: {result1.get('confidence', 'N/A')}\n")
    
    print("Usuario: ¿Cómo me apunto?")
    result2 = conv_rag.process_query("¿Cómo me apunto?", session_id)
    print(f"Asistente: {result2['answer']}\n")
    
    print("Usuario: ¿y cuándo es?")  # Query que necesita contexto
    result3 = conv_rag.process_query("¿y cuándo es?", session_id)
    print(f"Asistente: {result3['answer']}\n")
    
    # Mostrar historial
    print("=== HISTORIAL DE SESIÓN ===")
    history = conv_rag.get_session_history(session_id)
    for i, msg in enumerate(history, 1):
        print(f"{i}. [{msg['role']}]: {msg['content'][:50]}...")
    
    print(f"\n✅ Sesiones activas: {conv_rag.session_store.get_session_count()}")

