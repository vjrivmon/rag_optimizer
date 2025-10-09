#!/usr/bin/env python3
"""
Script para recrear el vector store con los embeddings correctos
y asegurar que toda la información crítica esté indexada
"""

import os
import warnings
from pathlib import Path
from colorama import init, Fore, Style
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import chromadb

# Inicializar
init(autoreset=True)
warnings.filterwarnings('ignore')

print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.GREEN}RECREANDO VECTOR STORE CON EMBEDDINGS CORRECTOS{Style.RESET_ALL}")
print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")

# 1. CONFIGURAR EMBEDDINGS CORRECTOS
print(f"{Fore.YELLOW}1. Configurando embeddings...{Style.RESET_ALL}")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
print(f"   ✅ Modelo: paraphrase-multilingual-mpnet-base-v2 (768 dims)")

# 2. CARGAR DOCUMENTOS
print(f"\n{Fore.YELLOW}2. Cargando documentos...{Style.RESET_ALL}")
docs_dir = Path("data/documents")
documents = []

for file_path in docs_dir.glob("*.txt"):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        documents.append(Document(
            page_content=content,
            metadata={"source": str(file_path)}
        ))
        print(f"   📄 {file_path.name}: {len(content)} chars")

# 3. CHUNKING MEJORADO
print(f"\n{Fore.YELLOW}3. Creando chunks optimizados...{Style.RESET_ALL}")

# Configuración optimizada para preguntas FAQ
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,  # Chunks más pequeños para mejor precisión
    chunk_overlap=100,  # Mayor overlap para no perder contexto
    separators=[
        "\n\n¿",  # Priorizar separación por preguntas FAQ
        "\n¿",
        "\n\n",
        "\n",
        ". ",
        ", ",
        " "
    ],
    keep_separator=True
)

all_chunks = []
for doc in documents:
    chunks = text_splitter.split_documents([doc])

    # Procesar chunks para mejorar el retrieval
    for chunk in chunks:
        content = chunk.page_content.strip()

        # Detectar y marcar chunks importantes
        chunk_type = "general"
        importance = "normal"

        # Detectar FAQs
        if content.startswith("¿") and "\n" in content:
            chunk_type = "faq"
            importance = "high"

        # Detectar información crítica
        critical_keywords = ["CEIP", "Antonio Ferrandis", "Acollida", "Crevillente", "gasolina", "Para-Mira-Ayuda", "PARAR", "MIRAR", "AYUDAR"]
        if any(kw in content for kw in critical_keywords):
            importance = "critical"

        # Detectar tipo de actividad
        activity = None
        if "coles" in content.lower() or "refuerzo escolar" in content.lower():
            activity = "coles"
        elif "resis" in content.lower() or "residencia" in content.lower():
            activity = "resis"
        elif "desayuno" in content.lower():
            activity = "desayunos"

        # Actualizar metadata
        chunk.metadata.update({
            "chunk_type": chunk_type,
            "importance": importance,
            "activity": activity,
            "chunk_size": len(content)
        })

        all_chunks.append(chunk)

print(f"   Total chunks: {len(all_chunks)}")

# Analizar chunks críticos
critical_chunks = [c for c in all_chunks if c.metadata.get('importance') == 'critical']
faq_chunks = [c for c in all_chunks if c.metadata.get('chunk_type') == 'faq']

print(f"   📌 Chunks críticos: {len(critical_chunks)}")
print(f"   ❓ Chunks FAQ: {len(faq_chunks)}")

# 4. VERIFICAR INFORMACIÓN CRÍTICA
print(f"\n{Fore.YELLOW}4. Verificando información crítica...{Style.RESET_ALL}")

critical_info = {
    "CEIP Antonio Ferrandis": False,
    "La Acollida": False,
    "gasolina asociación": False,
    "Para-Mira-Ayuda": False
}

for chunk in all_chunks:
    content = chunk.page_content.lower()
    if "ceip" in content and "antonio ferrandis" in content:
        critical_info["CEIP Antonio Ferrandis"] = True
        print(f"   ✅ Encontrado: CEIP Antonio Ferrandis")
        print(f"      {chunk.page_content[:100]}...")

    if "acollida" in content and "crevillente" in content:
        critical_info["La Acollida"] = True
        print(f"   ✅ Encontrado: La Acollida")
        print(f"      {chunk.page_content[:100]}...")

    if "gasolina" in content and "asociación" in content:
        critical_info["gasolina asociación"] = True
        print(f"   ✅ Encontrado: Gasolina asociación")
        print(f"      {chunk.page_content[:100]}...")

    if "para" in content and "mira" in content and "ayuda" in content:
        critical_info["Para-Mira-Ayuda"] = True
        print(f"   ✅ Encontrado: Para-Mira-Ayuda")
        print(f"      {chunk.page_content[:100]}...")

# 5. CREAR NUEVO VECTOR STORE
print(f"\n{Fore.YELLOW}5. Creando nuevo vector store...{Style.RESET_ALL}")

# Limpiar vector store existente
vector_store_path = "data/vectorstore/chroma_db_fixed"
if os.path.exists(vector_store_path):
    import shutil
    shutil.rmtree(vector_store_path)
    print(f"   🗑️ Vector store anterior eliminado")

# Crear nuevo vector store
vector_store = Chroma.from_documents(
    documents=all_chunks,
    embedding=embeddings,
    persist_directory=vector_store_path,
    collection_name="rag_collection_fixed"
)

print(f"   ✅ Vector store creado: {vector_store_path}")
print(f"   ✅ Colección: rag_collection_fixed")

# 6. PROBAR BÚSQUEDAS
print(f"\n{Fore.YELLOW}6. Probando búsquedas críticas...{Style.RESET_ALL}")

test_queries = [
    "¿Dónde es la actividad de coles?",
    "¿Quién paga la gasolina para ir a coles?",
    "¿Dónde es la actividad de resis?",
    "¿Qué significa Para-Mira-Ayuda?"
]

for query in test_queries:
    print(f"\n   Query: {query}")
    results = vector_store.similarity_search(query, k=3)

    for i, doc in enumerate(results, 1):
        content_preview = doc.page_content[:100].replace('\n', ' ')
        importance = doc.metadata.get('importance', 'normal')
        chunk_type = doc.metadata.get('chunk_type', 'general')

        color = Fore.GREEN if importance == 'critical' else Fore.YELLOW if chunk_type == 'faq' else Fore.WHITE
        print(f"     {color}[{i}] ({chunk_type}/{importance}) {content_preview}...{Style.RESET_ALL}")

print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.GREEN}✅ VECTOR STORE RECREADO EXITOSAMENTE{Style.RESET_ALL}")
print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")

print(f"{Fore.YELLOW}Para usar el nuevo vector store, actualiza tu código:{Style.RESET_ALL}")
print(f'   rag = ConfigurableRAGEngine("data/vectorstore/chroma_db_fixed")')

# 7. ESTADÍSTICAS FINALES
print(f"\n{Fore.CYAN}Estadísticas finales:{Style.RESET_ALL}")
print(f"  Total chunks: {len(all_chunks)}")
print(f"  Chunks críticos: {len(critical_chunks)}")
print(f"  Chunks FAQ: {len(faq_chunks)}")
print(f"  Información crítica indexada: {sum(critical_info.values())}/{len(critical_info)}")

if not all(critical_info.values()):
    print(f"\n{Fore.RED}⚠️ ADVERTENCIA: Falta información crítica en el corpus:{Style.RESET_ALL}")
    for info, found in critical_info.items():
        if not found:
            print(f"  ❌ {info}")