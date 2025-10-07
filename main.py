import yaml
import warnings
import os
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper
from src.evaluation.evaluator import ResponseEvaluator
from src.orchestrator.orchestrator import SystemOrchestrator

# Suprimir warnings de SSL
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def main():
    print("🚀 INICIANDO SISTEMA RAG AUTO-OPTIMIZER")
    print("="*60)

    # Cargar configuración
    print("\n⚙️  Cargando configuración...")
    with open('config/models_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print("   ✓ Configuración cargada")

    # Crear RAG Engine
    print("\n📚 Cargando RAG Engine...")
    rag = ConfigurableRAGEngine("data/vectorstore/chroma_db")
    print("   ✓ RAG Engine cargado")

    # Crear modelos
    print("\n🤖 Configurando modelos...")
    models = []
    for model_config in config['models']:
        model = LLMWrapper(
            model_name=model_config['name'],
            api_endpoint=model_config['endpoint'],
            context_window=model_config['context_window']
        )
        models.append(model)
        print(f"   ✓ {model_config['name']} - {model_config.get('description', '')}")

    # Crear evaluador
    print("\n📊 Inicializando evaluador...")
    evaluator = ResponseEvaluator()
    print("   ✓ Evaluador listo")

    # Crear orquestador
    print("\n🎯 Creando orquestador...")
    orchestrator = SystemOrchestrator(rag, models, evaluator)
    print("   ✓ Orquestador listo")

    # Crear carpeta de resultados
    os.makedirs('results', exist_ok=True)
    print("   ✓ Directorio de resultados creado")

    # Ejecutar evaluación
    print("\n" + "="*60)
    print("🔄 INICIANDO EVALUACIÓN")
    print("="*60)
    orchestrator.run_evaluation('data/evaluation_dataset.json')

    print("\n" + "="*60)
    print("✅ PROCESO COMPLETADO")
    print("="*60)
    print("\n📂 Resultados guardados en: results/evaluation_results.json")
    print("\n💡 Para visualizar los resultados:")
    print("   streamlit run interface/app.py")

if __name__ == "__main__":
    main()
