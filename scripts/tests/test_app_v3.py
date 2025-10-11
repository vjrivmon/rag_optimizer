#!/usr/bin/env python3
"""
🧪 Script de Testing para app_v3.py

Valida que todos los componentes funcionen correctamente antes de lanzar.
"""

import sys
from pathlib import Path
import json

# Añadir directorio raíz al path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test 1: Verificar que todos los imports funcionen"""
    print("🧪 Test 1: Verificando imports...")
    
    try:
        from interface.qualitative_evaluator import (
            evaluate_qualitative,
            get_evaluation_icon,
            get_evaluation_color,
            calculate_qualitative_stats
        )
        from interface.export_professional import (
            export_to_excel,
            generate_markdown_report
        )
        print("   ✅ Todos los imports correctos")
        return True
    except Exception as e:
        print(f"   ❌ Error en imports: {e}")
        return False


def test_data_files():
    """Test 2: Verificar que existan los archivos necesarios"""
    print("\n🧪 Test 2: Verificando archivos de datos...")
    
    # Verificar dataset
    dataset_path = Path('data/evaluation_dataset.json')
    if not dataset_path.exists():
        print(f"   ❌ No se encuentra: {dataset_path}")
        return False
    print(f"   ✅ Dataset encontrado: {dataset_path}")
    
    # Verificar benchmarks
    results_dir = Path('results')
    benchmark_files = list(results_dir.glob('benchmark_*.json'))
    
    if not benchmark_files:
        print(f"   ❌ No se encontraron archivos benchmark_*.json en {results_dir}")
        return False
    
    print(f"   ✅ Encontrados {len(benchmark_files)} archivos de benchmark")
    print(f"   📁 Más reciente: {benchmark_files[0].name}")
    
    return True


def test_qualitative_evaluator():
    """Test 3: Verificar evaluador cualitativo"""
    print("\n🧪 Test 3: Probando evaluador cualitativo...")
    
    from interface.qualitative_evaluator import evaluate_qualitative, calculate_qualitative_stats
    
    # Test case 1: Respuesta correcta
    result1, explanation1 = evaluate_qualitative(
        "La actividad es en Valencia",
        "La actividad se realiza en Valencia",
        {'combined_score': 0.95, 'faithfulness': 0.9, 'answer_relevancy': 1.0}
    )
    
    if result1 != 'correcta':
        print(f"   ❌ Test 1 falló: esperado 'correcta', obtenido '{result1}'")
        return False
    print("   ✅ Test 1 (correcta) passed")
    
    # Test case 2: Respuesta incorrecta
    result2, explanation2 = evaluate_qualitative(
        "No hay información disponible",
        "La respuesta es X",
        {'combined_score': 0.1, 'faithfulness': 0.0, 'answer_relevancy': 0.0}
    )
    
    if result2 != 'incorrecta':
        print(f"   ❌ Test 2 falló: esperado 'incorrecta', obtenido '{result2}'")
        return False
    print("   ✅ Test 2 (incorrecta) passed")
    
    # Test case 3: Respuesta incompleta
    result3, explanation3 = evaluate_qualitative(
        "La actividad es en algún lugar",
        "La actividad es en Valencia en la calle X",
        {'combined_score': 0.6, 'faithfulness': 0.7, 'answer_relevancy': 0.5}
    )
    
    if result3 != 'incompleta':
        print(f"   ❌ Test 3 falló: esperado 'incompleta', obtenido '{result3}'")
        return False
    print("   ✅ Test 3 (incompleta) passed")
    
    # Test estadísticas
    stats = calculate_qualitative_stats(['correcta', 'correcta', 'incompleta', 'incorrecta'])
    if stats['total'] != 4 or stats['correctas'] != 2:
        print(f"   ❌ Test estadísticas falló")
        return False
    print("   ✅ Test estadísticas passed")
    
    return True


def test_data_loading():
    """Test 4: Verificar carga de datos"""
    print("\n🧪 Test 4: Probando carga y enriquecimiento de datos...")
    
    # Cargar dataset
    dataset_path = Path('data/evaluation_dataset.json')
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    if not dataset or not isinstance(dataset, list):
        print("   ❌ Error: dataset vacío o formato incorrecto")
        return False
    print(f"   ✅ Dataset cargado: {len(dataset)} preguntas")
    
    # Cargar benchmark
    results_dir = Path('results')
    benchmark_files = sorted(
        results_dir.glob('benchmark_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not benchmark_files:
        print("   ❌ No hay benchmarks para probar")
        return False
    
    benchmark_path = benchmark_files[0]
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        benchmark_data = json.load(f)
    
    if not benchmark_data or not isinstance(benchmark_data, list):
        print("   ❌ Error: benchmark vacío o formato incorrecto")
        return False
    print(f"   ✅ Benchmark cargado: {len(benchmark_data)} evaluaciones")
    
    # Verificar estructura
    first_item = benchmark_data[0]
    required_keys = ['question_id', 'model_name', 'question', 'answer', 'metrics', 'generation_time']
    
    missing_keys = [key for key in required_keys if key not in first_item]
    if missing_keys:
        print(f"   ❌ Faltan keys en benchmark: {missing_keys}")
        return False
    print("   ✅ Estructura de benchmark correcta")
    
    # Probar enriquecimiento
    from interface.qualitative_evaluator import evaluate_qualitative
    
    expected_map = {q['id']: q for q in dataset}
    first_item_enriched = first_item.copy()
    qid = first_item['question_id']
    expected_q = expected_map.get(qid, {})
    
    first_item_enriched['expected_answer'] = expected_q.get('expected_answer', 'No disponible')
    eval_result, eval_explanation = evaluate_qualitative(
        first_item['answer'],
        first_item_enriched['expected_answer'],
        first_item['metrics']
    )
    first_item_enriched['qualitative_eval'] = eval_result
    
    if 'expected_answer' not in first_item_enriched or 'qualitative_eval' not in first_item_enriched:
        print("   ❌ Error: enriquecimiento falló")
        return False
    print("   ✅ Enriquecimiento de datos correcto")
    
    return True


def test_export():
    """Test 5: Verificar exportación"""
    print("\n🧪 Test 5: Probando exportación...")
    
    from interface.export_professional import export_to_excel, generate_markdown_report
    
    # Cargar datos mínimos para test
    dataset_path = Path('data/evaluation_dataset.json')
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    results_dir = Path('results')
    benchmark_files = sorted(
        results_dir.glob('benchmark_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not benchmark_files:
        print("   ⚠️ No hay benchmarks, skipping export test")
        return True
    
    benchmark_path = benchmark_files[0]
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        benchmark_data = json.load(f)
    
    # Enriquecer datos (solo primeros 5 para test rápido)
    from interface.qualitative_evaluator import evaluate_qualitative, calculate_qualitative_stats
    
    expected_map = {q['id']: q for q in dataset}
    enriched_sample = []
    
    for item in benchmark_data[:5]:
        item_copy = item.copy()
        qid = item['question_id']
        expected_q = expected_map.get(qid, {})
        item_copy['expected_answer'] = expected_q.get('expected_answer', 'No disponible')
        eval_result, eval_explanation = evaluate_qualitative(
            item['answer'],
            item_copy['expected_answer'],
            item['metrics']
        )
        item_copy['qualitative_eval'] = eval_result
        item_copy['qualitative_explanation'] = eval_explanation
        enriched_sample.append(item_copy)
    
    # Test Excel export
    try:
        excel_buffer = export_to_excel(enriched_sample, dataset)
        if excel_buffer.getbuffer().nbytes == 0:
            print("   ❌ Excel vacío")
            return False
        print(f"   ✅ Excel generado: {excel_buffer.getbuffer().nbytes} bytes")
    except Exception as e:
        print(f"   ❌ Error generando Excel: {e}")
        return False
    
    # Test Markdown export
    try:
        evals = [item['qualitative_eval'] for item in enriched_sample]
        qual_stats = calculate_qualitative_stats(evals)
        markdown = generate_markdown_report(enriched_sample, dataset, qual_stats)
        if not markdown or len(markdown) < 100:
            print("   ❌ Markdown demasiado corto o vacío")
            return False
        print(f"   ✅ Markdown generado: {len(markdown)} caracteres")
    except Exception as e:
        print(f"   ❌ Error generando Markdown: {e}")
        return False
    
    return True


def test_dependencies():
    """Test 6: Verificar dependencias"""
    print("\n🧪 Test 6: Verificando dependencias...")
    
    dependencies = {
        'streamlit': 'Streamlit',
        'pandas': 'Pandas',
        'plotly': 'Plotly',
        'openpyxl': 'OpenPyXL'
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {name} instalado")
        except ImportError:
            print(f"   ❌ {name} NO instalado")
            missing.append(module)
    
    if missing:
        print(f"\n   ⚠️  Instalar dependencias faltantes:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Ejecutar todos los tests"""
    print("=" * 80)
    print("🧪 TESTING RAG OPTIMIZER DASHBOARD V3")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Archivos de datos", test_data_files),
        ("Evaluador cualitativo", test_qualitative_evaluator),
        ("Carga de datos", test_data_loading),
        ("Exportación", test_export),
        ("Dependencias", test_dependencies)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n   💥 Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE TESTS")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}")
    
    print("\n" + "-" * 80)
    print(f"Resultado: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("\n🚀 Puedes ejecutar la app con:")
        print("   streamlit run interface/app_v3.py")
        print("   o")
        print("   ./run_dashboard_v3.sh")
        return 0
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa los errores antes de ejecutar la app.")
        return 1


if __name__ == "__main__":
    exit(main())

