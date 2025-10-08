#!/usr/bin/env python3
"""
Script mejorado para crear vector store con chunking inteligente
- Detecta conceptos clave y los mantiene juntos
- Metadata enriquecida para mejor retrieval
"""

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
import os
import shutil
import re


def detect_key_concept(text):
    """
    Detecta si el texto contiene un concepto clave que debe mantenerse junto
    """
    key_patterns = [
        r'PARA\.\s*MIRA\.\s*AYUDA',
        r'¿Qué significa Para-Mira-Ayuda\?',
        r'palabras que guían',
    ]

    for pattern in key_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 'para_mira_ayuda'

    return None


def create_improved_chunks(documents):
    """
    Crea chunks con lógica mejorada para conceptos clave
    """

    all_chunks = []

    for doc in documents:
        content = doc.page_content
        source = doc.metadata.get('source', '')

        # Determinar categoría del documento
        if 'faq' in source.lower() or 'desayunos' in source.lower():
            category = 'desayunos'
        elif 'charlas' in source.lower() or 'abuelitos' in source.lower() or 'resis' in source.lower():
            category = 'resis'
        elif 'filosofia' in source.lower() or 'quienes' in source.lower():
            category = 'filosofia'
        elif 'coles' in source.lower() or 'refuerzo' in source.lower():
            category = 'coles'
        else:
            category = 'general'

        # Dividir por párrafos primero
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        for para in paragraphs:
            # Detectar concepto clave
            key_concept = detect_key_concept(para)

            if key_concept == 'para_mira_ayuda':
                # Este es el concepto clave - mantenerlo completo
                # Buscar contexto adicional (siguiente párrafo)
                para_index = paragraphs.index(para)

                # Incluir el título y el párrafo explicativo completo
                full_concept = para

                # Si hay un siguiente párrafo que explica más, añadirlo
                if para_index + 1 < len(paragraphs):
                    next_para = paragraphs[para_index + 1]
                    # Si el siguiente párrafo es corto y relacionado, incluirlo
                    if len(next_para) < 500 and any(keyword in next_para.lower()
                                                     for keyword in ['parar', 'mirar', 'ayuda', 'guían']):
                        full_concept += '\n\n' + next_para

                # Crear chunk especial
                chunk = Document(
                    page_content=full_concept,
                    metadata={
                        'source': source,
                        'category': category,
                        'concept': 'para_mira_ayuda',
                        'priority': 'high'
                    }
                )
                all_chunks.append(chunk)
                continue

            # Para párrafos normales, usar chunking estándar
            if len(para) > 400:
                # Dividir párrafos largos
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=300,
                    chunk_overlap=100,
                    length_function=len,
                    separators=['\n', '. ', ', ', ' ']
                )
                sub_chunks = text_splitter.create_documents(
                    [para],
                    metadatas=[{'source': source, 'category': category}]
                )
                all_chunks.extend(sub_chunks)
            else:
                # Mantener párrafos cortos completos
                chunk = Document(
                    page_content=para,
                    metadata={
                        'source': source,
                        'category': category
                    }
                )
                all_chunks.append(chunk)

    return all_chunks


def create_vector_store_improved():
    """Crea un vector store mejorado con chunking inteligente"""

    print("📚 Cargando documentos...")
    loader = DirectoryLoader(
        'data/documents',
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents = loader.load()
    print(f"✓ Cargados {len(documents)} documentos")

    print("✂️  Dividiendo en chunks con lógica mejorada...")
    chunks = create_improved_chunks(documents)
    print(f"✓ Creados {len(chunks)} chunks")

    # Verificar que tenemos el chunk de Para-Mira-Ayuda
    para_mira_chunks = [c for c in chunks if c.metadata.get('concept') == 'para_mira_ayuda']
    if para_mira_chunks:
        print(f"   ✅ Chunk especial 'Para-Mira-Ayuda' creado ({len(para_mira_chunks[0].page_content)} chars)")
        print(f"      Preview: {para_mira_chunks[0].page_content[:150]}...")
    else:
        print("   ⚠️  WARNING: No se detectó el chunk de Para-Mira-Ayuda")

    print("🧠 Creando embeddings (mpnet-base-v2 768d)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'}
    )

    print("💾 Creando vector store con ChromaDB...")

    # Eliminar directorio anterior si existe
    chroma_path = "data/vectorstore/chroma_db"
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

    # Crear directorio
    os.makedirs(chroma_path, exist_ok=True)

    # Crear vector store
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=chroma_path
    )

    print("✅ Vector store mejorado creado y guardado exitosamente!")
    print(f"   Ubicación: {chroma_path}")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Chunks con metadata 'category':")
    categories = {}
    for chunk in chunks:
        cat = chunk.metadata.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"      - {cat}: {count} chunks")


if __name__ == "__main__":
    create_vector_store_improved()
