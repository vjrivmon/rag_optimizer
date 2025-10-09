#!/usr/bin/env python3
"""
Diagnóstico del sistema de retrieval
Investiga por qué no se encuentran las respuestas correctas
"""

import json
import warnings
from colorama import init, Fore, Style
from src.core.rag_engine import ConfigurableRAGEngine
import chromadb

# Inicializar
init(autoreset=True)
warnings.filterwarnings('ignore')

print(f"\n{Fore.RED}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.RED}DIAGNÓSTICO DEL SISTEMA DE RETRIEVAL{Style.RESET_ALL}")
print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}\n")

# Inicializar RAG
rag = ConfigurableRAGEngine(
    vector_store_path="data/vectorstore/chroma_db",
    use_hybrid=True
)

# Preguntas problemáticas y sus respuestas esperadas
problematic_questions = [
    {
        "id": 11,
        "question": "¿Dónde es la actividad de coles?",
        "expected": "Es en el CEIP Antonio Ferrandis de la Coma, Valencia.",
        "keywords": ["CEIP", "Antonio", "Ferrandis", "Coma", "coles"]
    },
    {
        "id": 16,
        "question": "¿Quién paga la gasolina para ir a coles?",
        "expected": "De la gasolina se encarga la asociación.",
        "keywords": ["gasolina", "asociación", "paga", "coles"]
    },
    {
        "id": 20,
        "question": "¿Dónde es la actividad de resis?",
        "expected": "En la residencia La Acollida, muy cerca de Blasco Ibáñez en la calle Crevillente 22.",
        "keywords": ["La Acollida", "Blasco Ibáñez", "Crevillente", "residencia", "resis"]
    },
    {
        "id": 25,
        "question": "¿Qué significa Para-Mira-Ayuda?",
        "expected": "Son las tres palabras que guían la labor de los voluntarios de DNI...",
        "keywords": ["Para", "Mira", "Ayuda", "PARAR", "MIRAR", "AYUDAR", "DNI"]
    }
]

# Análisis detallado por pregunta
for q_data in problematic_questions:
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Q{q_data['id']}: {q_data['question']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}Respuesta esperada:{Style.RESET_ALL}")
    print(f"  {q_data['expected'][:100]}...")

    print(f"\n{Fore.YELLOW}Keywords clave:{Style.RESET_ALL}")
    print(f"  {', '.join(q_data['keywords'])}")

    # Recuperar chunks
    print(f"\n{Fore.YELLOW}Chunks recuperados:{Style.RESET_ALL}")
    docs = rag.retrieve(q_data['question'])

    for i, doc in enumerate(docs[:5], 1):
        content = doc['content']
        score = doc.get('score', 0)
        metadata = doc.get('metadata', {})

        # Verificar si contiene keywords relevantes
        keywords_found = []
        for kw in q_data['keywords']:
            if kw.lower() in content.lower():
                keywords_found.append(kw)

        print(f"\n  {Fore.CYAN}Chunk {i} (score: {score:.3f}):{Style.RESET_ALL}")
        print(f"    Tipo: {metadata.get('type', 'unknown')}")
        print(f"    Source: {metadata.get('source', 'unknown')}")
        print(f"    Keywords encontradas: {keywords_found if keywords_found else 'NINGUNA'}")
        print(f"    Contenido: {content[:200]}...")

        # Verificar si contiene la respuesta
        if any(word in content.lower() for word in ["antonio ferrandis", "ceip", "coma"] if q_data['id'] == 11):
            print(f"    {Fore.GREEN}✅ CONTIENE INFO RELEVANTE{Style.RESET_ALL}")
        elif any(word in content.lower() for word in ["acollida", "crevillente", "blasco"] if q_data['id'] == 20):
            print(f"    {Fore.GREEN}✅ CONTIENE INFO RELEVANTE{Style.RESET_ALL}")
        elif "gasolina" in content.lower() and q_data['id'] == 16:
            print(f"    {Fore.GREEN}✅ CONTIENE INFO RELEVANTE{Style.RESET_ALL}")
        else:
            print(f"    {Fore.RED}❌ NO contiene info relevante{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}ANÁLISIS DIRECTO DE CHROMADB{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

# Acceso directo a ChromaDB
client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")
collection = client.get_collection("rag_collection")

# Buscar información específica
print(f"{Fore.YELLOW}Búsqueda directa en ChromaDB:{Style.RESET_ALL}\n")

# Buscar CEIP Antonio Ferrandis
print(f"1. Buscando 'CEIP Antonio Ferrandis':")
results = collection.query(
    query_texts=["CEIP Antonio Ferrandis Coma Valencia"],
    n_results=3
)
if results['documents'][0]:
    for i, doc in enumerate(results['documents'][0], 1):
        print(f"   Doc {i}: {doc[:150]}...")
else:
    print(f"   {Fore.RED}❌ No encontrado{Style.RESET_ALL}")

# Buscar La Acollida
print(f"\n2. Buscando 'La Acollida Crevillente':")
results = collection.query(
    query_texts=["La Acollida residencia Crevillente Blasco Ibáñez"],
    n_results=3
)
if results['documents'][0]:
    for i, doc in enumerate(results['documents'][0], 1):
        print(f"   Doc {i}: {doc[:150]}...")
else:
    print(f"   {Fore.RED}❌ No encontrado{Style.RESET_ALL}")

# Buscar Para-Mira-Ayuda
print(f"\n3. Buscando 'Para Mira Ayuda':")
results = collection.query(
    query_texts=["Para Mira Ayuda PARAR MIRAR AYUDAR DNI"],
    n_results=3
)
if results['documents'][0]:
    for i, doc in enumerate(results['documents'][0], 1):
        print(f"   Doc {i}: {doc[:150]}...")
else:
    print(f"   {Fore.RED}❌ No encontrado{Style.RESET_ALL}")

# Verificar total de documentos
print(f"\n{Fore.YELLOW}Estadísticas de la colección:{Style.RESET_ALL}")
collection_data = collection.get()
total_docs = len(collection_data['documents'])
print(f"  Total de chunks: {total_docs}")

# Buscar chunks que contengan palabras clave específicas
print(f"\n{Fore.YELLOW}Búsqueda por palabras clave exactas:{Style.RESET_ALL}\n")

keywords_to_search = ["CEIP", "Antonio Ferrandis", "Acollida", "Crevillente", "gasolina", "Para-Mira-Ayuda"]

for keyword in keywords_to_search:
    count = 0
    found_chunks = []
    for doc in collection_data['documents']:
        if keyword.lower() in doc.lower():
            count += 1
            found_chunks.append(doc[:100])

    if count > 0:
        print(f"  '{keyword}': {Fore.GREEN}{count} chunks encontrados{Style.RESET_ALL}")
        if found_chunks:
            print(f"    Ejemplo: {found_chunks[0]}...")
    else:
        print(f"  '{keyword}': {Fore.RED}0 chunks encontrados ❌{Style.RESET_ALL}")

print(f"\n{Fore.RED}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.RED}CONCLUSIONES DEL DIAGNÓSTICO{Style.RESET_ALL}")
print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}\n")