#!/usr/bin/env python3
"""
Test del sistema RAG Adaptativo
Compara el rendimiento con chunks fijos vs dinámicos
"""

import json
import time
import warnings
from colorama import init, Fore, Style
from src.core.adaptive_rag import AdaptiveRAGEngine, create_adaptive_rag
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper
from src.evaluation.ragas_evaluator import HybridEvaluator

# Inicializar colorama
init(autoreset=True)

# Suprimir warnings
warnings.filterwarnings('ignore')


def test_adaptive_system():
    """Test completo del sistema adaptativo"""

    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}TEST DEL SISTEMA RAG ADAPTATIVO{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Inicializar sistemas
    print(f"{Fore.YELLOW}🔧 Inicializando sistemas...{Style.RESET_ALL}")

    # Sistema tradicional (7 chunks fijos)
    rag_fixed = ConfigurableRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    # Sistema adaptativo
    rag_adaptive = create_adaptive_rag("data/vectorstore/chroma_db")

    # Modelo para generar respuestas (usar Gemma2 que era el mejor con 5 chunks)
    model = LLMWrapper(
        model_name="gemma2:27b",
        api_endpoint="https://ollama.gti-ia.upv.es:443/api/generate",
        context_window=2048
    )

    # Evaluador con RAGAs completas
    evaluator = HybridEvaluator(
        use_ragas=True,
        use_openai=False,
        use_ollama=True,
        ollama_model="gemma2:27b",
        ollama_base_url="https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags=True
    )

    print(f"{Fore.GREEN}✓ Sistemas inicializados{Style.RESET_ALL}\n")

    # Cargar preguntas de prueba (focus en problemáticas)
    with open("data/evaluation_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Seleccionar preguntas clave (las que más fallaron)
    test_questions = [
        dataset[10],   # Q11: ¿Dónde es la actividad de coles?
        dataset[15],   # Q16: ¿Quién paga la gasolina para ir a coles?
        dataset[19],   # Q20: ¿Dónde es la actividad de resis?
        dataset[0],    # Q1: ¿Qué se hace en la actividad de desayunos?
        dataset[5],    # Q6: ¿Cómo me apunto a desayunos solidarios?
        dataset[24],   # Q25: ¿Qué significa Para-Mira-Ayuda?
    ]

    results_comparison = []

    for q_data in test_questions:
        question = q_data['question']
        expected = q_data['expected_answer']
        q_id = q_data['id']

        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Pregunta {q_id}: {question}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        result_entry = {
            'question_id': q_id,
            'question': question,
            'expected': expected
        }

        # Test con sistema FIJO (7 chunks)
        print(f"\n{Fore.YELLOW}📌 Sistema FIJO (7 chunks):{Style.RESET_ALL}")

        start = time.time()
        docs_fixed = rag_fixed.retrieve(question)[:7]
        context_fixed = rag_fixed.build_context(docs_fixed)

        prompt = model.build_rag_prompt(question, context_fixed, 'medium')
        response_fixed = model.generate(prompt)

        if response_fixed['success']:
            answer_fixed = response_fixed.get('answer', response_fixed['response'])
            latency_fixed = time.time() - start

            # Evaluar
            metrics_fixed = evaluator.evaluate(
                question=question,
                answer=answer_fixed,
                contexts=[d['content'] for d in docs_fixed],
                ground_truth=expected
            )

            score_fixed = metrics_fixed.get('combined_score', 0)
            print(f"   Chunks usados: 7")
            print(f"   Score: {Fore.GREEN if score_fixed > 0.6 else Fore.RED}{score_fixed:.3f}{Style.RESET_ALL}")
            print(f"   Latencia: {latency_fixed:.1f}s")
            print(f"   Respuesta (primeros 100 chars): {answer_fixed[:100]}...")

            result_entry['fixed'] = {
                'chunks': 7,
                'score': score_fixed,
                'latency': latency_fixed
            }

        # Test con sistema ADAPTATIVO
        print(f"\n{Fore.YELLOW}🎯 Sistema ADAPTATIVO:{Style.RESET_ALL}")

        start = time.time()
        docs_adaptive, metadata = rag_adaptive.retrieve_adaptive(question)
        context_adaptive = rag_adaptive.build_context(docs_adaptive)

        prompt = model.build_rag_prompt(question, context_adaptive, 'medium')
        response_adaptive = model.generate(prompt)

        if response_adaptive['success']:
            answer_adaptive = response_adaptive.get('answer', response_adaptive['response'])
            latency_adaptive = time.time() - start

            # Evaluar
            metrics_adaptive = evaluator.evaluate(
                question=question,
                answer=answer_adaptive,
                contexts=[d['content'] for d in docs_adaptive],
                ground_truth=expected
            )

            score_adaptive = metrics_adaptive.get('combined_score', 0)
            print(f"   Chunks usados: {metadata['chunks_selected']} (tipo: {metadata['question_type']})")
            print(f"   Score: {Fore.GREEN if score_adaptive > 0.6 else Fore.RED}{score_adaptive:.3f}{Style.RESET_ALL}")
            print(f"   Latencia: {latency_adaptive:.1f}s")
            print(f"   Relevancia avg: {metadata['avg_relevance']:.2f}")
            print(f"   Respuesta (primeros 100 chars): {answer_adaptive[:100]}...")

            result_entry['adaptive'] = {
                'chunks': metadata['chunks_selected'],
                'score': score_adaptive,
                'latency': latency_adaptive,
                'question_type': metadata['question_type'],
                'avg_relevance': metadata['avg_relevance']
            }

        # Comparación
        if 'fixed' in result_entry and 'adaptive' in result_entry:
            diff = result_entry['adaptive']['score'] - result_entry['fixed']['score']
            if diff > 0:
                print(f"\n   {Fore.GREEN}✅ Mejora: +{diff:.3f}{Style.RESET_ALL}")
            elif diff < 0:
                print(f"\n   {Fore.RED}⚠️ Empeora: {diff:.3f}{Style.RESET_ALL}")
            else:
                print(f"\n   {Fore.YELLOW}= Sin cambio{Style.RESET_ALL}")

        results_comparison.append(result_entry)

    # Resumen final
    print(f"\n\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}RESUMEN DE RESULTADOS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Calcular estadísticas
    fixed_scores = [r['fixed']['score'] for r in results_comparison if 'fixed' in r]
    adaptive_scores = [r['adaptive']['score'] for r in results_comparison if 'adaptive' in r]

    avg_fixed = sum(fixed_scores) / len(fixed_scores) if fixed_scores else 0
    avg_adaptive = sum(adaptive_scores) / len(adaptive_scores) if adaptive_scores else 0

    print(f"{Fore.YELLOW}Sistema FIJO (7 chunks):{Style.RESET_ALL}")
    print(f"  Score promedio: {avg_fixed:.3f}")

    print(f"\n{Fore.YELLOW}Sistema ADAPTATIVO:{Style.RESET_ALL}")
    print(f"  Score promedio: {avg_adaptive:.3f}")

    improvement = ((avg_adaptive - avg_fixed) / avg_fixed * 100) if avg_fixed > 0 else 0

    print(f"\n{Fore.GREEN if improvement > 0 else Fore.RED}Mejora general: {improvement:+.1f}%{Style.RESET_ALL}")

    # Detalles por tipo de pregunta
    print(f"\n{Fore.YELLOW}Distribución de chunks por tipo:{Style.RESET_ALL}")
    for r in results_comparison:
        if 'adaptive' in r:
            q_type = r['adaptive']['question_type']
            chunks = r['adaptive']['chunks']
            score = r['adaptive']['score']
            print(f"  Q{r['question_id']:2d} ({q_type:10s}): {chunks} chunks, score={score:.3f}")

    # Guardar resultados
    output_file = f"results/adaptive_test_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results_comparison,
            'summary': {
                'avg_fixed': avg_fixed,
                'avg_adaptive': avg_adaptive,
                'improvement_pct': improvement
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{Fore.GREEN}✅ Resultados guardados en: {output_file}{Style.RESET_ALL}")


if __name__ == "__main__":
    test_adaptive_system()