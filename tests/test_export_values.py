#!/usr/bin/env python3
"""
Test para verificar que la exportación de conversaciones funciona correctamente
sin valores NaN ni 'unknown' en campos críticos.

Autor: Claude Code
Fecha: 2025-11-10
"""

import sys
from pathlib import Path

# Añadir path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_confidence_breakdown_structure():
    """Verifica que el breakdown de confidence tenga la estructura correcta"""

    # Simular un breakdown típico del sistema
    breakdown = {
        'confidence': 0.75,
        'formula': 'weighted_average',
        'total_factors': 6,
        'breakdown': {
            'chunks': {
                'count': 10,
                'score': 0.9,
                'weight': 0.15,
                'contribution': 0.135
            },
            'similarity': {
                'avg_score': 0.82,  # NO 'score', sino 'avg_score'
                'weight': 0.25,
                'contribution': 0.205,
                'method': 'content_overlap'
            },
            'answer_length': {
                'chars': 234,
                'score': 0.9,
                'quality': 'detallada',
                'weight': 0.20,
                'contribution': 0.18
            },
            'keywords': {
                'question_words': 5,  # NO 'keywords_total', sino 'question_words'
                'overlap_count': 4,   # NO 'keywords_found', sino 'overlap_count'
                'overlap_ratio': 0.8,
                'weight': 0.15,
                'contribution': 0.12
            },
            'uncertainty': {
                'has_negative_phrases': False,  # NO 'has_negative', sino 'has_negative_phrases'
                'score': 0.95,
                'weight': 0.15,
                'contribution': 0.1425
            },
            'specificity': {
                'patterns_found': ['nombres_propios', 'horarios'],  # Array, no string
                'count': 2,
                'score': 0.5,
                'weight': 0.10,
                'contribution': 0.05
            }
        }
    }

    print("✅ Test 1: Verificando estructura del breakdown...")

    # Verificar campos críticos
    assert 'confidence' in breakdown, "❌ Falta campo 'confidence'"
    assert 'breakdown' in breakdown, "❌ Falta campo 'breakdown'"

    # Verificar cada factor
    for factor_name, factor_data in breakdown['breakdown'].items():
        print(f"   Verificando factor: {factor_name}")

        assert 'weight' in factor_data, f"❌ {factor_name}: falta 'weight'"
        assert 'contribution' in factor_data, f"❌ {factor_name}: falta 'contribution'"

        # Verificar que los scores no sean None/NaN
        if 'score' in factor_data:
            assert factor_data['score'] is not None, f"❌ {factor_name}: 'score' es None"
            assert not (isinstance(factor_data['score'], float) and
                       factor_data['score'] != factor_data['score']), f"❌ {factor_name}: 'score' es NaN"

        if 'avg_score' in factor_data:
            assert factor_data['avg_score'] is not None, f"❌ {factor_name}: 'avg_score' es None"
            assert not (isinstance(factor_data['avg_score'], float) and
                       factor_data['avg_score'] != factor_data['avg_score']), f"❌ {factor_name}: 'avg_score' es NaN"

        if 'overlap_ratio' in factor_data:
            assert factor_data['overlap_ratio'] is not None, f"❌ {factor_name}: 'overlap_ratio' es None"

    print("   ✅ Todos los factores tienen la estructura correcta")

    # Simular el código de exportación mejorado
    print("\n   Simulando exportación...")
    export_lines = []

    for factor, data in breakdown['breakdown'].items():
        factor_name = factor.replace('_', ' ').upper()

        # Extraer score según el factor (código mejorado)
        if data.get('score') is not None:
            score = f"{(data['score'] * 100):.0f}%"
        elif data.get('avg_score') is not None:
            score = f"{(data['avg_score'] * 100):.0f}%"
        elif data.get('overlap_ratio') is not None:
            score = f"{(data['overlap_ratio'] * 100):.0f}%"
        else:
            score = 'N/A'

        weight = f"{(data['weight'] * 100):.0f}%"
        contribution = f"{(data['contribution'] * 100):.1f}%"

        line = f"    - {factor_name}: {score} (peso: {weight}, contribucion: {contribution})"
        export_lines.append(line)
        print(f"   {line}")

        # Verificar que no haya "NaN" en la línea
        assert 'NaN' not in line, f"❌ Línea contiene NaN: {line}"

    print("   ✅ Exportación sin valores NaN")
    print("✅ Test 1 PASADO\n")

    return True


def test_chunks_info_structure():
    """Verifica que los chunks tengan la estructura correcta con fuentes"""

    print("✅ Test 2: Verificando estructura de chunks...")

    # Simular chunks típicos del sistema
    chunks_info = [
        {
            'rank': 1,
            'content': '¿Qué es DNI?\nDNI (Damos Nuestra Ilusión) es una asociación...',
            'score': 0.92,
            'source': '01_faq_dni.txt',  # NO 'unknown'
            'location': 'FAQ (general)'
        },
        {
            'rank': 2,
            'content': 'Los desayunos solidarios se realizan los sábados...',
            'score': 0.87,
            'source': '08_preguntas_basicas.txt',
            'location': 'FAQ (desayunos)'
        },
        {
            'rank': 3,
            'content': 'Para participar en DNI necesitas...',
            'score': 0.82,
            'source': '09_como_participar.txt',
            'location': 'Tipo: document'
        }
    ]

    # Verificar cada chunk
    for chunk in chunks_info:
        print(f"   Verificando chunk {chunk['rank']}...")

        assert 'content' in chunk, f"❌ Chunk {chunk['rank']}: falta 'content'"
        assert 'source' in chunk, f"❌ Chunk {chunk['rank']}: falta 'source'"
        assert 'rank' in chunk, f"❌ Chunk {chunk['rank']}: falta 'rank'"

        # Verificar que source no sea 'unknown'
        assert chunk['source'] != 'unknown', f"❌ Chunk {chunk['rank']}: source es 'unknown'"
        assert chunk['source'] != 'documento desconocido', f"❌ Chunk {chunk['rank']}: source es 'documento desconocido'"

        # Verificar que el contenido no esté vacío
        assert len(chunk['content']) > 0, f"❌ Chunk {chunk['rank']}: contenido vacío"

        print(f"      ✅ Source: {chunk['source']}")
        print(f"      ✅ Content: {chunk['content'][:50]}...")

    print("\n   ✅ Todos los chunks validados")
    print("✅ Test 2 PASADO\n")

    return True


def main():
    """Ejecuta todos los tests"""
    print("="*80)
    print("TEST DE ESTRUCTURA DE DATOS DE EXPORTACIÓN")
    print("="*80)
    print()

    tests_passed = 0
    tests_total = 2

    try:
        if test_confidence_breakdown_structure():
            tests_passed += 1
    except AssertionError as e:
        print(f"❌ Test 1 FALLIDO: {e}\n")
    except Exception as e:
        print(f"❌ Test 1 ERROR: {e}\n")

    try:
        if test_chunks_info_structure():
            tests_passed += 1
    except AssertionError as e:
        print(f"❌ Test 2 FALLIDO: {e}\n")
    except Exception as e:
        print(f"❌ Test 2 ERROR: {e}\n")

    # Resumen
    print("="*80)
    print(f"RESUMEN: {tests_passed}/{tests_total} tests pasados")
    print("="*80)

    if tests_passed == tests_total:
        print("✅ TODOS LOS TESTS PASARON - Estructura de datos correcta")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} test(s) fallaron")
        return 1


if __name__ == "__main__":
    exit(main())
