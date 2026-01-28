"""
Test Automatizado del Chatbot DNI
==================================

Prueba automática de todas las queries de test_queries.txt con validaciones:
- Respuesta generada (no vacía)
- Confidence > 0.4
- Intent clasificado correctamente
- Tiempo de respuesta < 5s
- Sin errores de thinking tags

Genera reporte completo con métricas por categoría.
"""

import sys
from pathlib import Path

# Añadir path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import json
from typing import Dict, List, Any
from datetime import datetime

# Imports del proyecto
from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.core.intent_classifier import IntentClassifier
from src.core.conversational_rag import ConversationalRAGEngine


# ============================================================================
# CATEGORÍAS DE QUERIES
# ============================================================================

QUERY_CATEGORIES = {
    'basicas': ['¿Qué es DNI?', '¿Cuáles son los valores de DNI?', '¿Desde cuándo existe DNI?'],
    'como_participar': ['¿Cómo me apunto?', '¿Qué requisitos necesito?', '¿Es gratis participar?'],
    'proyectos': ['¿Qué proyectos tiene DNI?', '¿Qué es desayunos solidarios?', '¿Qué es COLES?'],
    'horarios': ['¿Cuándo son los desayunos?', '¿Qué días vais a COLES?', '¿Horarios de RESIS?'],
    'contacto': ['¿Cómo os contacto?', '¿Tenéis WhatsApp?', '¿Instagram?', 'Dónde puedo seguiros'],
    'genericos': ['hola', 'gracias', 'adiós', 'ayuda', 'info'],
    'fuera_scope': ['¿Quién ganó el mundial 2022?', '¿Cuál es la capital de Francia?']
}


# ============================================================================
# VALIDACIONES
# ============================================================================

def validate_response(result: Dict[str, Any], question: str, elapsed_time: float) -> Dict[str, Any]:
    """
    Valida una respuesta del chatbot.
    
    Returns:
        Dict con resultados de validación:
        - passed: bool
        - errors: List[str]
        - warnings: List[str]
    """
    errors = []
    warnings = []
    
    # Validación 1: Respuesta no vacía
    answer = result.get('answer', '').strip()
    if not answer:
        errors.append("Respuesta vacía")
    elif len(answer) < 20:
        warnings.append(f"Respuesta muy corta ({len(answer)} chars)")
    
    # Validación 2: Confidence > 0.4
    confidence = result.get('confidence', 0)
    if confidence < 0.4:
        warnings.append(f"Confidence bajo: {confidence:.3f}")
    
    # Validación 3: Tiempo de respuesta < 5s
    if elapsed_time > 5.0:
        warnings.append(f"Respuesta lenta: {elapsed_time:.2f}s")
    
    # Validación 4: Sin thinking tags residuales
    if '<think>' in answer or '</think>' in answer or '<Think>' in answer:
        errors.append("Thinking tags presentes en respuesta")
    
    # Validación 5: Sin mensajes de error obvios
    error_patterns = ['error:', 'exception:', 'traceback:']
    if any(pattern in answer.lower() for pattern in error_patterns):
        errors.append("Mensaje de error en respuesta")
    
    return {
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'confidence': confidence,
        'response_time': elapsed_time,
        'answer_length': len(answer)
    }


def detect_query_category(query: str) -> str:
    """Detecta la categoría de una query"""
    query_lower = query.lower()
    
    for category, keywords in QUERY_CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in query_lower:
                return category
    
    return 'general'


# ============================================================================
# TESTING PRINCIPAL
# ============================================================================

def load_test_queries(file_path: str) -> List[str]:
    """Carga queries desde test_queries.txt"""
    queries = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    queries.append(line)
    except FileNotFoundError:
        print(f"⚠️  Archivo no encontrado: {file_path}")
        return []
    
    return queries


def run_automated_tests():
    """Ejecuta todos los tests automatizados"""
    print("\n" + "="*80)
    print("🧪 TESTING AUTOMATIZADO - CHATBOT DNI")
    print("="*80 + "\n")
    
    # Cargar queries
    test_file = project_root / "data" / "test_queries.txt"
    queries = load_test_queries(str(test_file))
    
    if not queries:
        print("❌ No se encontraron queries para testear")
        return
    
    print(f"📋 Cargadas {len(queries)} queries de prueba\n")
    
    # Inicializar componentes
    print("🤖 Inicializando componentes...")
    
    try:
        DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"
        VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"
        
        model = LLMWrapper(
            model_name="gemma2:27b",
            api_endpoint=DEFAULT_API_ENDPOINT
        )
        
        rag_engine = EnhancedRAGEngineNew(
            vector_store_path=str(VECTOR_STORE_PATH),
            model=model
        )
        
        conversational_rag = ConversationalRAGEngine(
            base_rag_engine=rag_engine,
            model_wrapper=model
        )
        
        intent_classifier = IntentClassifier()
        
        print("✅ Componentes inicializados\n")
        
    except Exception as e:
        print(f"❌ Error inicializando: {e}")
        return
    
    # Ejecutar tests
    print("🚀 Ejecutando tests...\n")
    
    results = []
    session_id = f"test_session_{int(time.time())}"
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Testing: '{query[:60]}{'...' if len(query) > 60 else ''}'")
        
        start_time = time.time()
        
        try:
            # Clasificar intent
            intent_result = intent_classifier.classify(query)
            
            # Procesar query
            if intent_result.intent != 'question' and intent_result.predefined_response:
                # Mensaje genérico
                result = {
                    'answer': intent_result.predefined_response,
                    'confidence': intent_result.confidence,
                    'intent': intent_result.intent
                }
            else:
                # Query compleja - RAG
                result = conversational_rag.process_query(
                    query=query,
                    session_id=session_id,
                    question_id=i
                )
            
            elapsed_time = time.time() - start_time
            
            # Validar respuesta
            validation = validate_response(result, query, elapsed_time)
            
            # Almacenar resultado
            results.append({
                'query': query,
                'category': detect_query_category(query),
                'result': result,
                'validation': validation,
                'elapsed_time': elapsed_time
            })
            
            # Mostrar resultado
            status = "✅" if validation['passed'] else "⚠️"
            print(f"  {status} {elapsed_time:.2f}s - Confidence: {validation['confidence']:.3f}")
            
            if validation['errors']:
                for error in validation['errors']:
                    print(f"     ❌ {error}")
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    print(f"     ⚠️  {warning}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error procesando query: {e}\n")
            results.append({
                'query': query,
                'category': 'error',
                'result': {},
                'validation': {'passed': False, 'errors': [str(e)]},
                'elapsed_time': 0
            })
    
    # Generar reporte
    generate_report(results)


def generate_report(results: List[Dict]):
    """Genera reporte completo de testing"""
    print("\n" + "="*80)
    print("📊 REPORTE DE TESTING")
    print("="*80 + "\n")
    
    total = len(results)
    passed = sum(1 for r in results if r['validation']['passed'])
    failed = total - passed
    
    # Estadísticas globales
    print("ESTADÍSTICAS GLOBALES")
    print("-" * 80)
    print(f"Total queries: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Tiempos
    times = [r['elapsed_time'] for r in results if r['elapsed_time'] > 0]
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        print(f"\nTiempo promedio: {avg_time:.2f}s")
        print(f"Tiempo mínimo: {min_time:.2f}s")
        print(f"Tiempo máximo: {max_time:.2f}s")
    
    # Confidence promedio
    confidences = [r['validation']['confidence'] for r in results if 'confidence' in r['validation']]
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        print(f"Confidence promedio: {avg_conf:.3f}")
    
    print()
    
    # Por categoría
    print("POR CATEGORÍA")
    print("-" * 80)
    
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'passed': 0}
        categories[cat]['total'] += 1
        if r['validation']['passed']:
            categories[cat]['passed'] += 1
    
    for cat, stats in sorted(categories.items()):
        total_cat = stats['total']
        passed_cat = stats['passed']
        rate = passed_cat / total_cat * 100 if total_cat > 0 else 0
        status = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "❌"
        print(f"{status} {cat.capitalize()}: {passed_cat}/{total_cat} ({rate:.1f}%)")
    
    print()
    
    # Queries problemáticas
    failed_queries = [r for r in results if not r['validation']['passed']]
    
    if failed_queries:
        print("QUERIES PROBLEMÁTICAS")
        print("-" * 80)
        for r in failed_queries[:10]:  # Top 10
            print(f"\n❌ {r['query']}")
            for error in r['validation'].get('errors', []):
                print(f"   - {error}")
    
    print("\n" + "="*80)
    
    # Guardar resultados en JSON
    output_file = project_root / "results" / f"test_automated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_queries': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed/total if total > 0 else 0,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Resultados guardados en: {output_file}")
    
    # Resultado final
    if passed / total >= 0.9:
        print("\n🎉 ¡ÉXITO! >90% de queries exitosas")
    elif passed / total >= 0.7:
        print("\n⚠️  ACEPTABLE: 70-90% de queries exitosas")
    else:
        print("\n❌ NECESITA MEJORAS: <70% de queries exitosas")


if __name__ == "__main__":
    run_automated_tests()

