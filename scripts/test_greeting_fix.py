#!/usr/bin/env python3
"""
Script de Test - Verificación de eliminación de saludos
========================================================

Verifica que el sistema conversacional NO salude después de la primera interacción.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.conversational_rag import ConversationalRAGEngine


def test_greeting_removal():
    """Test de la función de eliminación de saludos"""

    # Crear instancia mock de ConversationalRAGEngine
    conv_rag = ConversationalRAGEngine(
        base_rag_engine=None,  # No necesitamos RAG real para este test
        model_wrapper=None
    )

    print("\n" + "="*80)
    print("🧪 TEST: Eliminación de Saludos en Conversaciones")
    print("="*80 + "\n")

    # Casos de prueba
    test_cases = [
        # (input, expected_start, description)
        (
            "¡Hola! Sobre la edad, DNI está enfocado principalmente a jóvenes...",
            "Sobre la edad,",
            "Caso 1: ¡Hola! al inicio"
        ),
        (
            "Hola. Entiendo tu pregunta. DNI es una asociación...",
            "Entiendo tu pregunta.",
            "Caso 2: Hola. al inicio"
        ),
        (
            "¡Buenas! En cuanto a la filosofía, nos basamos en...",
            "En cuanto a la filosofía,",
            "Caso 3: ¡Buenas! al inicio"
        ),
        (
            "Buenos días, respecto al voluntariado...",
            "Respecto al voluntariado",
            "Caso 4: Buenos días al inicio"
        ),
        (
            "Sobre el tema que consultas, DNI trabaja...",
            "Sobre el tema que consultas,",
            "Caso 5: Sin saludo (no debería cambiar)"
        ),
        (
            "En cuanto a tu pregunta, podemos decir...",
            "En cuanto a tu pregunta,",
            "Caso 6: Sin saludo (no debería cambiar)"
        ),
        (
            "¡Me alegra que te interese unirte a DNI. Para apuntarte...",
            "Para apuntarte",
            "Caso 7: ¡Me alegra que... al inicio"
        ),
        (
            "¡Qué bien que preguntes! DNI tiene varios proyectos...",
            "DNI tiene varios proyectos",
            "Caso 8: ¡Qué bien que... al inicio"
        ),
    ]

    passed = 0
    failed = 0

    for i, (input_text, expected_start, description) in enumerate(test_cases, 1):
        print(f"{description}")
        print(f"   Input:  {input_text[:60]}...")

        # Aplicar la función de limpieza
        cleaned = conv_rag._remove_unwanted_greetings(input_text)

        print(f"   Output: {cleaned[:60]}...")

        # Verificar que empieza como esperamos
        if cleaned.startswith(expected_start):
            print(f"   ✅ PASS\n")
            passed += 1
        else:
            print(f"   ❌ FAIL - Esperado: '{expected_start[:30]}...'\n")
            failed += 1

    print("="*80)
    print(f"📊 RESULTADOS: {passed}/{len(test_cases)} tests pasaron")
    print("="*80 + "\n")

    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_greeting_removal()
    sys.exit(0 if success else 1)
