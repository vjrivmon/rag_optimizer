#!/usr/bin/env python3
"""
Fase 5: AB Testing Rápido - Solo preguntas críticas
Compara before/after en los casos problemáticos identificados
"""

import json
import time
import logging
from typing import Dict, List, Any
from pathlib import Path
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir paths para imports
sys.path.append('src')

try:
    from core.rag_engine import ConfigurableRAGEngine
    from core.enhanced_rag_engine_new import EnhancedRAGEngine
    from core.enhanced_model_wrapper import EnhancedModelWrapper
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)

def run_quick_ab_test():
    """Ejecuta AB testing rápido en casos críticos"""
    logger.info("🚀 Iniciando AB Testing Rápido - Casos Críticos")

    # Preguntas críticas identificadas
    critical_cases = [
        {
            "id": 22,
            "question": "¿Qué se hace en la actividad de resis?",
            "keywords": ["resis", "acollida", "residentes", "pasar tiempo"],
            "issue": "CRÍTICO - Info disponible pero no se usa"
        },
        {
            "id": 6,
            "question": "¿Cómo me apunto a desayunos solidarios?",
            "keywords": ["miércoles", "whatsapp", "formulario"],
            "issue": "TIMEOUT - qwen3 se truncaba"
        },
        {
            "id": 14,
            "question": "¿Qué edad tienen los niños en coles?",
            "keywords": ["tres años", "sexto de primaria"],
            "issue": "INFO NO USADA - deepseek decía no tener info"
        },
        {
            "id": 19,
            "question": "¿Qué otras actividades se hacen relacionadas con niños?",
            "keywords": ["reyes", "terra mítica", "día del niño"],
            "issue": "TIMEOUT - qwen3 se truncaba"
        }
    ]

    try:
        # Inicializar engines
        logger.info("🔧 Inicializando sistemas...")
        original_engine = ConfigurableRAGEngine("data/vectorstore/chroma_db", use_hybrid=True)
        optimized_engine = EnhancedRAGEngine("data/vectorstore/chroma_db", use_hybrid=True)

        # Aplicar configuración optimizada
        optimized_engine.update_params({
            'top_k': 6,
            'similarity_threshold': 0.2
        })

        # Model wrapper
        model_wrapper = EnhancedModelWrapper("gemma2:27b")

        results = []

        for case in critical_cases:
            logger.info(f"\n🎯 Testeando: {case['issue']}")
            logger.info(f"   Q{case['id']}: {case['question']}")

            # Test con sistema ORIGINAL
            try:
                start_time = time.time()
                original_docs = original_engine.retrieve(case['question'])
                original_prompt = f"Basado en la siguiente información, responde: {case['question']}\n\n"
                for i, doc in enumerate(original_docs[:5], 1):
                    original_prompt += f"{i}. {doc['content']}\n"
                original_prompt += "\nRespuesta:"

                original_response = model_wrapper._generate_with_timeout(original_prompt, 120, 0.7)
                original_time = time.time() - start_time

                # Calcular keywords encontradas
                original_keywords = sum(1 for kw in case['keywords'] if kw in original_response.lower())

                # Test con sistema OPTIMIZADO
                start_time = time.time()
                optimized_docs = optimized_engine.retrieve_with_optimization(
                    case['question'], case['id'], "gemma2:27b"
                )
                optimized_prompt = optimized_engine.create_enhanced_prompt(
                    case['question'], [doc['content'] for doc in optimized_docs], "gemma2:27b", case['id']
                )
                optimized_response = model_wrapper._generate_with_timeout(optimized_prompt, 180, 0.4)
                optimized_time = time.time() - start_time

                # Calcular keywords encontradas
                optimized_keywords = sum(1 for kw in case['keywords'] if kw in optimized_response.lower())

                # Calcular mejoras
                keyword_improvement = optimized_keywords - original_keywords
                time_improvement = original_time - optimized_time  # Positivo si es más rápido

                result = {
                    'question_id': case['id'],
                    'question': case['question'],
                    'issue': case['issue'],
                    'original': {
                        'response': original_response[:150] + '...',
                        'keywords_found': original_keywords,
                        'generation_time': original_time,
                        'docs_retrieved': len(original_docs)
                    },
                    'optimized': {
                        'response': optimized_response[:150] + '...',
                        'keywords_found': optimized_keywords,
                        'generation_time': optimized_time,
                        'docs_retrieved': len(optimized_docs)
                    },
                    'improvements': {
                        'keyword_improvement': keyword_improvement,
                        'time_improvement': time_improvement,
                        'relative_improvement': (optimized_keywords / max(original_keywords, 1)) - 1
                    }
                }

                results.append(result)

                # Mostrar resultado
                keyword_status = "✅ MEJORÓ" if keyword_improvement > 0 else "➖ IGUAL" if keyword_improvement == 0 else "❌ EMPEORÓ"
                time_status = "⚡ MÁS RÁPIDO" if time_improvement > 1 else "➖ SIMILAR" if time_improvement > -1 else "⏰ MÁS LENTO"

                logger.info(f"   Keywords: {original_keywords} → {optimized_keywords} ({keyword_status})")
                logger.info(f"   Tiempo: {original_time:.1f}s → {optimized_time:.1f}s ({time_status})")
                logger.info(f"   Docs: {len(original_docs)} → {len(optimized_docs)}")

            except Exception as e:
                logger.error(f"   ❌ Error en caso {case['id']}: {e}")
                results.append({
                    'question_id': case['id'],
                    'error': str(e)
                })

        # Análisis final
        successful_results = [r for r in results if 'error' not in r]
        if successful_results:
            total_keyword_improvement = sum(r['improvements']['keyword_improvement'] for r in successful_results)
            total_time_improvement = sum(r['improvements']['time_improvement'] for r in successful_results)
            avg_relative_improvement = sum(r['improvements']['relative_improvement'] for r in successful_results) / len(successful_results)

            logger.info(f"\n📊 RESUMEN DE AB TESTING:")
            logger.info(f"   Casos evaluados: {len(successful_results)}/{len(critical_cases)}")
            logger.info(f"   Mejora total en keywords: +{total_keyword_improvement}")
            logger.info(f"   Mejora total en tiempo: +{total_time_improvement:.1f}s (más rápido)")
            logger.info(f"   Mejora relativa promedio: {avg_relative_improvement*100:.1f}%")

            # Guardar resultados
            output_file = f"results/quick_ab_test_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'test_metadata': {
                        'timestamp': time.time(),
                        'cases_tested': len(successful_results),
                        'total_cases': len(critical_cases)
                    },
                    'results': results,
                    'summary': {
                        'total_keyword_improvement': total_keyword_improvement,
                        'total_time_improvement': total_time_improvement,
                        'avg_relative_improvement': avg_relative_improvement,
                        'success_rate': len(successful_results) / len(critical_cases)
                    }
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Resultados guardados en: {output_file}")

            # Conclusión
            if total_keyword_improvement > 0 and avg_relative_improvement > 0:
                logger.info("🎉 ÉXITO: El sistema optimizado muestra mejoras claras")
            elif total_keyword_improvement > 0:
                logger.info("✅ MEJORA: El sistema optimizado es superior en keywords")
            elif avg_relative_improvement > 0:
                logger.info("✅ MEJORA: El sistema optimizado muestra mejoras relativas")
            else:
                logger.info("⚠️ LIMITADO: El sistema optimizado necesita mejoras adicionales")

        return results

    except Exception as e:
        logger.error(f"❌ Error en AB testing: {e}")
        return []

if __name__ == "__main__":
    run_quick_ab_test()