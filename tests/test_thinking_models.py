#!/usr/bin/env python3
"""
Test de modelos thinking con max_tokens alto
Verifica que el servidor UPV soporta respuestas largas sin timeout
"""

import yaml
import time
from colorama import init, Fore, Style
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper

# Inicializar colorama
init(autoreset=True)

print(f"{Fore.CYAN}🧪 TEST: Modelos Thinking con max_tokens Alto{Style.RESET_ALL}")
print("="*80)

# Cargar configuración
with open('config/models_config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# RAG Engine
print(f"\n{Fore.GREEN}📚 Cargando RAG Engine...{Style.RESET_ALL}")
rag = ConfigurableRAGEngine("data/vectorstore/chroma_db")

# Solo modelos thinking
thinking_models = []
for model_config in config['models']:
    if any(keyword in model_config['name'].lower() for keyword in ['qwen', 'deepseek', 'r1']):
        model = LLMWrapper(
            model_name=model_config['name'],
            api_endpoint=model_config['endpoint'],
            context_window=model_config['context_window']
        )
        thinking_models.append(model)
        print(f"   ✓ {model_config['name']} (thinking model)")

if not thinking_models:
    print(f"{Fore.RED}❌ No se encontraron modelos thinking{Style.RESET_ALL}")
    exit(1)

# Pregunta de test
test_question = "¿Qué se hace en la actividad de desayunos?"

# Recuperar contexto
print(f"\n{Fore.GREEN}📚 Recuperando contexto...{Style.RESET_ALL}")
docs = rag.retrieve(test_question)
context_text = rag.build_context(docs[:5])
print(f"   ✓ {len(docs)} documentos recuperados")

# Test con diferentes max_tokens
max_tokens_tests = [1200, 1500, 2000]

results = []

for model in thinking_models:
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🤖 Modelo: {model.model_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

    for max_tokens in max_tokens_tests:
        print(f"\n   📊 Test con max_tokens={max_tokens}")

        # Generar prompt
        prompt = model.build_rag_prompt(test_question, context_text, strictness="medium")

        # Generar respuesta
        start = time.time()
        generation = model.generate(
            prompt,
            temperature=0.3,
            top_p=0.9,
            max_tokens=max_tokens
        )
        latency = time.time() - start

        if generation['success']:
            response = generation['response']
            response_length = len(response)

            # Contar thinking vs respuesta real
            if '<think>' in response.lower():
                think_end = response.lower().find('</think>')
                if think_end > 0:
                    thinking_length = think_end + 8
                    actual_response_length = response_length - thinking_length
                else:
                    thinking_length = response_length
                    actual_response_length = 0
            else:
                thinking_length = 0
                actual_response_length = response_length

            # Resultado
            print(f"      ✅ {Fore.GREEN}ÉXITO{Style.RESET_ALL}")
            print(f"      ⏱️  Latencia: {latency:.1f}s")
            print(f"      📝 Total chars: {response_length}")
            print(f"      🧠 Thinking: {thinking_length} chars ({thinking_length/response_length*100:.1f}%)")
            print(f"      💬 Respuesta real: {actual_response_length} chars ({actual_response_length/response_length*100:.1f}%)")

            # Mostrar preview de respuesta real (sin thinking)
            if '<think>' in response.lower() and '</think>' in response.lower():
                actual_answer = response.split('</think>')[1].strip()
                print(f"      📄 Preview: {actual_answer[:150]}...")
            else:
                print(f"      📄 Preview: {response[:150]}...")

            results.append({
                'model': model.model_name,
                'max_tokens': max_tokens,
                'latency': latency,
                'success': True,
                'response_length': response_length,
                'actual_response_length': actual_response_length
            })
        else:
            error = generation.get('error', 'Unknown error')
            print(f"      ❌ {Fore.RED}ERROR: {error}{Style.RESET_ALL}")
            print(f"      ⏱️  Latencia: {latency:.1f}s")

            # Verificar si es timeout
            if 'timeout' in error.lower() or latency > 60:
                print(f"      ⚠️  {Fore.YELLOW}TIMEOUT detectado - max_tokens={max_tokens} es demasiado alto{Style.RESET_ALL}")

            results.append({
                'model': model.model_name,
                'max_tokens': max_tokens,
                'latency': latency,
                'success': False,
                'error': error
            })

# Resumen final
print(f"\n\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}📊 RESUMEN DE RESULTADOS{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

for model in thinking_models:
    print(f"\n{Fore.GREEN}🤖 {model.model_name}{Style.RESET_ALL}")

    model_results = [r for r in results if r['model'] == model.model_name]
    successful = [r for r in model_results if r['success']]
    failed = [r for r in model_results if not r['success']]

    print(f"   ✅ Exitosos: {len(successful)}/{len(model_results)}")

    if successful:
        max_working_tokens = max(r['max_tokens'] for r in successful)
        avg_latency = sum(r['latency'] for r in successful) / len(successful)
        avg_response_pct = sum(r['actual_response_length']/r['response_length']*100 for r in successful if r['response_length'] > 0) / len(successful)

        print(f"   📊 Max tokens que funciona: {max_working_tokens}")
        print(f"   ⏱️  Latencia promedio: {avg_latency:.1f}s")
        print(f"   💬 Respuesta real promedio: {avg_response_pct:.1f}% del total")

    if failed:
        print(f"   ❌ Fallos: {len(failed)}")
        for r in failed:
            print(f"      - max_tokens={r['max_tokens']}: {r.get('error', 'Unknown')}")

# Recomendación
print(f"\n\n{Fore.CYAN}💡 RECOMENDACIÓN{Style.RESET_ALL}")
print("="*80)

all_successful = [r for r in results if r['success']]
if all_successful:
    # Encontrar el max_tokens óptimo (mayor que funciona sin timeout)
    max_safe_tokens = max(r['max_tokens'] for r in all_successful)
    avg_response_ratio = sum(r['actual_response_length']/r['response_length'] for r in all_successful if r['response_length'] > 0) / len(all_successful)

    print(f"✅ Los modelos thinking soportan hasta {Fore.GREEN}max_tokens={max_safe_tokens}{Style.RESET_ALL}")
    print(f"✅ Aproximadamente {Fore.GREEN}{avg_response_ratio*100:.0f}%{Style.RESET_ALL} del output es respuesta real (resto es thinking)")
    print(f"✅ Rango recomendado para benchmark: {Fore.GREEN}[1200, {max_safe_tokens}]{Style.RESET_ALL}")
else:
    print(f"❌ {Fore.RED}Ningún test fue exitoso - el servidor puede tener problemas{Style.RESET_ALL}")

print("\n" + "="*80)
print(f"{Fore.GREEN}✅ Test completado{Style.RESET_ALL}\n")
