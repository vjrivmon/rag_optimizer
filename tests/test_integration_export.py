#!/usr/bin/env python3
"""
Test de integración para verificar que el sistema completo exporta correctamente
los valores sin NaN ni 'unknown'.

Este test carga los componentes reales del sistema y hace una query de prueba.
"""

import sys
from pathlib import Path

# Añadir path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew


def test_real_confidence_breakdown():
    """Test con datos reales del sistema"""
    print("="*80)
    print("TEST DE INTEGRACIÓN: Confidence Breakdown")
    print("="*80)
    print()

    try:
        # Inicializar componentes
        print("📦 Inicializando componentes...")
        
        VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"
        
        if not VECTOR_STORE_PATH.exists():
            print(f"❌ Vector store no existe en: {VECTOR_STORE_PATH}")
            print("⚠️  Ejecuta primero: python scripts/02_create_faq_aware_chunks.py")
            return False
            
        model = LLMWrapper(
            model_name="gemma2:27b",
            api_endpoint="https://ollama.gti-ia.upv.es:443/api/generate"
        )
        print("   ✓ Modelo cargado")
        
        rag_engine = EnhancedRAGEngineNew(
            vector_store_path=str(VECTOR_STORE_PATH),
            model=model
        )
        print("   ✓ RAG Engine cargado")
        print()

        # Query de test
        question = "¿Qué es DNI?"
        print(f"❓ Query de test: {question}")
        print()

        # Recuperar chunks (sin generar respuesta completa para hacer el test más rápido)
        print("🔍 Recuperando chunks...")
        chunks = rag_engine.base_rag.retrieve(question)
        print(f"   ✓ {len(chunks)} chunks recuperados")
        print()

        # Simular una respuesta típica
        answer = "DNI (Damos Nuestra Ilusión) es una asociación de jóvenes voluntarios en Valencia con el lema PARA. MIRA. AYUDA."
        
        # 1. Test del confidence breakdown
        print("🧪 Test 1: Calculando confidence con breakdown...")
        confidence_data = rag_engine.calculate_confidence_with_breakdown(chunks, answer, question)
        
        print(f"   Confidence: {confidence_data['confidence']:.3f}")
        print(f"   Total factors: {confidence_data['total_factors']}")
        print()

        # Verificar estructura
        assert 'confidence' in confidence_data, "❌ Falta campo 'confidence'"
        assert 'breakdown' in confidence_data, "❌ Falta campo 'breakdown'"
        assert 'total_factors' in confidence_data, "❌ Falta campo 'total_factors'"
        
        print("   Verificando factores del breakdown:")
        for factor_name, factor_data in confidence_data['breakdown'].items():
            print(f"      • {factor_name}")
            
            # Verificar campos obligatorios
            assert 'weight' in factor_data, f"❌ {factor_name}: falta 'weight'"
            assert 'contribution' in factor_data, f"❌ {factor_name}: falta 'contribution'"
            
            # Verificar que ningún valor sea NaN
            for key, value in factor_data.items():
                if isinstance(value, float):
                    assert value == value, f"❌ {factor_name}.{key} es NaN"
                    
        print("   ✅ Todos los factores tienen valores válidos (sin NaN)")
        print()

        # 2. Test de top chunks info
        print("🧪 Test 2: Extrayendo información de top chunks...")
        top_chunks_info = rag_engine.extract_top_chunks_info(chunks, top_n=3)
        
        print(f"   Total chunks extraídos: {len(top_chunks_info)}")
        print()

        print("   Verificando chunks:")
        for chunk in top_chunks_info:
            print(f"      • Chunk {chunk['rank']}")
            print(f"        Source: {chunk['source']}")
            print(f"        Content: {chunk['content'][:50]}...")
            
            # Verificar campos obligatorios
            assert 'rank' in chunk, "❌ Falta campo 'rank'"
            assert 'content' in chunk, "❌ Falta campo 'content'"
            assert 'source' in chunk, "❌ Falta campo 'source'"
            
            # Verificar que source no sea 'unknown'
            assert chunk['source'] != 'unknown', f"❌ Chunk {chunk['rank']}: source es 'unknown'"
            assert chunk['source'] != 'documento desconocido', f"❌ Chunk {chunk['rank']}: source es 'documento desconocido'"
            
            # Verificar que tenga contenido
            assert len(chunk['content']) > 0, f"❌ Chunk {chunk['rank']}: contenido vacío"
            
        print("   ✅ Todos los chunks tienen fuentes válidas (sin 'unknown')")
        print()

        # Resumen
        print("="*80)
        print("✅ TODOS LOS TESTS DE INTEGRACIÓN PASARON")
        print("="*80)
        print()
        print("📊 Resumen:")
        print(f"   • Confidence calculado: {confidence_data['confidence']:.3f}")
        print(f"   • Factores validados: {len(confidence_data['breakdown'])}")
        print(f"   • Chunks con fuentes: {len(top_chunks_info)}")
        print(f"   • Sin valores NaN: ✅")
        print(f"   • Sin valores 'unknown': ✅")
        print()

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    success = test_real_confidence_breakdown()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
