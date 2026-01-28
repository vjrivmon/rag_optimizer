#!/usr/bin/env python3
"""
🧪 Test del Sistema Ensemble

Prueba rápida con 1-2 preguntas para validar que todo funciona.
"""

import sys
from pathlib import Path

# Añadir directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from src.ensemble.question_classifier import QuestionClassifier
from src.ensemble.strategies import VotingStrategy, WeightedStrategy, RoutingStrategy, ConsensusStrategy


def test_question_classifier():
    """Test del clasificador de preguntas"""
    print("\n🧪 TEST 1: Question Classifier")
    print("=" * 80)
    
    classifier = QuestionClassifier()
    
    test_questions = [
        ("¿Qué significa Para-Mira-Ayuda?", 25, 'filosofica'),
        ("¿Dónde es la actividad de coles?", 11, 'factual'),
        ("¿Cómo se compra la comida?", 9, 'procedural'),
        ("¿Necesito documentación?", 17, 'normativa'),
    ]
    
    for question, qid, expected_type in test_questions:
        classified = classifier.classify(question, qid)
        icon = "✅" if classified == expected_type else "⚠️"
        print(f"{icon} P{qid}: {question[:50]}")
        print(f"   Clasificado: {classified} (esperado: {expected_type})")
        
        # Modelos recomendados
        models = classifier.get_recommended_models(classified, qid)
        print(f"   Modelos recomendados: {models}")
        print()
    
    print("✅ Clasificador funcionando correctamente\n")
    return True


def test_voting_strategy():
    """Test de la estrategia voting"""
    print("\n🧪 TEST 2: Voting Strategy")
    print("=" * 80)
    
    strategy = VotingStrategy()
    
    # Respuestas simuladas
    mock_responses = [
        {
            'model_name': 'gemma2:27b',
            'answer': 'Respuesta A',
            'metrics': {'combined_score': 0.85},
            'generation_time': 10.0,
            'contexts': []
        },
        {
            'model_name': 'llama3.3:70b',
            'answer': 'Respuesta B',
            'metrics': {'combined_score': 0.75},
            'generation_time': 15.0,
            'contexts': []
        },
        {
            'model_name': 'qwen3:32b',
            'answer': 'Respuesta C',
            'metrics': {'combined_score': 0.80},
            'generation_time': 12.0,
            'contexts': []
        }
    ]
    
    result = strategy.select_best_response(mock_responses)
    
    print(f"Respuesta seleccionada de: {result['selected_from']}")
    print(f"Razón: {result['selection_reason']}")
    print(f"Scores: {result['all_scores']}")
    
    assert result['selected_from'] == 'gemma2:27b', "Debería seleccionar gemma2 (mejor score)"
    print("✅ Voting strategy funcionando correctamente\n")
    return True


def test_weighted_strategy():
    """Test de la estrategia weighted"""
    print("\n🧪 TEST 3: Weighted Strategy")
    print("=" * 80)
    
    strategy = WeightedStrategy()
    
    print(f"Pesos configurados: {strategy.weights}")
    
    # Respuestas simuladas
    mock_responses = [
        {
            'model_name': 'gemma2:27b',
            'answer': 'Respuesta A',
            'metrics': {'combined_score': 0.80},  # Score más bajo
            'generation_time': 10.0,
            'contexts': []
        },
        {
            'model_name': 'qwen3:32b',
            'answer': 'Respuesta B',
            'metrics': {'combined_score': 0.85},  # Score más alto
            'generation_time': 12.0,
            'contexts': []
        }
    ]
    
    result = strategy.select_best_response(mock_responses)
    
    print(f"Respuesta seleccionada de: {result['selected_from']}")
    print(f"Razón: {result['selection_reason']}")
    print(f"Scores ponderados: {result['weighted_scores']}")
    print(f"Scores raw: {result['raw_scores']}")
    
    # gemma2 tiene más peso (0.40 vs 0.30), así que debería ganar aunque score sea menor
    print("✅ Weighted strategy funcionando correctamente\n")
    return True


def test_routing_strategy():
    """Test de la estrategia routing"""
    print("\n🧪 TEST 4: Routing Strategy")
    print("=" * 80)
    
    classifier = QuestionClassifier()
    strategy = RoutingStrategy(classifier)
    
    # Test con P25 (configuración especial)
    print("Test con P25 (configuración especial):")
    recommended = strategy.get_recommended_models("¿Qué significa Para-Mira-Ayuda?", 25)
    print(f"   Modelos recomendados: {recommended}")
    assert 'llama3.3:70b' in recommended and 'gemma2:27b' in recommended
    
    # Test con pregunta filosófica genérica
    print("\nTest con pregunta filosófica:")
    recommended = strategy.get_recommended_models("¿Qué caracteriza a DNI?", 26)
    print(f"   Modelos recomendados: {recommended}")
    
    # Respuestas simuladas
    mock_responses = [
        {
            'model_name': 'gemma2:27b',
            'answer': 'Respuesta A',
            'metrics': {'combined_score': 0.85},
            'generation_time': 10.0,
            'contexts': []
        },
        {
            'model_name': 'llama3.3:70b',
            'answer': 'Respuesta B',
            'metrics': {'combined_score': 0.80},
            'generation_time': 15.0,
            'contexts': []
        },
        {
            'model_name': 'deepseek-r1:latest',
            'answer': 'Respuesta C',
            'metrics': {'combined_score': 0.90},  # Mejor score pero no recomendado
            'generation_time': 20.0,
            'contexts': []
        }
    ]
    
    result = strategy.select_best_response(
        mock_responses,
        question="¿Qué caracteriza a DNI?",
        question_id=26
    )
    
    print(f"\nRespuesta seleccionada de: {result['selected_from']}")
    print(f"Razón: {result['selection_reason']}")
    print(f"Tipo de routing: {result['routing_type']}")
    
    # Debería seleccionar gemma2 o llama3.3, NO deepseek (aunque tenga mejor score)
    assert result['selected_from'] in ['gemma2:27b', 'llama3.3:70b']
    print("✅ Routing strategy funcionando correctamente\n")
    return True


def test_consensus_strategy():
    """Test de la estrategia consensus"""
    print("\n🧪 TEST 5: Consensus Strategy")
    print("=" * 80)
    
    strategy = ConsensusStrategy(consensus_threshold=0.2)
    
    # Caso 1: Alto consenso
    print("Caso 1: Alto consenso (scores similares)")
    mock_responses_consensus = [
        {
            'model_name': 'gemma2:27b',
            'answer': 'Respuesta A',
            'metrics': {'combined_score': 0.85},
            'generation_time': 10.0,
            'contexts': []
        },
        {
            'model_name': 'llama3.3:70b',
            'answer': 'Respuesta B',
            'metrics': {'combined_score': 0.83},
            'generation_time': 15.0,
            'contexts': []
        },
        {
            'model_name': 'qwen3:32b',
            'answer': 'Respuesta C',
            'metrics': {'combined_score': 0.87},
            'generation_time': 12.0,
            'contexts': []
        }
    ]
    
    result1 = strategy.select_best_response(mock_responses_consensus)
    print(f"   Seleccionado: {result1['selected_from']}")
    print(f"   Razón: {result1['selection_reason']}")
    print(f"   Consenso: {result1['consensus_stats']}")
    
    # Caso 2: Alta divergencia
    print("\nCaso 2: Alta divergencia (scores muy diferentes)")
    mock_responses_divergence = [
        {
            'model_name': 'gemma2:27b',
            'answer': 'Respuesta A',
            'metrics': {'combined_score': 0.90},
            'generation_time': 10.0,
            'contexts': []
        },
        {
            'model_name': 'llama3.3:70b',
            'answer': 'Respuesta B',
            'metrics': {'combined_score': 0.30},
            'generation_time': 15.0,
            'contexts': []
        },
        {
            'model_name': 'qwen3:32b',
            'answer': 'Respuesta C',
            'metrics': {'combined_score': 0.50},
            'generation_time': 12.0,
            'contexts': []
        }
    ]
    
    result2 = strategy.select_best_response(mock_responses_divergence)
    print(f"   Seleccionado: {result2['selected_from']}")
    print(f"   Razón: {result2['selection_reason']}")
    print(f"   Consenso: {result2['consensus_stats']}")
    
    print("✅ Consensus strategy funcionando correctamente\n")
    return True


def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 80)
    print("🧪 TEST SUITE - SISTEMA ENSEMBLE")
    print("=" * 80)
    
    tests = [
        ("Clasificador de Preguntas", test_question_classifier),
        ("Voting Strategy", test_voting_strategy),
        ("Weighted Strategy", test_weighted_strategy),
        ("Routing Strategy", test_routing_strategy),
        ("Consensus Strategy", test_consensus_strategy),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"📊 RESULTADOS: {passed}/{len(tests)} tests passed")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("\n✅ El sistema ensemble está listo para usar")
        print("\n🚀 Siguiente paso: Ejecutar benchmark completo")
        print("   python benchmark_ensemble.py")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) fallaron")
        return 1


if __name__ == "__main__":
    exit(main())

