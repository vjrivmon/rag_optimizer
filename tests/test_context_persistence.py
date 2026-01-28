"""
Test de Persistencia de Contexto Conversacional
===============================================

Simula conversaciones reales para verificar que el contexto
se mantiene correctamente a lo largo de múltiples preguntas.
"""

import sys
from pathlib import Path

# Añadir path del proyecto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.core.conversational_rag import ConversationalRAGEngine


def print_separator(title=""):
    """Imprime separador visual"""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)
    print()


def simulate_conversation_about_desayunos():
    """
    Simula la conversación problemática sobre desayunos solidarios.
    """
    print_separator("TEST: CONVERSACIÓN SOBRE DESAYUNOS SOLIDARIOS")

    # Inicializar componentes
    DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"
    VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"

    print("🔧 Inicializando sistema...")
    model = LLMWrapper(
        model_name="gemma2:27b",
        api_endpoint=DEFAULT_API_ENDPOINT
    )

    rag_engine = EnhancedRAGEngineNew(
        vector_store_path=str(VECTOR_STORE_PATH),
        model=model
    )

    conv_rag = ConversationalRAGEngine(
        base_rag_engine=rag_engine,
        model_wrapper=model
    )

    print("✅ Sistema inicializado\n")

    # ID de sesión único para esta conversación
    session_id = "test_session_desayunos"

    # Conversación simulada
    conversation = [
        ("¿Qué es DNI?", "Debe responder sobre DNI en general"),
        ("¿Cómo me puedo apuntar a la actividad de desayunos?", "Debe explicar cómo apuntarse a DESAYUNOS"),
        ("¿Cuánto dura la actividad?", "❗ Debe mantener contexto: DESAYUNOS"),
        ("¿y qué se hace?", "❗ Debe mantener contexto: DESAYUNOS (actividad en sí)"),
        ("¿quién compra los alimentos?", "❗❗ CRÍTICO: Debe responder sobre DESAYUNOS específicamente"),
    ]

    results = []

    for i, (question, expected_behavior) in enumerate(conversation, 1):
        print_separator(f"PREGUNTA {i}/{len(conversation)}")

        print(f"👤 Usuario: {question}")
        print(f"📝 Comportamiento esperado: {expected_behavior}")
        print()

        # Procesar pregunta
        result = conv_rag.process_query(
            query=question,
            session_id=session_id,
            question_id=i
        )

        answer = result.get('answer', 'Sin respuesta')
        confidence = result.get('confidence', 0.0)

        print(f"\n🤖 Asistente:\n{answer}\n")
        print(f"📊 Confidence: {confidence:.2f}")

        # Evaluar si mantiene contexto en preguntas críticas
        is_critical = "❗" in expected_behavior
        maintains_context = None

        if is_critical:
            # Verificar si la respuesta menciona "desayuno" o contexto relevante
            answer_lower = answer.lower()

            # Palabras clave que indican contexto de desayunos
            desayuno_keywords = ['desayuno', 'desayunos', 'sábado', 'bocadillo', 'repartir']

            found_keywords = [kw for kw in desayuno_keywords if kw in answer_lower]
            maintains_context = len(found_keywords) > 0

            if maintains_context:
                print(f"✅ CONTEXTO MANTENIDO (palabras: {', '.join(found_keywords)})")
            else:
                print(f"❌ CONTEXTO PERDIDO (no menciona desayunos específicamente)")

                # Verificar si menciona otros proyectos (indicio de pérdida de contexto)
                other_projects = ['cena', 'coles', 'resis', 'abuelito', 'kayak', 'dana']
                mentioned_others = [proj for proj in other_projects if proj in answer_lower]
                if mentioned_others:
                    print(f"   ⚠️ Menciona otros proyectos: {', '.join(mentioned_others)}")

        results.append({
            'question': question,
            'answer': answer,
            'confidence': confidence,
            'is_critical': is_critical,
            'maintains_context': maintains_context
        })

        print()

    # RESUMEN FINAL
    print_separator("RESUMEN DE RESULTADOS")

    critical_questions = [r for r in results if r['is_critical']]
    successful = [r for r in critical_questions if r['maintains_context']]

    print(f"Total de preguntas: {len(results)}")
    print(f"Preguntas críticas: {len(critical_questions)}")
    print(f"Contexto mantenido: {len(successful)}/{len(critical_questions)}")

    success_rate = len(successful) / len(critical_questions) * 100 if critical_questions else 0
    print(f"\n📈 Tasa de éxito: {success_rate:.1f}%\n")

    if success_rate >= 80:
        print("✅ PRUEBA EXITOSA - El sistema mantiene bien el contexto")
    elif success_rate >= 50:
        print("⚠️ PRUEBA PARCIAL - El sistema mantiene contexto parcialmente")
    else:
        print("❌ PRUEBA FALLIDA - El sistema NO mantiene el contexto adecuadamente")

    # Detalles de fallos
    failed = [r for r in critical_questions if not r['maintains_context']]
    if failed:
        print("\n❌ Preguntas donde se perdió el contexto:")
        for r in failed:
            print(f"   - {r['question']}")

    print()

    return success_rate >= 80


def test_project_switching():
    """
    Prueba cambio entre proyectos.
    """
    print_separator("TEST: CAMBIO ENTRE PROYECTOS")

    # Inicializar componentes
    DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"
    VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"

    print("🔧 Inicializando sistema...")
    model = LLMWrapper(
        model_name="gemma2:27b",
        api_endpoint=DEFAULT_API_ENDPOINT
    )

    rag_engine = EnhancedRAGEngineNew(
        vector_store_path=str(VECTOR_STORE_PATH),
        model=model
    )

    conv_rag = ConversationalRAGEngine(
        base_rag_engine=rag_engine,
        model_wrapper=model
    )

    print("✅ Sistema inicializado\n")

    session_id = "test_session_switching"

    conversation = [
        ("¿Cómo funcionan los desayunos solidarios?", "desayunos"),
        ("¿Cuánto dura?", "desayunos"),
        ("Y sobre el refuerzo escolar, ¿qué necesito?", "coles"),  # Cambio explícito
        ("¿Qué días vais?", "coles"),  # Debe mantener COLES
    ]

    for i, (question, expected_project) in enumerate(conversation, 1):
        print(f"\n{'='*80}")
        print(f"PREGUNTA {i}: {question}")
        print(f"Proyecto esperado: {expected_project.upper()}")
        print('='*80 + '\n')

        result = conv_rag.process_query(
            query=question,
            session_id=session_id,
            question_id=i
        )

        print(f"\n🤖 Respuesta:\n{result.get('answer', '')[:300]}...\n")

    print("\n✅ Test de cambio de proyecto completado")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  SUITE DE TESTS: PERSISTENCIA DE CONTEXTO")
    print("="*80 + "\n")

    # Test 1: Conversación sobre desayunos (caso problemático original)
    test1_success = simulate_conversation_about_desayunos()

    # Test 2: Cambio entre proyectos
    # test_project_switching()  # Comentar si solo quieres test 1

    # Resultado final
    print("\n" + "="*80)
    print("  RESULTADO FINAL")
    print("="*80 + "\n")

    if test1_success:
        print("✅ TODOS LOS TESTS PASADOS")
    else:
        print("❌ ALGUNOS TESTS FALLARON")

    print()
