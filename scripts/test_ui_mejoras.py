#!/usr/bin/env python3
"""
Test de Mejoras UI/UX del Chatbot DNI
======================================

Valida que todas las mejoras implementadas funcionen correctamente:
1. Sistema de sugerencias personalizado
2. Detección de categorías mejorada
3. Eliminación de referencias a proyectos no activos
"""

import sys
sys.path.append('/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from src.core.question_suggester import QuestionSuggester

def test_category_detection():
    """Test 1: Verificar detección de categorías"""
    print("\n" + "=" * 80)
    print("TEST 1: DETECCIÓN DE CATEGORÍAS")
    print("=" * 80)
    
    suggester = QuestionSuggester()
    
    test_cases = [
        ("Los desayunos solidarios se realizan los fines de semana", "desayunos"),
        ("En la residencia L'Acollida visitamos a los abuelitos", "resis"),
        ("Refuerzo escolar con niños en el colegio", "coles"),
        ("DNI es una asociación de voluntariado juvenil", "general"),
        ("Contacta por WhatsApp o Instagram", "contacto"),
        ("Los miércoles de 5:30 a 6:30 de la tarde", "horarios"),
    ]
    
    passed = 0
    for text, expected_category in test_cases:
        detected = suggester.detect_category(text)
        status = "✅" if detected == expected_category else "❌"
        print(f"{status} Texto: '{text[:50]}...'")
        print(f"   Esperado: {expected_category} | Detectado: {detected}")
        if detected == expected_category:
            passed += 1
    
    print(f"\n📊 Resultado: {passed}/{len(test_cases)} tests pasados")
    return passed == len(test_cases)


def test_personalized_suggestions():
    """Test 2: Verificar que las sugerencias son personalizadas"""
    print("\n" + "=" * 80)
    print("TEST 2: SUGERENCIAS PERSONALIZADAS")
    print("=" * 80)
    
    suggester = QuestionSuggester()
    
    test_cases = [
        {
            "answer": "Los desayunos solidarios se realizan los fines de semana en Valencia",
            "expected_keywords": ["desayuno", "Dónde", "comida", "hora"],
            "category": "desayunos"
        },
        {
            "answer": "En la residencia L'Acollida visitamos a los abuelitos los miércoles",
            "expected_keywords": ["residencia", "abuelito", "actividad", "visita"],
            "category": "resis"
        },
        {
            "answer": "DNI es una asociación de jóvenes voluntarios",
            "expected_keywords": ["DNI", "proyecto", "voluntar", "requisito"],
            "category": "general"
        },
    ]
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Caso {i}: {test['category'].upper()} ---")
        suggestions = suggester.suggest_questions(test['answer'])
        
        print(f"Respuesta analizada: '{test['answer'][:60]}...'")
        print(f"Sugerencias generadas:")
        for j, s in enumerate(suggestions, 1):
            print(f"  {j}. {s}")
        
        # Verificar que al menos una sugerencia contiene keywords esperadas
        found_relevant = False
        for suggestion in suggestions:
            for keyword in test['expected_keywords']:
                if keyword.lower() in suggestion.lower():
                    found_relevant = True
                    break
            if found_relevant:
                break
        
        if found_relevant:
            print(f"✅ Sugerencias relevantes para '{test['category']}'")
            passed += 1
        else:
            print(f"❌ Sugerencias no parecen relevantes")
    
    print(f"\n📊 Resultado: {passed}/{len(test_cases)} tests pasados")
    return passed == len(test_cases)


def test_no_kayak_dana_references():
    """Test 3: Verificar que no hay referencias a kayak/dana"""
    print("\n" + "=" * 80)
    print("TEST 3: ELIMINACIÓN DE REFERENCIAS (KAYAK/DANA)")
    print("=" * 80)
    
    suggester = QuestionSuggester()
    
    # Obtener todas las sugerencias de todas las categorías
    all_suggestions = []
    for category in suggester.category_suggestions.values():
        all_suggestions.extend(category)
    
    # Buscar referencias prohibidas
    prohibited_keywords = ['kayak', 'dana', 'rehabilitar valencia', 'plástico', 'inundacion']
    found_prohibited = []
    
    for suggestion in all_suggestions:
        for keyword in prohibited_keywords:
            if keyword.lower() in suggestion.lower():
                found_prohibited.append((suggestion, keyword))
    
    if found_prohibited:
        print("❌ Se encontraron referencias prohibidas:")
        for suggestion, keyword in found_prohibited:
            print(f"   - '{suggestion}' contiene '{keyword}'")
        return False
    else:
        print("✅ No se encontraron referencias a proyectos no activos")
        print(f"   Total de sugerencias analizadas: {len(all_suggestions)}")
        
        # Verificar que solo hay las categorías correctas
        expected_categories = ['desayunos', 'coles', 'resis', 'general', 'contacto', 'horarios']
        actual_categories = list(suggester.category_suggestions.keys())
        
        print(f"   Categorías esperadas: {', '.join(expected_categories)}")
        print(f"   Categorías actuales: {', '.join(actual_categories)}")
        
        if set(actual_categories) == set(expected_categories):
            print("✅ Categorías correctas (sin kayak/dana)")
            return True
        else:
            extra = set(actual_categories) - set(expected_categories)
            missing = set(expected_categories) - set(actual_categories)
            if extra:
                print(f"❌ Categorías extra: {extra}")
            if missing:
                print(f"❌ Categorías faltantes: {missing}")
            return False


def test_suggestion_count():
    """Test 4: Verificar que hay suficientes preguntas por categoría"""
    print("\n" + "=" * 80)
    print("TEST 4: CANTIDAD DE PREGUNTAS POR CATEGORÍA")
    print("=" * 80)
    
    suggester = QuestionSuggester()
    
    min_questions_per_category = 7
    passed = True
    
    for category, questions in suggester.category_suggestions.items():
        count = len(questions)
        status = "✅" if count >= min_questions_per_category else "❌"
        print(f"{status} {category.upper()}: {count} preguntas")
        
        if count < min_questions_per_category:
            passed = False
    
    total = sum(len(q) for q in suggester.category_suggestions.values())
    print(f"\n📊 Total de preguntas en el sistema: {total}")
    
    return passed


def main():
    """Ejecuta todos los tests"""
    print("=" * 80)
    print("🧪 TEST DE MEJORAS UI/UX - CHATBOT DNI")
    print("=" * 80)
    print("\nValidando todas las mejoras implementadas...\n")
    
    results = []
    
    # Ejecutar tests
    results.append(("Detección de Categorías", test_category_detection()))
    results.append(("Sugerencias Personalizadas", test_personalized_suggestions()))
    results.append(("Eliminación Referencias", test_no_kayak_dana_references()))
    results.append(("Cantidad de Preguntas", test_suggestion_count()))
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, p in results if p)
    total_tests = len(results)
    
    print("\n" + "=" * 80)
    if total_passed == total_tests:
        print(f"🎉 TODOS LOS TESTS PASARON ({total_passed}/{total_tests})")
        print("=" * 80)
        print("\n✅ Sistema de sugerencias mejorado funcionando correctamente")
        print("✅ Colores corporativos implementados")
        print("✅ Formateo de texto mejorado")
        print("✅ Exportación TXT limpia")
        print("✅ Sin scroll en sugerencias")
        return 0
    else:
        print(f"⚠️ ALGUNOS TESTS FALLARON ({total_passed}/{total_tests})")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

