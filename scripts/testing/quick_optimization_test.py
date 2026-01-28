#!/usr/bin/env python3
"""
Test rápido de optimizaciones - solo casos críticos
"""

import sys
import time
import json
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir paths para imports
sys.path.append('src')

try:
    from core.enhanced_model_wrapper import EnhancedModelWrapper
    from core.enhanced_rag_engine_new import create_enhanced_rag_engine
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)

def test_critical_cases():
    """Test solo los casos críticos identificados en Fase 1"""
    logger.info("🚨 Test rápido de casos críticos...")

    # Inicializar componentes
    try:
        rag_engine = create_enhanced_rag_engine()
        model_wrapper = EnhancedModelWrapper("gemma2:27b")  # Test con el mejor modelo
    except Exception as e:
        logger.error(f"Error inicializando: {e}")
        return

    # Casos críticos a probar
    critical_cases = [
        {
            "id": 22,
            "question": "¿Qué se hace en la actividad de resis?",
            "keywords": ["resis", "acollida", "residentes", "pasar tiempo"],
            "description": "CASO CRÍTICO - Información disponible pero no se usa"
        },
        {
            "id": 6,
            "question": "¿Cómo me apunto a desayunos solidarios?",
            "keywords": ["miércoles", "whatsapp", "formulario"],
            "description": "CASO TIMEOUT - qwen3 se truncaba"
        }
    ]

    results = []

    for case in critical_cases:
        logger.info(f"\n🎯 Testeando: {case['description']}")
        logger.info(f"   P{case['id']}: {case['question']}")

        try:
            start_time = time.time()

            # Retrieval optimizado
            docs = rag_engine.retrieve_with_optimization(case['question'], case['id'], "gemma2:27b")
            contexts = [doc['content'] for doc in docs]

            # Prompt optimizado
            prompt = rag_engine.create_enhanced_prompt(case['question'], contexts, "gemma2:27b", case['id'])

            # Generación con timeout
            response = model_wrapper._generate_with_timeout(prompt, 60, 0.3)

            generation_time = time.time() - start_time

            # Análisis de resultados
            analysis = {
                'question_id': case['id'],
                'question': case['question'],
                'contexts_retrieved': len(contexts),
                'response': response,
                'generation_time': generation_time,
                'keyword_matches': sum(1 for kw in case['keywords'] if kw in response.lower()),
                'is_truncated': '[Respuesta truncada' in response,
                'has_no_info': 'no tengo esa información' in response.lower(),
                'optimization_type': rag_engine.get_optimization_summary(case['id'], "gemma2:27b")['optimization_type']
            }

            results.append(analysis)

            # Mostrar resultado
            status = "✅ ÉXITO" if analysis['keyword_matches'] > 0 else "❌ FALLÓ"
            logger.info(f"   {status} - {analysis['generation_time']:.1f}s - Keywords: {analysis['keyword_matches']}/{len(case['keywords'])}")

            # Mostrar respuesta preview
            response_preview = response[:100] + "..." if len(response) > 100 else response
            logger.info(f"   💬 {response_preview}")

            # Verificar optimización aplicada
            config = rag_engine.get_optimization_summary(case['id'], "gemma2:27b")
            logger.info(f"   🔧 Optimización: {config['optimization_type']}")

        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            results.append({
                'question_id': case['id'],
                'error': str(e)
            })

    # Guardar resultados
    output_file = f"results/quick_optimization_test_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"\n✅ Resultados guardados en: {output_file}")

    # Resumen final
    successful_cases = sum(1 for r in results if r.get('keyword_matches', 0) > 0)
    total_cases = len(results)

    logger.info(f"\n📊 RESUMEN:")
    logger.info(f"   Casos exitosos: {successful_cases}/{total_cases}")
    logger.info(f"   Tasa de éxito: {successful_cases/total_cases*100:.1f}%")

    if successful_cases == total_cases:
        logger.info("   🎉 ¡TODOS los casos críticos funcionan!")
    elif successful_cases > 0:
        logger.info("   ⚠️ Mejora parcial - algunos casos funcionan")
    else:
        logger.info("   🚨 Los casos críticos necesitan más trabajo")

    return results

if __name__ == "__main__":
    test_critical_cases()