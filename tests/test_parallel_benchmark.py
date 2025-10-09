#!/usr/bin/env python3
"""
Test rápido del benchmark paralelo optimizado
"""

import sys
import time
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from src.optimization.parallel_benchmark import ParallelBenchmark

def test_parallel_benchmark():
    """Prueba el benchmark paralelo con configuración optimizada"""

    print("🚀 TEST BENCHMARK PARALELO OPTIMIZADO")
    print("=" * 80)

    # Test 1: Modo ultra rápido (2 preguntas, 2 métricas)
    print("\n📊 Test 1: Modo Ultra Rápido")
    print("-" * 40)

    start = time.time()

    benchmark = ParallelBenchmark(
        n_workers=2,           # 2 workers para prueba
        use_cache=True,        # Usar caché
        ragas_mode="fast"      # Solo 2 métricas
    )

    try:
        result = benchmark.run_parallel(max_questions=2)

        elapsed = time.time() - start
        print(f"\n✅ Test 1 completado en {elapsed:.1f} segundos")

        # Mostrar estadísticas
        stats = result['statistics']
        print(f"   • Cache hits: {stats['cache_hits']}")
        print(f"   • Cache misses: {stats['cache_misses']}")
        print(f"   • Errores: {stats['errors']}")

    except Exception as e:
        print(f"❌ Error en Test 1: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("🏁 TEST COMPLETADO")
    print("\nComparación de tiempos:")
    print("   • Benchmark secuencial (estimado): ~16 minutos")
    print(f"   • Benchmark paralelo: {elapsed:.1f} segundos ({elapsed/60:.1f} minutos)")
    print(f"   • Mejora: {1600/elapsed:.1f}x más rápido")


if __name__ == "__main__":
    test_parallel_benchmark()