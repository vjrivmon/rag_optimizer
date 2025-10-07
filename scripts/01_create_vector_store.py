# Importaciones actualizadas
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # Actualizado
from langchain_community.vectorstores import FAISS
import os

def create_vector_store():
    """Crea un vector store desde documentos de texto"""
    
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
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✓ Creados {len(chunks)} chunks")
    
    print("🧠 Creando embeddings...")
    # Modelo corregido - sin "ing" en paraphrase
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cuda'}  # o 'cpu' si no tienes GPU
    )
    
    print("💾 Creando vector store...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Crear directorio si no existe
    os.makedirs('data/vectorstore', exist_ok=True)
    
    # Guardar
    vectorstore.save_local("data/vectorstore/faiss_index")
    print("✅ Vector store creado y guardado exitosamente!")

if __name__ == "__main__":
    create_vector_store()