#!/usr/bin/env python3
"""
Test para diagnosticar el impacto del truncamiento a 5 chunks

Compara el rendimiento con:
- Config A: 5 chunks truncados (actual)
- Config B: 10 chunks completos (sin truncar)

Preguntas problemáticas identificadas:
- Q1, Q2, Q4, Q11: HIGH RISK (respuesta en pos 7-10)
- Q20, Q22, Q24, Q25, Q26: MEDIUM RISK (respuesta fuera top 10)
"""

import json
import sys
import time
from pathlib import Path
from colorama import init, Fore, Style
from tabulate import tabulate

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper
from src.evaluation.ragas_evaluator import HybridEvaluator

init(autoreset=True)

# Preguntas problemáticas identificadas
PROBLEM_QUESTIONS = [1, 2, 4, 11, 20, 22, 24, 25, 26]

def load_questions():
    """Cargar dataset de evaluación"""
    with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    return [q for q in questions if q['id'] in PROBLEM_QUESTIONS]

def test_config(config_name, num_chunks, chunk_size, rag_engine, model, evaluator, questions):
    """
    Test una configuración específica

    Args:
        config_name: Nombre de la config (ej: "5 chunks truncados")
        num_chunks: Número de chunks a usar
        chunk_size: Tamaño máximo de cada chunk (None = completo)
        rag_engine: Motor RAG
        model: Modelo LLM a usar
        evaluator: Evaluador RAGAs
        questions: Lista de preguntas a evaluar
    """
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"Testing: {config_name}")
    print(f"{'='*80}{Style.RESET_ALL}")

    results = []

    for i, q in enumerate(questions, 1):
        qid = q['id']
        question = q['question']
        expected = q.get('expected_answer')

        print(f"\n[{i}/{len(questions)}] Q{qid}: {question[:60]}...")

        # Recuperar contexto
        docs = rag_engine.retrieve(question)

        # Aplicar truncamiento según config
        if chunk_size:
            contexts = [doc['content'][:chunk_size] for doc in docs[:num_chunks]]
        else:
            contexts = [doc['content'] for doc in docs[:num_chunks]]

        context_text = rag_engine.build_context(docs[:num_chunks])

        print(f"   📚 Usando {len(contexts)} chunks (de {len(docs)} recuperados)")

        # Generar respuesta
        prompt = f"""Contexto:
{context_text}

Pregunta: {question}

Respuesta:"""

        start = time.time()
        response_data = model.generate(prompt)
        response = response_data.get('response', '')
        latency = time.time() - start

        # Evaluar con RAGAs
        try:
            eval_start = time.time()
            metrics = evaluator.evaluate(
                question=question,
                answer=response,
                contexts=contexts,
                ground_truth=expected
            )
            eval_time = time.time() - eval_start

            score = metrics.get('combined_score', 0.0)
            context_recall = metrics.get('context_recall', 0.0)
            answer_relevancy = metrics.get('answer_relevancy', 0.0)

            print(f"   ✓ Score: {score:.3f} (CR: {context_recall:.2f}, AR: {answer_relevancy:.2f}) [{eval_time:.1f}s]")

            results.append({
                'qid': qid,
                'question': question[:50],
                'score': score,
                'context_recall': context_recall,
                'answer_relevancy': answer_relevancy,
                'latency': latency
            })

        except Exception as e:
            print(f"   {Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
            results.append({
                'qid': qid,
                'question': question[:50],
                'score': 0.0,
                'context_recall': 0.0,
                'answer_relevancy': 0.0,
                'latency': latency
            })

    return results

def compare_results(results_a, results_b):
    """Comparar resultados de dos configuraciones"""
    print(f"\n{Fore.GREEN}{'='*80}")
    print("COMPARACIÓN DE RESULTADOS")
    print(f"{'='*80}{Style.RESET_ALL}")

    comparison = []

    for ra, rb in zip(results_a, results_b):
        qid = ra['qid']
        score_a = ra['score']
        score_b = rb['score']
        diff = score_b - score_a
        diff_pct = (diff / score_a * 100) if score_a > 0 else 0

        status = "✅" if diff > 0.1 else "⚠️" if abs(diff) < 0.1 else "❌"

        comparison.append([
            f"Q{qid}",
            ra['question'][:40] + '...',
            f"{score_a:.3f}",
            f"{score_b:.3f}",
            f"{diff:+.3f}",
            f"{diff_pct:+.1f}%",
            status
        ])

    headers = ["Q", "Pregunta", "5 chunks", "10 chunks", "Diff", "Diff %", ""]
    print(tabulate(comparison, headers=headers, tablefmt="grid"))

    # Stats
    avg_a = sum(r['score'] for r in results_a) / len(results_a)
    avg_b = sum(r['score'] for r in results_b) / len(results_b)

    print(f"\n{Fore.YELLOW}ESTADÍSTICAS:")
    print(f"  Config A (5 chunks): Avg score = {avg_a:.3f}")
    print(f"  Config B (10 chunks): Avg score = {avg_b:.3f}")
    print(f"  Mejora promedio: {avg_b - avg_a:+.3f} ({(avg_b - avg_a)/avg_a*100:+.1f}%)")

    improved = sum(1 for ra, rb in zip(results_a, results_b) if rb['score'] > ra['score'] + 0.1)
    print(f"  Preguntas mejoradas: {improved}/{len(results_a)} ({improved/len(results_a)*100:.0f}%)")
    print(f"{Style.RESET_ALL}")

def main():
    print(f"{Fore.CYAN}{'='*80}")
    print("TEST DE IMPACTO DEL TRUNCAMIENTO")
    print(f"{'='*80}{Style.RESET_ALL}")

    # Cargar preguntas problemáticas
    questions = load_questions()
    print(f"\n📋 Testing {len(questions)} preguntas problemáticas: {PROBLEM_QUESTIONS}")

    # Setup
    print(f"\n{Fore.GREEN}🔧 Inicializando sistema...{Style.RESET_ALL}")

    rag = ConfigurableRAGEngine(
        vector_store_path='data/vectorstore/chroma_db',
        use_hybrid=True
    )

    # Usar gemma2:27b (el más rápido)
    model = LLMWrapper(
        model_name="gemma2:27b",
        api_endpoint="https://ollama.gti-ia.upv.es:443/api/generate",
        context_window=2048
    )

    # Evaluador con Ollama
    evaluator = HybridEvaluator(
        use_ragas=True,
        use_openai=False,
        use_ollama=True,
        ollama_model="gemma2:27b",
        ollama_base_url="https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags=True
    )

    print(f"   ✓ RAG engine: Hybrid retrieval (ChromaDB + BM25)")
    print(f"   ✓ Model: gemma2:27b")
    print(f"   ✓ Evaluator: Ollama RAGAs (timeout 240s)")

    # Test Config A: 5 chunks truncados (actual)
    results_a = test_config(
        config_name="Config A: 5 chunks × 400 chars (ACTUAL)",
        num_chunks=5,
        chunk_size=400,
        rag_engine=rag,
        model=model,
        evaluator=evaluator,
        questions=questions
    )

    # Test Config B: 10 chunks completos
    results_b = test_config(
        config_name="Config B: 10 chunks × completo (SIN TRUNCAR)",
        num_chunks=10,
        chunk_size=None,
        rag_engine=rag,
        model=model,
        evaluator=evaluator,
        questions=questions
    )

    # Comparar
    compare_results(results_a, results_b)

    print(f"\n{Fore.CYAN}{'='*80}")
    print("CONCLUSIÓN")
    print(f"{'='*80}{Style.RESET_ALL}")

    avg_a = sum(r['score'] for r in results_a) / len(results_a)
    avg_b = sum(r['score'] for r in results_b) / len(results_b)
    improvement = (avg_b - avg_a) / avg_a * 100

    if improvement > 15:
        print(f"{Fore.GREEN}✅ CONFIRMADO: El truncamiento a 5 chunks causa pérdida significativa de calidad")
        print(f"   Mejora con 10 chunks: {improvement:+.1f}%")
        print(f"\n💡 RECOMENDACIÓN: Aumentar a 8 chunks + timeout 240s{Style.RESET_ALL}")
    elif improvement > 5:
        print(f"{Fore.YELLOW}⚠️  El truncamiento tiene impacto moderado")
        print(f"   Mejora con 10 chunks: {improvement:+.1f}%")
        print(f"\n💡 RECOMENDACIÓN: Considerar aumentar a 7-8 chunks{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ El truncamiento NO parece ser la causa principal")
        print(f"   Mejora con 10 chunks: {improvement:+.1f}%")
        print(f"\n💡 INVESTIGAR: Otros problemas en retrieval o chunking{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
