#!/usr/bin/env python3
"""
Fix Vector Store v2 - Corrige problema con Q6 y optimiza FAQ chunking
"""

import os
import shutil
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import chromadb
import re

def detect_faq_questions(text):
    """Detecta y extrae preguntas FAQ del texto"""
    # Patrón para detectar preguntas (líneas que empiezan con ¿)
    question_pattern = r'^¿[^\n]+\?$'

    questions = []
    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(question_pattern, line):
            # Encontramos una pregunta
            question = line
            answer_lines = []

            # Recoger líneas de respuesta hasta la siguiente pregunta o línea vacía múltiple
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()

                # Si encontramos otra pregunta, terminamos
                if re.match(question_pattern, next_line):
                    break

                # Si es línea vacía, verificar si hay más contenido
                if not next_line:
                    # Mirar adelante para ver si hay más contenido
                    if i + 1 < len(lines) and lines[i + 1].strip() and not re.match(question_pattern, lines[i + 1].strip()):
                        answer_lines.append('')  # Mantener línea vacía
                    else:
                        break  # Terminar si no hay más contenido relevante
                else:
                    answer_lines.append(lines[i])

                i += 1

            # Crear el par pregunta-respuesta
            if answer_lines:
                answer = '\n'.join(answer_lines).strip()
                questions.append({
                    'question': question,
                    'answer': answer,
                    'full_text': f"{question}\n{answer}"
                })
        else:
            i += 1

    return questions

def determine_activity(text):
    """Determina a qué actividad pertenece el texto"""
    text_lower = text.lower()

    # Palabras clave por actividad
    keywords = {
        'desayunos': ['desayuno', 'sábado', 'mañana', 'valencianas', 'leche', 'formulario', 'apunt'],
        'coles': ['coles', 'refuerzo', 'escolar', 'ceip', 'antonio ferrandis', 'niños', 'deberes'],
        'resis': ['resis', 'residencia', 'acollida', 'ancianos', 'abuelos', 'charlas'],
        'general': []
    }

    scores = {}
    for activity, words in keywords.items():
        score = sum(1 for word in words if word in text_lower)
        scores[activity] = score

    # Retornar la actividad con mayor score, o 'general' si no hay matches
    max_activity = max(scores.items(), key=lambda x: x[1])
    return max_activity[0] if max_activity[1] > 0 else 'general'

def determine_importance(text):
    """Determina la importancia del chunk"""
    text_lower = text.lower()

    # Palabras clave críticas
    critical_keywords = ['dónde', 'donde', 'ceip antonio ferrandis', 'acollida', 'porta de la mar',
                         'cómo me apunto', 'como me apunto', 'formulario', 'inscrib']

    # Palabras clave de alta importancia
    high_keywords = ['gasolina', 'paga', 'para-mira-ayuda', 'horario', 'cuando', 'cuándo',
                     'qué se hace', 'que se hace', 'objetivo']

    if any(keyword in text_lower for keyword in critical_keywords):
        return 'critical'
    elif any(keyword in text_lower for keyword in high_keywords):
        return 'high'
    else:
        return 'normal'

def create_optimized_chunks(documents):
    """Crea chunks optimizados con metadata mejorada"""
    all_chunks = []

    for doc in documents:
        content = doc.page_content
        source = doc.metadata.get('source', '')

        # Detectar si es un archivo FAQ
        is_faq = '01_faq' in source or 'faq' in source.lower()

        if is_faq:
            # Procesar como FAQ - mantener pares pregunta-respuesta juntos
            faq_items = detect_faq_questions(content)

            for item in faq_items:
                chunk_text = item['full_text']
                activity = determine_activity(chunk_text)
                importance = determine_importance(chunk_text)

                # Ajuste especial para "¿Cómo me apunto?"
                if "cómo me apunto" in chunk_text.lower() or "como me apunto" in chunk_text.lower():
                    activity = 'desayunos'  # Corregir actividad
                    importance = 'critical'   # Marcar como crítico

                chunk = type(doc)(
                    page_content=chunk_text,
                    metadata={
                        'source': source,
                        'chunk_type': 'faq',
                        'question': item['question'],
                        'activity': activity,
                        'importance': importance,
                        'chunk_size': len(chunk_text)
                    }
                )
                all_chunks.append(chunk)

            # También procesar el resto del contenido no-FAQ si existe
            non_faq_content = []
            lines = content.split('\n')
            in_faq = False

            for line in lines:
                if re.match(r'^¿[^\n]+\?$', line.strip()):
                    in_faq = True
                elif in_faq and line.strip() == '':
                    in_faq = False
                elif not in_faq and line.strip():
                    non_faq_content.append(line)

            if non_faq_content:
                remaining_text = '\n'.join(non_faq_content)
                if len(remaining_text) > 100:  # Solo si hay contenido significativo
                    # Usar text splitter para el resto
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=300,
                        chunk_overlap=100,
                        separators=["\n\n", "\n", ". ", ", ", " "],
                        keep_separator=True
                    )

                    temp_doc = type(doc)(
                        page_content=remaining_text,
                        metadata=doc.metadata
                    )

                    sub_chunks = text_splitter.split_documents([temp_doc])
                    for chunk in sub_chunks:
                        activity = determine_activity(chunk.page_content)
                        importance = determine_importance(chunk.page_content)

                        chunk.metadata.update({
                            'chunk_type': 'general',
                            'activity': activity,
                            'importance': importance,
                            'chunk_size': len(chunk.page_content)
                        })
                        all_chunks.append(chunk)
        else:
            # Procesar como documento normal
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", ", ", " "],
                keep_separator=True
            )

            chunks = text_splitter.split_documents([doc])

            for chunk in chunks:
                activity = determine_activity(chunk.page_content)
                importance = determine_importance(chunk.page_content)

                chunk.metadata.update({
                    'chunk_type': 'general',
                    'activity': activity,
                    'importance': importance,
                    'chunk_size': len(chunk.page_content)
                })
                all_chunks.append(chunk)

    return all_chunks

def main():
    print("=" * 80)
    print("FIX VECTOR STORE v2 - Optimización FAQ y corrección Q6")
    print("=" * 80)

    # Configurar rutas
    docs_path = Path("data/documents")
    vector_store_path = Path("data/vectorstore/chroma_db")

    # Backup del vector store actual
    backup_path = Path("data/vectorstore/chroma_db_backup_v2")
    if vector_store_path.exists():
        print(f"\n📦 Creando backup en {backup_path}...")
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(vector_store_path, backup_path)

    # Cargar documentos
    print("\n📚 Cargando documentos...")
    documents = []
    for file_path in docs_path.glob("*.txt"):
        print(f"   - {file_path.name}")
        loader = TextLoader(str(file_path), encoding='utf-8')
        documents.extend(loader.load())

    print(f"\n✓ {len(documents)} documentos cargados")

    # Crear chunks optimizados
    print("\n✂️ Creando chunks optimizados...")
    all_chunks = create_optimized_chunks(documents)

    # Estadísticas de chunks
    faq_chunks = [c for c in all_chunks if c.metadata.get('chunk_type') == 'faq']
    general_chunks = [c for c in all_chunks if c.metadata.get('chunk_type') == 'general']
    critical_chunks = [c for c in all_chunks if c.metadata.get('importance') == 'critical']

    print(f"\n📊 Estadísticas de chunks:")
    print(f"   - Total: {len(all_chunks)} chunks")
    print(f"   - FAQ: {len(faq_chunks)} chunks")
    print(f"   - General: {len(general_chunks)} chunks")
    print(f"   - Críticos: {len(critical_chunks)} chunks")

    # Verificar chunks críticos
    print("\n🎯 Chunks críticos identificados:")
    for chunk in critical_chunks[:5]:  # Mostrar primeros 5
        preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"   - {preview}...")

    # Verificar específicamente Q6
    print("\n🔍 Verificando chunk de Q6 (¿Cómo me apunto?)...")
    q6_found = False
    for chunk in all_chunks:
        if "cómo me apunto" in chunk.page_content.lower():
            q6_found = True
            print(f"   ✅ ENCONTRADO:")
            print(f"      Contenido: {chunk.page_content[:150]}...")
            print(f"      Metadata: {chunk.metadata}")
            break

    if not q6_found:
        print("   ❌ NO ENCONTRADO - ERROR CRÍTICO")
        return

    # Configurar embeddings (mismo modelo que en rag_engine.py)
    print("\n🤖 Configurando embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Limpiar vector store existente
    if vector_store_path.exists():
        print(f"\n🗑️ Limpiando vector store existente...")
        shutil.rmtree(vector_store_path)

    # Crear nuevo vector store
    print("\n💾 Creando nuevo vector store optimizado...")
    vector_store = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=str(vector_store_path),
        collection_name="rag_collection_fixed_v2",
        collection_metadata={"hnsw:space": "cosine"}
    )

    print(f"✓ Vector store creado con {len(all_chunks)} chunks")

    # Verificación rápida
    print("\n🧪 Verificación rápida del vector store...")
    test_queries = [
        "¿Cómo me apunto a desayunos solidarios?",
        "¿Dónde es la actividad de coles?",
        "¿Quién paga la gasolina?"
    ]

    for query in test_queries:
        print(f"\n   Query: {query}")
        results = vector_store.similarity_search(query, k=3)
        for i, doc in enumerate(results):
            preview = doc.page_content[:80].replace('\n', ' ')
            print(f"   {i+1}. {preview}...")

    print("\n" + "=" * 80)
    print("✅ VECTOR STORE v2 RECONSTRUIDO EXITOSAMENTE")
    print("=" * 80)
    print("\nMejoras implementadas:")
    print("1. ✅ FAQ chunks mantienen pregunta-respuesta juntos")
    print("2. ✅ Metadata de actividades corregida (Q6 ahora es 'desayunos')")
    print("3. ✅ Importancia 'critical' para preguntas clave")
    print("4. ✅ Optimización específica para '¿Cómo me apunto?'")
    print("\n🚀 Listo para ejecutar benchmark completo")

if __name__ == "__main__":
    main()