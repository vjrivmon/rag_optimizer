#!/usr/bin/env python3
"""
Test para verificar que el backend DUAL usa correctamente Ollama + OpenAI

Ejecuta 1 pregunta de prueba y muestra:
- Qué métricas calculó cada backend
- Tiempos de respuesta
- Confirmación de llamadas a OpenAI API
"""

import sys
import time
import os
from colorama import init, Fore, Style

sys.path.insert(0, 'src')
from core.rag_engine import ConfigurableRAGEngine
from evaluation.ragas_evaluator import HybridEvaluator

init(autoreset=True)

def test_dual_backend():
    """Test del backend dual con logging detallado"""

    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🧪 TEST BACKEND DUAL: Ollama + OpenAI{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Verificar API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print(f"{Fore.RED}❌ OPENAI_API_KEY no encontrada en .env{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   Configúrala para usar el backend dual{Style.RESET_ALL}")
        return False

    print(f"{Fore.GREEN}✅ OpenAI API Key encontrada: {api_key[:20]}...{Style.RESET_ALL}\n")

    # Inicializar RAG
    print(f"{Fore.YELLOW}📚 Cargando RAG Engine...{Style.RESET_ALL}")
    rag = ConfigurableRAGEngine("data/vectorstore/chroma_db")

    # Inicializar evaluador DUAL
    print(f"{Fore.YELLOW}🔀 Inicializando evaluador DUAL...{Style.RESET_ALL}")
    evaluator = HybridEvaluator(
        use_ragas=True,
        use_dual_backend=True,
        ollama_model='gemma2:27b',
        ollama_base_url='https://ollama.gti-ia.upv.es:443',
        filter_thinking_tags=True
    )

    print(f"\n{Fore.GREEN}✅ Sistema configurado{Style.RESET_ALL}\n")

    # Pregunta de prueba
    question = "¿Qué se hace en la actividad de desayunos?"
    expected = "La actividad consiste en que un grupo de voluntarios se reúne y reparte desayunos a personas sin hogar."

    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}❓ PREGUNTA DE PRUEBA{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"📝 {question}\n")

    # Recuperar contexto
    print(f"{Fore.YELLOW}🔍 Recuperando contexto...{Style.RESET_ALL}")
    docs = rag.retrieve(question)
    contexts = [doc['content'][:400] for doc in docs[:5]]
    print(f"   ✓ {len(contexts)} documentos recuperados\n")

    # Respuesta simulada (sin llamar a LLM de generación)
    answer = "En la actividad de desayunos solidarios, un grupo de voluntarios se reúne y reparte desayunos a personas sin hogar en Valencia."

    print(f"{Fore.YELLOW}🤖 Respuesta (simulada):{Style.RESET_ALL}")
    print(f"   {answer}\n")

    # EVALUAR CON BACKEND DUAL
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔀 EVALUACIÓN CON BACKEND DUAL{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}⏱️  Iniciando evaluación...{Style.RESET_ALL}\n")

    # Monitorear llamadas con timestamps
    start_time = time.time()

    try:
        # Evaluar
        metrics = evaluator.evaluate(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=expected,
            keywords=['voluntarios', 'desayunos', 'reparte']
        )

        total_time = time.time() - start_time

        # Mostrar resultados
        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ EVALUACIÓN COMPLETADA ({total_time:.1f}s){Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")

        # Separar métricas por origen
        ollama_metrics = {
            'answer_relevancy': metrics.get('answer_relevancy'),
            'context_recall': metrics.get('context_recall'),
            'answer_similarity': metrics.get('answer_similarity')
        }

        openai_metrics = {
            'faithfulness': metrics.get('faithfulness'),
            'context_precision': metrics.get('context_precision'),
            'answer_correctness': metrics.get('answer_correctness')
        }

        classic_metrics = {
            'has_response': metrics.get('has_response'),
            'keyword_coverage': metrics.get('keyword_coverage'),
            'context_overlap': metrics.get('context_overlap')
        }

        # Mostrar métricas Ollama
        print(f"{Fore.YELLOW}🦙 MÉTRICAS OLLAMA (servidor UPV):{Style.RESET_ALL}")
        for name, value in ollama_metrics.items():
            if value is not None:
                status = f"{Fore.GREEN}✓{Style.RESET_ALL}"
                print(f"   {status} {name:20s}: {value:.3f}")
            else:
                status = f"{Fore.RED}✗{Style.RESET_ALL}"
                print(f"   {status} {name:20s}: No calculada")

        # Mostrar métricas OpenAI
        print(f"\n{Fore.YELLOW}🤖 MÉTRICAS OPENAI (API):{Style.RESET_ALL}")
        openai_count = 0
        for name, value in openai_metrics.items():
            if value is not None:
                status = f"{Fore.GREEN}✓{Style.RESET_ALL}"
                print(f"   {status} {name:20s}: {value:.3f}")
                openai_count += 1
            else:
                status = f"{Fore.RED}✗{Style.RESET_ALL}"
                print(f"   {status} {name:20s}: No calculada")

        # Mostrar métricas clásicas
        print(f"\n{Fore.YELLOW}📊 MÉTRICAS CLÁSICAS (local):{Style.RESET_ALL}")
        for name, value in classic_metrics.items():
            if value is not None:
                status = f"{Fore.GREEN}✓{Style.RESET_ALL}"
                print(f"   {status} {name:20s}: {value:.3f}")

        # Score combinado
        combined = metrics.get('combined_score')
        print(f"\n{Fore.CYAN}🎯 SCORE COMBINADO: {combined:.3f}{Style.RESET_ALL}")

        # Verificación final
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📋 VERIFICACIÓN{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

        ollama_ok = all(v is not None for v in ollama_metrics.values())
        openai_ok = openai_count > 0

        if ollama_ok and openai_ok:
            print(f"{Fore.GREEN}✅ Backend DUAL funcionando correctamente{Style.RESET_ALL}")
            print(f"   🦙 Ollama: {sum(1 for v in ollama_metrics.values() if v is not None)}/3 métricas")
            print(f"   🤖 OpenAI: {openai_count}/3 métricas")
            print(f"\n{Fore.GREEN}🎉 TEST EXITOSO: Se están usando AMBOS backends{Style.RESET_ALL}")
            return True
        elif openai_ok:
            print(f"{Fore.YELLOW}⚠️  Ollama falló, pero OpenAI funciona{Style.RESET_ALL}")
            print(f"   🤖 OpenAI: {openai_count}/3 métricas calculadas")
            return False
        else:
            print(f"{Fore.RED}❌ OpenAI NO está funcionando{Style.RESET_ALL}")
            print(f"   Ninguna métrica OpenAI fue calculada")
            print(f"\n{Fore.YELLOW}Posibles causas:{Style.RESET_ALL}")
            print(f"   1. API key inválida o sin créditos")
            print(f"   2. Problema de red/firewall")
            print(f"   3. Error en configuración")
            return False

    except Exception as e:
        print(f"\n{Fore.RED}❌ ERROR EN EVALUACIÓN:{Style.RESET_ALL}")
        print(f"   {str(e)}")
        import traceback
        print(f"\n{Fore.YELLOW}Traceback:{Style.RESET_ALL}")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_dual_backend()
    sys.exit(0 if success else 1)
