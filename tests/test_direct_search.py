#!/usr/bin/env python3
"""
Test directo de búsqueda en ChromaDB
Verifica por qué no se encuentran las respuestas correctas
"""

import chromadb
from sentence_transformers import SentenceTransformer
from colorama import init, Fore, Style

init(autoreset=True)

print(f"\n{Fore.RED}TEST DIRECTO DE BÚSQUEDA EN CHROMADB{Style.RESET_ALL}\n")

# Inicializar ChromaDB
client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")
collection = client.get_collection("langchain")

# Cargar el mismo modelo de embeddings usado por el sistema
embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')

# Preguntas problemáticas
test_queries = [
    ("¿Dónde es la actividad de coles?", ["CEIP", "Antonio", "Ferrandis"]),
    ("¿Quién paga la gasolina para ir a coles?", ["gasolina", "asociación"]),
    ("¿Dónde es la actividad de resis?", ["Acollida", "Crevillente"]),
    ("coles CEIP Antonio Ferrandis", ["CEIP", "Antonio"]),  # Búsqueda directa
    ("residencia La Acollida Crevillente", ["Acollida", "Crevillente"])  # Búsqueda directa
]

for query, keywords in test_queries:
    print(f"\n{Fore.CYAN}Query: {query}{Style.RESET_ALL}")
    print(f"Keywords esperadas: {keywords}")

    # Búsqueda por embeddings
    query_embedding = embedder.encode([query])

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=5
    )

    print(f"\n{Fore.YELLOW}Top 5 resultados:{Style.RESET_ALL}")
    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0]), 1):
        # Verificar keywords
        found_keywords = [kw for kw in keywords if kw.lower() in doc.lower()]

        if found_keywords:
            color = Fore.GREEN
            status = f"✅ Contiene: {found_keywords}"
        else:
            color = Fore.RED
            status = "❌ NO contiene keywords"

        print(f"\n  {color}[{i}] Distancia: {distance:.3f} - {status}{Style.RESET_ALL}")
        print(f"      {doc[:200]}...")

print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.CYAN}ANÁLISIS DE EMBEDDINGS{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

# Comparar similitud de embeddings
queries_to_compare = [
    "¿Dónde es la actividad de coles?",
    "CEIP Antonio Ferrandis Coma Valencia",
    "coles refuerzo escolar",
    "actividad coles"
]

target_text = "¿Dónde es?\nEs en el CEIP Antonio Ferrandis de la Coma, Valencia."

print(f"Texto objetivo: {target_text[:100]}...\n")
target_embedding = embedder.encode([target_text])

for query in queries_to_compare:
    query_embedding = embedder.encode([query])

    # Calcular similitud coseno
    from numpy import dot
    from numpy.linalg import norm

    similarity = dot(query_embedding[0], target_embedding[0]) / (norm(query_embedding[0]) * norm(target_embedding[0]))

    color = Fore.GREEN if similarity > 0.5 else Fore.YELLOW if similarity > 0.3 else Fore.RED
    print(f"{color}Query: '{query}'{Style.RESET_ALL}")
    print(f"  Similitud: {similarity:.3f}")

print(f"\n{Fore.RED}CONCLUSIÓN:{Style.RESET_ALL}")
print("El problema parece estar en que las preguntas no tienen alta similitud")
print("semántica con las respuestas debido a la diferencia de formulación.")