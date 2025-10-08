"""
Script para crear chunks inteligentes que mantienen pares Q&A de FAQs juntos.

Soluciona el problema donde RecursiveCharacterTextSplitter separa preguntas
de sus respuestas, causando retrieval fallido en preguntas como:
- "¿Qué se hace en la actividad de desayunos?"
- "¿Cómo me apunto a desayunos solidarios?"
"""

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import os
import shutil
import re


def detect_faq_category(text: str) -> str:
    """Detecta la categoría del FAQ basándose en palabras clave"""
    text_lower = text.lower()

    if any(kw in text_lower for kw in ['desayuno', 'cena', 'porta de la mar', 'solidario']):
        return 'desayunos'
    elif any(kw in text_lower for kw in ['coles', 'refuerzo escolar', 'ceip', 'niños', 'primaria']):
        return 'coles'
    elif any(kw in text_lower for kw in ['resis', 'residencia', 'acollida', 'abuelitos']):
        return 'resis'
    else:
        return 'general'


def chunk_faq_document(text: str, source: str) -> list[Document]:
    """
    Divide un documento FAQ manteniendo pares pregunta-respuesta juntos.

    Estrategia:
    1. Detectar líneas que son preguntas (empiezan con ¿)
    2. Agrupar cada pregunta con su respuesta (línea siguiente)
    3. Agregar contexto adicional si el chunk es muy pequeño
    """

    chunks = []
    lines = text.split('\n')

    i = 0
    current_section = "general"

    while i < len(lines):
        line = lines[i].strip()

        # Detectar secciones (===== TÍTULO =====)
        if line.startswith('=====') and line.endswith('====='):
            section_name = line.replace('=', '').strip()
            current_section = detect_faq_category(section_name)
            i += 1
            continue

        # Detectar pregunta FAQ
        if line.startswith('¿') or (line and '?' in line and len(line) < 100):
            # Construir chunk con pregunta + respuesta + contexto
            chunk_lines = [line]  # Pregunta

            # Agregar respuesta (líneas siguientes que no son preguntas)
            j = i + 1
            while j < len(lines) and j < i + 10:  # Máximo 10 líneas
                next_line = lines[j].strip()

                # Parar si encontramos otra pregunta o sección
                if next_line.startswith('¿') or next_line.startswith('====='):
                    break

                # Parar si es línea vacía y ya tenemos contenido
                if not next_line and len(chunk_lines) > 2:
                    break

                if next_line:  # Agregar líneas no vacías
                    chunk_lines.append(next_line)

                j += 1

            # Crear chunk solo si tiene contenido sustancial
            chunk_text = '\n'.join(chunk_lines)
            if len(chunk_text) > 30:  # Mínimo 30 caracteres
                # Detectar categoría específica del chunk
                chunk_category = detect_faq_category(chunk_text)
                if chunk_category == 'general':
                    chunk_category = current_section

                chunks.append(Document(
                    page_content=chunk_text,
                    metadata={
                        'source': source,
                        'type': 'faq',
                        'category': chunk_category,
                        'question': line
                    }
                ))

            i = j  # Saltar las líneas procesadas
        else:
            i += 1

    return chunks


def chunk_regular_document(text: str, source: str, chunk_size: int = 300, overlap: int = 100) -> list[Document]:
    """
    Divide documentos no-FAQ usando estrategia de ventana deslizante.
    Para documentos que no tienen formato pregunta-respuesta.
    """
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len
    )

    docs = splitter.create_documents(
        texts=[text],
        metadatas=[{'source': source, 'type': 'document'}]
    )

    return docs


def is_faq_document(text: str) -> bool:
    """Detecta si un documento tiene formato FAQ"""
    # Contar preguntas (líneas que empiezan con ¿)
    question_count = len(re.findall(r'^\¿.+\?', text, re.MULTILINE))

    # Si tiene 3+ preguntas, considerarlo FAQ
    return question_count >= 3


def create_faq_aware_vector_store():
    """Crea vector store con chunking inteligente de FAQs"""

    print("📚 Cargando documentos...")
    loader = DirectoryLoader(
        'data/documents',
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents = loader.load()
    print(f"✓ Cargados {len(documents)} documentos")

    print("\n✂️  Dividiendo con chunking FAQ-aware...")
    all_chunks = []
    faq_count = 0
    regular_count = 0

    for doc in documents:
        source = doc.metadata.get('source', 'unknown')
        filename = os.path.basename(source)

        if is_faq_document(doc.page_content):
            print(f"  → {filename}: FAQ detectado")
            chunks = chunk_faq_document(doc.page_content, source)
            faq_count += len(chunks)
        else:
            print(f"  → {filename}: Documento regular")
            chunks = chunk_regular_document(doc.page_content, source)
            regular_count += len(chunks)

        all_chunks.extend(chunks)

    print(f"✓ Creados {len(all_chunks)} chunks:")
    print(f"  • FAQ chunks: {faq_count}")
    print(f"  • Regular chunks: {regular_count}")

    # Mostrar ejemplos de chunks FAQ
    print("\n📋 Ejemplos de chunks FAQ creados:")
    faq_chunks = [c for c in all_chunks if c.metadata.get('type') == 'faq'][:3]
    for i, chunk in enumerate(faq_chunks, 1):
        preview = chunk.page_content[:100].replace('\n', ' ')
        category = chunk.metadata.get('category', 'unknown')
        print(f"  [{i}] [{category}] {preview}...")

    print("\n🧠 Creando embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'}
    )

    print("💾 Creando vector store con ChromaDB...")

    # Eliminar directorio anterior si existe
    chroma_path = "data/vectorstore/chroma_db"
    if os.path.exists(chroma_path):
        print(f"  → Eliminando vector store anterior...")
        shutil.rmtree(chroma_path)

    # Crear directorio
    os.makedirs(chroma_path, exist_ok=True)

    # Crear vector store
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=chroma_path
    )

    print("✅ Vector store creado y guardado exitosamente!")
    print(f"   Ubicación: {chroma_path}")
    print(f"   Total chunks: {len(all_chunks)}")

    # Estadísticas por categoría
    print("\n📊 Estadísticas por categoría:")
    categories = {}
    for chunk in all_chunks:
        cat = chunk.metadata.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {cat}: {count} chunks")


if __name__ == "__main__":
    create_faq_aware_vector_store()
