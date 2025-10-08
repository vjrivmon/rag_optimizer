#!/usr/bin/env python3
"""
Benchmark con backend DUAL (Ollama + OpenAI)

Ejecuta benchmark usando:
- Ollama (servidor UPV) para 3 métricas rápidas
- OpenAI para 3 métricas complejas que saturarían el servidor

Resultado: 6 métricas completas sin saturar el servidor Ollama
"""

from benchmark import BenchmarkRunner

if __name__ == '__main__':
    # Configuración con backend DUAL
    evaluator_config = {
        'backend': 'dual',  # ← MODO DUAL
        'ollama_model': 'gemma2:27b',
        'ollama_base_url': 'https://ollama.gti-ia.upv.es:443',
        'filter_thinking_tags': True
    }

    runner = BenchmarkRunner(evaluator_config=evaluator_config)
    runner.setup()
    runner.run_benchmark('data/eval_dataset.json')
    runner.save_results()
    runner.print_summary()
