"""
Benchmark de Persistencia de Contexto
=====================================

Evalúa la capacidad del sistema para mantener contexto conversacional
cuando las preguntas NO mencionan explícitamente el tema/proyecto.

Metodología:
1. Primera pregunta menciona explícitamente el proyecto/tema
2. Preguntas siguientes son ambiguas (no mencionan el proyecto)
3. Se evalúa si el sistema mantiene el contexto correctamente
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Añadir path del proyecto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.core.conversational_rag import ConversationalRAGEngine


# ============================================================================
# CONVERSACIONES DE PRUEBA
# ============================================================================

BENCHMARK_CONVERSATIONS = [
    {
        "id": "conv_desayunos_1",
        "name": "Desayunos Solidarios - Información Básica",
        "conversation": [
            {
                "question": "¿Cómo me puedo apuntar a la actividad de desayunos solidarios?",
                "context_explicit": True,
                "expected_keywords": ["desayuno", "formulario", "miércoles", "sábado"],
                "expected_project": "Desayunos Solidarios"
            },
            {
                "question": "¿Cuánto dura la actividad?",
                "context_explicit": False,
                "expected_keywords": ["desayuno", "hora", "1.5", "noventa", "minutos"],
                "expected_project": "Desayunos Solidarios"
            },
            {
                "question": "¿y qué se hace?",
                "context_explicit": False,
                "expected_keywords": ["desayuno", "repartir", "bocadillo", "café", "personas"],
                "expected_project": "Desayunos Solidarios"
            },
            {
                "question": "¿quién compra los alimentos?",
                "context_explicit": False,
                "expected_keywords": ["desayuno", "dni", "asociación", "compra"],
                "expected_project": "Desayunos Solidarios",
                "critical": True  # Pregunta crítica reportada
            }
        ]
    },
    {
        "id": "conv_desayunos_2",
        "name": "Desayunos Solidarios - Horarios y Ubicación",
        "conversation": [
            {
                "question": "¿Cuándo son los desayunos solidarios?",
                "context_explicit": True,
                "expected_keywords": ["sábado", "mañana", "8"],
                "expected_project": "Desayunos Solidarios"
            },
            {
                "question": "¿Dónde quedamos?",
                "context_explicit": False,
                "expected_keywords": ["sagunt", "177", "carrer", "punto", "encuentro"],
                "expected_project": "Desayunos Solidarios"
            },
            {
                "question": "¿Qué pasa si llueve?",
                "context_explicit": False,
                "expected_keywords": ["desayuno", "avisa", "suspende", "comunicar"],
                "expected_project": "Desayunos Solidarios"
            }
        ]
    },
    {
        "id": "conv_resis_1",
        "name": "Charlas con Abuelitos (RESIS) - Información Básica",
        "conversation": [
            {
                "question": "¿Cómo funcionan las charlas con abuelitos en la residencia?",
                "context_explicit": True,
                "expected_keywords": ["abuelito", "residencia", "l'acollida", "charlas"],
                "expected_project": "Charlas con Abuelitos"
            },
            {
                "question": "¿Qué días vais?",
                "context_explicit": False,
                "expected_keywords": ["jueves", "tarde", "residencia"],
                "expected_project": "Charlas con Abuelitos"
            },
            {
                "question": "¿Qué tipo de conversaciones se tienen?",
                "context_explicit": False,
                "expected_keywords": ["abuelito", "vida", "escuchar", "compañía"],
                "expected_project": "Charlas con Abuelitos"
            }
        ]
    },
    {
        "id": "conv_coles_1",
        "name": "Refuerzo Escolar (COLES) - Información Básica",
        "conversation": [
            {
                "question": "¿Cómo funciona el refuerzo escolar COLES?",
                "context_explicit": True,
                "expected_keywords": ["refuerzo", "escolar", "coles", "niños", "deberes"],
                "expected_project": "Refuerzo Escolar"
            },
            {
                "question": "¿Qué días se hace?",
                "context_explicit": False,
                "expected_keywords": ["martes", "jueves", "tarde", "semana"],
                "expected_project": "Refuerzo Escolar"
            },
            {
                "question": "¿Necesito ser bueno en matemáticas?",
                "context_explicit": False,
                "expected_keywords": ["refuerzo", "matemáticas", "paciencia", "ayudar"],
                "expected_project": "Refuerzo Escolar"
            }
        ]
    },
    {
        "id": "conv_compromiso_1",
        "name": "Compromiso de Asistencia - Caso General",
        "conversation": [
            {
                "question": "Me gustaría participar en los desayunos solidarios, pero tengo una duda",
                "context_explicit": True,
                "expected_keywords": ["desayuno", "participar", "duda"],
                "expected_project": "Desayunos Solidarios"
            },
            {
                "question": "¿Si me apunto un día tengo que ir el resto?",
                "context_explicit": False,
                "expected_keywords": ["desayuno", "compromiso", "flexible", "apuntar"],
                "expected_project": "Desayunos Solidarios"
            }
        ]
    }
]


# ============================================================================
# EVALUADOR DE CONTEXTO
# ============================================================================

class ContextPersistenceEvaluator:
    """Evaluador de persistencia de contexto"""

    def __init__(self):
        self.model = None
        self.rag_engine = None
        self.conv_rag = None

    def initialize_system(self):
        """Inicializa el sistema RAG conversacional"""
        print("🔧 Inicializando sistema...")

        DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"
        VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"

        self.model = LLMWrapper(
            model_name="gemma2:27b",
            api_endpoint=DEFAULT_API_ENDPOINT
        )

        self.rag_engine = EnhancedRAGEngineNew(
            vector_store_path=str(VECTOR_STORE_PATH),
            model=self.model
        )

        self.conv_rag = ConversationalRAGEngine(
            base_rag_engine=self.rag_engine,
            model_wrapper=self.model
        )

        print("✅ Sistema inicializado\n")

    def evaluate_context_maintained(
        self,
        answer: str,
        expected_keywords: List[str],
        expected_project: str
    ) -> Tuple[bool, float, List[str]]:
        """
        Evalúa si la respuesta mantiene el contexto esperado.

        Args:
            answer: Respuesta del modelo
            expected_keywords: Palabras clave esperadas
            expected_project: Proyecto esperado

        Returns:
            Tuple (mantiene_contexto, score, keywords_encontradas)
        """
        answer_lower = answer.lower()

        # Buscar keywords
        found_keywords = [kw for kw in expected_keywords if kw in answer_lower]

        # Calcular score
        score = len(found_keywords) / len(expected_keywords) if expected_keywords else 0.0

        # Determinar si mantiene contexto (al menos 40% de keywords)
        maintains_context = score >= 0.4

        return maintains_context, score, found_keywords

    def check_wrong_project_mentioned(
        self,
        answer: str,
        expected_project: str
    ) -> List[str]:
        """
        Detecta si se mencionan proyectos incorrectos.

        Args:
            answer: Respuesta del modelo
            expected_project: Proyecto esperado

        Returns:
            Lista de proyectos incorrectos mencionados
        """
        answer_lower = answer.lower()

        # Mapeo de proyectos ÚNICAMENTE con sus keywords EXCLUSIVAS
        # (NO incluir keywords que son parte del proyecto esperado)
        projects_wrong_keywords = {
            "Desayunos Solidarios": [
                ("cena solidaria", "Cenas Solidarias"),
                ("charlas con abuelitos", "Charlas con Abuelitos"),
                ("residencia l'acollida", "Charlas con Abuelitos"),
                ("refuerzo escolar", "Refuerzo Escolar"),
                ("proyecto coles", "Refuerzo Escolar")
            ],
            "Charlas con Abuelitos": [
                ("desayunos solidarios", "Desayunos Solidarios"),
                ("repartir bocadillos", "Desayunos Solidarios"),
                ("refuerzo escolar", "Refuerzo Escolar"),
                ("proyecto coles", "Refuerzo Escolar")
            ],
            "Refuerzo Escolar": [
                ("desayunos solidarios", "Desayunos Solidarios"),
                ("repartir bocadillos", "Desayunos Solidarios"),
                ("charlas con abuelitos", "Charlas con Abuelitos"),
                ("residencia l'acollida", "Charlas con Abuelitos")
            ],
        }

        # Verificar si se mencionan proyectos incorrectos
        wrong_projects = []

        # Obtener las wrong_keywords para el proyecto esperado
        wrong_kw_list = projects_wrong_keywords.get(expected_project, [])

        for wrong_kw, wrong_project_name in wrong_kw_list:
            if wrong_kw in answer_lower:
                wrong_projects.append(f"{wrong_kw} ({wrong_project_name})")

        return wrong_projects

    def run_conversation(
        self,
        conversation_data: Dict
    ) -> Dict:
        """
        Ejecuta una conversación completa y evalúa resultados.

        Args:
            conversation_data: Dict con datos de la conversación

        Returns:
            Resultados de la evaluación
        """
        conv_id = conversation_data['id']
        conv_name = conversation_data['name']
        questions = conversation_data['conversation']

        print("\n" + "="*80)
        print(f"  CONVERSACIÓN: {conv_name}")
        print(f"  ID: {conv_id}")
        print("="*80 + "\n")

        session_id = f"bench_{conv_id}"
        results = []

        for i, q_data in enumerate(questions, 1):
            question = q_data['question']
            is_explicit = q_data['context_explicit']
            expected_keywords = q_data['expected_keywords']
            expected_project = q_data['expected_project']
            is_critical = q_data.get('critical', False)

            print(f"\n{'─'*80}")
            print(f"Pregunta {i}/{len(questions)}")
            print(f"{'─'*80}")
            print(f"👤 Usuario: {question}")
            print(f"📌 Contexto explícito: {'✅ Sí' if is_explicit else '❌ No'}")
            print(f"🎯 Proyecto esperado: {expected_project}")
            if is_critical:
                print(f"⚠️  PREGUNTA CRÍTICA (reportada en el issue)")
            print()

            # Procesar con RAG conversacional
            result = self.conv_rag.process_query(
                query=question,
                session_id=session_id,
                question_id=i
            )

            answer = result.get('answer', '')
            confidence = result.get('confidence', 0.0)

            # Mostrar respuesta (truncada)
            print(f"🤖 Respuesta:")
            print(f"   {answer[:250]}{'...' if len(answer) > 250 else ''}\n")

            # Evaluar contexto
            maintains_context, keyword_score, found_keywords = self.evaluate_context_maintained(
                answer, expected_keywords, expected_project
            )

            # Detectar proyectos incorrectos mencionados
            wrong_projects = self.check_wrong_project_mentioned(answer, expected_project)

            # Resultado
            if maintains_context and not wrong_projects:
                status = "✅ CONTEXTO MANTENIDO"
                status_emoji = "✅"
            elif maintains_context and wrong_projects:
                status = "⚠️ CONTEXTO PARCIAL (menciona otros proyectos)"
                status_emoji = "⚠️"
            else:
                status = "❌ CONTEXTO PERDIDO"
                status_emoji = "❌"

            print(f"{status}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Keywords score: {keyword_score:.1%} ({len(found_keywords)}/{len(expected_keywords)})")

            if found_keywords:
                print(f"   Keywords encontradas: {', '.join(found_keywords)}")

            if wrong_projects:
                print(f"   ⚠️ Proyectos incorrectos: {', '.join(wrong_projects)}")

            # Guardar resultado
            results.append({
                'question': question,
                'answer': answer,
                'context_explicit': is_explicit,
                'expected_project': expected_project,
                'maintains_context': maintains_context,
                'keyword_score': keyword_score,
                'found_keywords': found_keywords,
                'wrong_projects': wrong_projects,
                'confidence': confidence,
                'is_critical': is_critical,
                'status': status_emoji
            })

        # Resumen de la conversación
        print(f"\n{'='*80}")
        print(f"  RESUMEN: {conv_name}")
        print(f"{'='*80}\n")

        total_questions = len(results)
        implicit_questions = [r for r in results if not r['context_explicit']]
        successful = [r for r in implicit_questions if r['maintains_context'] and not r['wrong_projects']]

        success_rate = len(successful) / len(implicit_questions) * 100 if implicit_questions else 0

        print(f"Total preguntas: {total_questions}")
        print(f"Preguntas implícitas (sin contexto explícito): {len(implicit_questions)}")
        print(f"Contexto mantenido correctamente: {len(successful)}/{len(implicit_questions)}")
        print(f"📈 Tasa de éxito: {success_rate:.1f}%\n")

        return {
            'conversation_id': conv_id,
            'conversation_name': conv_name,
            'total_questions': total_questions,
            'implicit_questions': len(implicit_questions),
            'successful': len(successful),
            'success_rate': success_rate,
            'results': results
        }

    def run_full_benchmark(self) -> Dict:
        """
        Ejecuta el benchmark completo con todas las conversaciones.

        Returns:
            Resultados agregados del benchmark
        """
        print("\n" + "="*80)
        print("  BENCHMARK: PERSISTENCIA DE CONTEXTO CONVERSACIONAL")
        print("="*80)
        print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Conversaciones: {len(BENCHMARK_CONVERSATIONS)}")
        print("="*80 + "\n")

        all_results = []

        for conv_data in BENCHMARK_CONVERSATIONS:
            result = self.run_conversation(conv_data)
            all_results.append(result)

        # Resultados agregados
        print("\n" + "="*80)
        print("  RESULTADOS FINALES DEL BENCHMARK")
        print("="*80 + "\n")

        total_conversations = len(all_results)
        total_implicit = sum(r['implicit_questions'] for r in all_results)
        total_successful = sum(r['successful'] for r in all_results)

        overall_success_rate = (total_successful / total_implicit * 100) if total_implicit > 0 else 0

        print(f"Total conversaciones evaluadas: {total_conversations}")
        print(f"Total preguntas implícitas: {total_implicit}")
        print(f"Total contexto mantenido: {total_successful}/{total_implicit}")
        print(f"\n📊 TASA DE ÉXITO GLOBAL: {overall_success_rate:.1f}%\n")

        # Desglose por conversación
        print("Desglose por conversación:")
        print()
        for r in all_results:
            rate = r['success_rate']
            emoji = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
            print(f"  {emoji} {r['conversation_name']}: {rate:.1f}% ({r['successful']}/{r['implicit_questions']})")

        # Preguntas críticas
        print("\n" + "─"*80)
        print("  PREGUNTAS CRÍTICAS (reportadas en el issue)")
        print("─"*80 + "\n")

        critical_found = False
        for conv_result in all_results:
            for q_result in conv_result['results']:
                if q_result.get('is_critical', False):
                    critical_found = True
                    status = q_result['status']
                    print(f"{status} {q_result['question']}")
                    print(f"   Proyecto: {q_result['expected_project']}")
                    print(f"   Score: {q_result['keyword_score']:.1%}")
                    print()

        if not critical_found:
            print("  (No hay preguntas marcadas como críticas)")

        # Evaluación final
        print("\n" + "="*80)
        if overall_success_rate >= 80:
            print("  ✅ BENCHMARK EXITOSO")
            print("  El sistema mantiene correctamente el contexto conversacional")
        elif overall_success_rate >= 60:
            print("  ⚠️ BENCHMARK PARCIAL")
            print("  El sistema mantiene el contexto en la mayoría de casos")
        else:
            print("  ❌ BENCHMARK FALLIDO")
            print("  El sistema NO mantiene adecuadamente el contexto")
        print("="*80 + "\n")

        # Guardar resultados a archivo JSON
        output_file = project_root / "results" / f"benchmark_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'overall_success_rate': overall_success_rate,
                'total_implicit_questions': total_implicit,
                'total_successful': total_successful,
                'conversations': all_results
            }, f, ensure_ascii=False, indent=2)

        print(f"📁 Resultados guardados en: {output_file}\n")

        return {
            'overall_success_rate': overall_success_rate,
            'total_implicit_questions': total_implicit,
            'total_successful': total_successful,
            'conversations': all_results
        }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    evaluator = ContextPersistenceEvaluator()
    evaluator.initialize_system()
    results = evaluator.run_full_benchmark()
