from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os
import shutil

def create_vector_store():
    """Crea un vector store desde documentos de texto usando ChromaDB"""

    print("📚 Cargando documentos...")
    loader = DirectoryLoader(
        'data/documents',
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents = loader.load()
    print(f"✓ Cargados {len(documents)} documentos")

    print("✂️  Dividiendo en chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✓ Creados {len(chunks)} chunks")

    print("🧠 Creando embeddings...")
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

    print("✅ Vector store creado y guardado exitosamente!")
    print(f"   Ubicación: {chroma_path}")

if __name__ == "__main__":
    create_vector_store()
