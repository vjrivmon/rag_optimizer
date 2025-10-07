#!/usr/bin/env python3
"""
Script interactivo para probar el sistema RAG con preguntas personalizadas
Compara respuestas de todos los modelos lado a lado
"""

import yaml
import warnings
from tabulate import tabulate
from colorama import init, Fore, Style
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper
from src.evaluation.ragas_evaluator import HybridEvaluator

# Inicializar colorama para colores en terminal
init(autoreset=True)

# Suprimir warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
warnings.filterwarnings('ignore', category=DeprecationWarning)


def print_header(text):
    """Imprime header formateado"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{text.center(80)}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def print_section(text):
    """Imprime sección formateada"""
    print(f"\n{Fore.YELLOW}{'─'*80}")
    print(f"{Fore.YELLOW}{text}")
    print(f"{Fore.YELLOW}{'─'*80}{Style.RESET_ALL}")


def format_time(seconds):
    """Formatea tiempo en segundos"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"


def test_question(question: str, rag_engine, models, evaluator):
    """Prueba una pregunta con todos los modelos"""

    print_header(f"PREGUNTA: {question}")

    # Recuperar contexto
    print(f"{Fore.GREEN}📚 Recuperando contexto...{Style.RESET_ALL}")
    docs = rag_engine.retrieve(question)
    contexts = [doc['content'] for doc in docs]

    if docs:
        print(f"{Fore.GREEN}   ✓ Recuperados {len(docs)} documentos relevantes{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}   ⚠️  No se encontraron documentos relevantes{Style.RESET_ALL}")

    context_text = rag_engine.build_context(docs)

    # Probar con cada modelo
    results = []

    for model in models:
        print_section(f"🤖 {model.model_name}")

        # Construir prompt
        prompt = model.build_rag_prompt(question, context_text, 'high')

        # Generar respuesta
        generation = model.generate(prompt, temperature=0.3, top_p=0.9, max_tokens=400)

        if generation['success']:
            response = generation['response']
            latency = generation['latency']

            print(f"{Fore.GREEN}   ✓ Respuesta generada en {format_time(latency)}{Style.RESET_ALL}")
            print(f"\n{Fore.WHITE}   Respuesta:{Style.RESET_ALL}")
            print(f"   {response[:300]}{'...' if len(response) > 300 else ''}\n")

            # Evaluar
            metrics = evaluator.evaluate(
                question=question,
                answer=response,
                contexts=contexts,
                ground_truth=None,
                keywords=[]
            )

            results.append({
                'model': model.model_name,
                'response': response,
                'latency': latency,
                'metrics': metrics
            })

        else:
            print(f"{Fore.RED}   ❌ Error: {generation.get('error')}{Style.RESET_ALL}")
            results.append({
                'model': model.model_name,
                'response': '',
                'latency': generation['latency'],
                'metrics': {}
            })

    # Tabla comparativa
    print_header("COMPARACIÓN DE RESULTADOS")

    # Tabla de tiempos y scores
    table_data = []
    for r in results:
        table_data.append([
            r['model'],
            format_time(r['latency']),
            f"{r['metrics'].get('combined_score', 0):.3f}",
            f"{r['metrics'].get('context_overlap', 0):.2f}",
            len(r['response'])
        ])

    print(tabulate(
        table_data,
        headers=['Modelo', 'Tiempo', 'Score', 'Contexto', 'Longitud'],
        tablefmt='grid'
    ))

    # Tabla de respuestas completas
    print_section("RESPUESTAS COMPLETAS")
    for r in results:
        print(f"\n{Fore.CYAN}[{r['model']}]{Style.RESET_ALL}")
        print(f"{r['response']}\n")

    # Métricas detalladas
    print_section("MÉTRICAS DETALLADAS")
    for r in results:
        print(f"\n{Fore.CYAN}{r['model']}:{Style.RESET_ALL}")
        for metric, value in r['metrics'].items():
            if metric != 'response_length':
                print(f"   {metric:.<30} {value:.4f}")

    return results


def interactive_mode():
    """Modo interactivo para testing"""

    print_header("SISTEMA RAG - MODO INTERACTIVO")

    # Cargar configuración
    print(f"{Fore.GREEN}⚙️  Cargando configuración...{Style.RESET_ALL}")
    with open('config/models_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Cargar RAG
    print(f"{Fore.GREEN}📚 Cargando RAG Engine...{Style.RESET_ALL}")
    rag = ConfigurableRAGEngine("data/vectorstore/chroma_db")

    # Cargar modelos
    print(f"{Fore.GREEN}🤖 Cargando modelos...{Style.RESET_ALL}")
    models = []
    for model_config in config['models']:
        model = LLMWrapper(
            model_name=model_config['name'],
            api_endpoint=model_config['endpoint'],
            context_window=model_config['context_window']
        )
        models.append(model)
        print(f"   ✓ {model_config['name']}")

    # Crear evaluador
    print(f"{Fore.GREEN}📊 Inicializando evaluador...{Style.RESET_ALL}")
    evaluator = HybridEvaluator(use_ragas=True, use_openai=False)

    print(f"\n{Fore.GREEN}✅ Sistema listo!{Style.RESET_ALL}")

    # Loop interactivo
    while True:
        print_section("NUEVA PREGUNTA")
        question = input(f"{Fore.YELLOW}Escribe tu pregunta (o 'salir' para terminar): {Style.RESET_ALL}").strip()

        if question.lower() in ['salir', 'exit', 'quit', 'q']:
            print(f"\n{Fore.GREEN}👋 ¡Hasta luego!{Style.RESET_ALL}\n")
            break

        if not question:
            continue

        # Procesar pregunta
        test_question(question, rag, models, evaluator)

        # Continuar?
        print(f"\n{Fore.CYAN}───────────────────────────────────────────────────────────────{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
