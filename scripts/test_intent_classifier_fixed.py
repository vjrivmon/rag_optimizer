#!/usr/bin/env python3
"""
Test del IntentClassifier corregido
====================================

Prueba que:
1. PARA.MIRA.AYUDA no se clasifica como 'help' (debe usar RAG)
2. "ayuda" simple sí se clasifica como 'help'
3. No hay referencias a kayak/DANA en respuestas
"""

import sys
from pathlib import Path

# Añadir path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.intent_classifier import IntentClassifier


def test_intent_classifier():
    """Test del IntentClassifier corregido"""

    print("\n" + "="*80)
    print("TEST: IntentClassifier Corregido")
    print("="*80 + "\n")

    classifier = IntentClassifier()

    # Test 1: PARA.MIRA.AYUDA debe ir a RAG (intent='question')
    print("Test 1: PARA.MIRA.AYUDA debe clasificarse como 'question' (RAG)")
    print("-" * 80)

    test_queries = [
        "¿Qué significa PARA. MIRA. AYUDA.?",
        "PARA.MIRA.AYUDA",
        "para mira ayuda",
        "¿Qué es PARA MIRA AYUDA?",
    ]

    for query in test_queries:
        result = classifier.classify(query)
        status = "✅ CORRECTO" if result.intent == 'question' else "❌ INCORRECTO"
        print(f"{status} | Query: '{query}'")
        print(f"          Intent: {result.intent} (esperado: 'question')")
        print(f"          Confidence: {result.confidence:.2f}")
        print()

    # Test 2: "ayuda" simple debe clasificarse como 'help'
    print("\nTest 2: 'ayuda' simple debe clasificarse como 'help'")
    print("-" * 80)

    simple_help = [
        "ayuda",
        "help",
        "info",
        "¿qué puedes hacer?",
    ]

    for query in simple_help:
        result = classifier.classify(query)
        status = "✅ CORRECTO" if result.intent == 'help' else "❌ INCORRECTO"
        print(f"{status} | Query: '{query}'")
        print(f"          Intent: {result.intent} (esperado: 'help')")
        print(f"          Confidence: {result.confidence:.2f}")
        print()

    # Test 3: Verificar que no hay kayak/DANA en respuestas
    print("\nTest 3: Verificar que no hay referencias a kayak/DANA")
    print("-" * 80)

    help_response = classifier.predefined_responses['help']

    has_kayak = 'kayak' in help_response.lower()
    has_dana = 'dana' in help_response.lower()

    print("Respuesta de 'help':")
    print(help_response)
    print()

    if has_kayak:
        print("❌ INCORRECTO: La respuesta contiene 'kayak'")
    else:
        print("✅ CORRECTO: No se encontró 'kayak'")

    if has_dana:
        print("❌ INCORRECTO: La respuesta contiene 'DANA'")
    else:
        print("✅ CORRECTO: No se encontró 'DANA'")

    print()

    # Verificar que se mencionan los proyectos correctos
    has_residencias = 'residencias' in help_response.lower() or 'residencia' in help_response.lower()
    has_desayunos = 'desayunos' in help_response.lower()
    has_refuerzo = 'refuerzo' in help_response.lower()

    print("Proyectos mencionados:")
    print(f"  {'✅' if has_desayunos else '❌'} Desayunos solidarios")
    print(f"  {'✅' if has_residencias else '❌'} Residencias")
    print(f"  {'✅' if has_refuerzo else '❌'} Refuerzo escolar")

    print("\n" + "="*80)
    print("TEST COMPLETADO")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_intent_classifier()
