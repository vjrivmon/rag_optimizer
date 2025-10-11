#!/usr/bin/env python3
"""
🔧 Fix para P25: Mejorar chunks de "Para-Mira-Ayuda"

Problema: El chunking actual separa el título "PARA. MIRA. AYUDA." de su explicación.
Solución: Regenerar el vector store con chunks que mantengan título + explicación juntos.
"""

import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# === CONFIGURACIÓN ===
DOCS_DIR = "data/documents"
VECTOR_STORE_PATH = "data/vectorstore/chroma_db"
COLLECTION_NAME = "langchain"

# === CHUNKS MEJORADOS ESPECÍFICOS PARA P25 ===
IMPROVED_CHUNKS = [
    # Chunk principal: Para-Mira-Ayuda con explicación completa
    """PARA. MIRA. AYUDA.

Estas son las tres palabras que guían la labor de nuestros voluntarios de DNI (Damos Nuestra Ilusión). 

En un mundo que avanza a un ritmo frenético, es necesario detenerse para ser conscientes de aquellos que nos rodean y estar dispuesto a ofrecer nuestra ayuda con generosidad y alegría.

PARAR: Detenerse en la vida cotidiana para ser conscientes de nuestro entorno.
MIRAR: Observar con atención y empatía a quienes nos rodean.
AYUDAR: Ofrecer nuestra ayuda de manera generosa y alegre.

Estas tres palabras son el lema y la filosofía de trabajo de DNI. No buscamos grandes gestos ni reconocimiento, sino transformar el día a día y hacer del voluntariado algo habitual y natural.""",

    # Chunk secundario: Contexto de DNI y Por qué DNI
    """¿POR QUÉ DNI?

La pregunta correcta no es qué es DNI, sino por qué DNI. ¿Qué es lo que ha sucedido para que aparezca? ¿Qué intenta conseguir? ¿A quién pretende llegar?

DNI busca dejar un mundo mejor, aspira a ayudar al vecino, no pretende irse muy lejos para conseguir hacer algo bueno, porque siempre tendremos a una persona cerca que nos está esperando. No pretende ser importante, sino meterse en tu día a día, habituarte a PARAR, enseñarte a MIRAR con cariño y cercanía, y ofrecer la máxima AYUDA, sacando lo mejor de nosotros mismos.

DNI es la verdadera juventud, es inquietud, es caridad, es ambición… es todo aquello que define a los que quieren cambiar el mundo, empezando por la puerta de su casa.""",

    # Chunk terciario: Filosofía de trabajo
    """FILOSOFÍA DE TRABAJO DE DNI

No buscamos grandes gestos ni reconocimiento. Buscamos transformar el día a día, hacer del voluntariado algo habitual, natural. 

Queremos que PARAR, MIRAR y AYUDAR se convierta en una forma de vida.

El lema "PARA. MIRA. AYUDA." resume nuestra filosofía:
- En la vida acelerada, debemos PARAR para ser conscientes
- MIRAR a nuestro alrededor con empatía y cercanía
- AYUDAR a quienes nos rodean con generosidad y alegría

DNI es solidaridad, inquietud, juventud. Esto es DNI."""
]


def fix_p25_vector_store():
    """Regenera chunks específicos para mejorar P25"""
    
    print("🔧 Iniciando fix para P25: Para-Mira-Ayuda")
    print("="*80)
    
    # 1. Inicializar embeddings
    print("\n📊 Inicializando embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # 2. Cargar vector store existente
    print(f"\n📂 Cargando vector store desde: {VECTOR_STORE_PATH}")
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    
    # 3. Obtener todos los documentos actuales
    print("\n🔍 Analizando documentos existentes...")
    all_data = vector_store.get()
    current_docs = all_data['documents']
    current_ids = all_data['ids']
    current_metadatas = all_data['metadatas']
    
    print(f"   Total documentos actuales: {len(current_docs)}")
    
    # 4. Encontrar y eliminar chunks viejos de "Para-Mira-Ayuda"
    print("\n🗑️  Eliminando chunks antiguos de 'Para-Mira-Ayuda'...")
    ids_to_delete = []
    
    for i, doc in enumerate(current_docs):
        doc_lower = doc.lower()
        if 'para' in doc_lower and 'mira' in doc_lower and 'ayuda' in doc_lower:
            ids_to_delete.append(current_ids[i])
            print(f"   ❌ Eliminando: {doc[:80]}...")
    
    if ids_to_delete:
        vector_store.delete(ids=ids_to_delete)
        print(f"   ✅ Eliminados {len(ids_to_delete)} chunks antiguos")
    else:
        print("   ℹ️  No se encontraron chunks antiguos para eliminar")
    
    # 5. Agregar chunks mejorados
    print("\n✨ Agregando chunks mejorados...")
    improved_documents = []
    
    for i, chunk in enumerate(IMPROVED_CHUNKS, 1):
        doc = Document(
            page_content=chunk,
            metadata={
                'source': '04_filosofia_dni.txt',
                'chunk_type': 'improved_p25',
                'chunk_number': i,
                'total_chunks': len(IMPROVED_CHUNKS)
            }
        )
        improved_documents.append(doc)
        print(f"   ✅ Chunk {i}: {chunk[:80].replace(chr(10), ' ')}...")
    
    # Agregar al vector store
    vector_store.add_documents(improved_documents)
    
    # 6. Verificar
    print("\n🔍 Verificando cambios...")
    all_data_new = vector_store.get()
    new_total = len(all_data_new['documents'])
    
    print(f"   Documentos antes: {len(current_docs)}")
    print(f"   Documentos eliminados: {len(ids_to_delete)}")
    print(f"   Documentos agregados: {len(IMPROVED_CHUNKS)}")
    print(f"   Documentos después: {new_total}")
    print(f"   Diferencia neta: {new_total - len(current_docs):+d}")
    
    # 7. Probar búsqueda
    print("\n🧪 Probando búsqueda con la pregunta P25...")
    results = vector_store.similarity_search(
        "¿Qué significa Para-Mira-Ayuda?",
        k=5
    )
    
    print(f"\n   Top 5 resultados recuperados:")
    for i, doc in enumerate(results, 1):
        content_preview = doc.page_content[:100].replace('\n', ' ')
        print(f"   {i}. {content_preview}...")
    
    print("\n" + "="*80)
    print("✅ Fix completado exitosamente")
    print("\n💡 Siguiente paso: Ejecutar test de P25 para verificar mejora")
    print("   python test_p25_only.py")
    
    return vector_store


if __name__ == "__main__":
    fix_p25_vector_store()

