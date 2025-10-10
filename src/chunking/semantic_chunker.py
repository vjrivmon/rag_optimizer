#!/usr/bin/env python3
"""
🔪 Semantic Chunker - Chunking inteligente adaptado al tipo de documento

MEJORA #1: Chunking Strategy Optimization
- FAQs: Una Q&A completa = 1 chunk (sin truncar)
- Narrativos: Respeta párrafos con overlapping inteligente
- Estructurados: Mantiene tablas y listas completas

USO:
    from semantic_chunker import SemanticChunker

    chunker = SemanticChunker()
    chunks = chunker.chunk_document(
        doc_text=faq_content,
        doc_type='faq',
        metadata={'source': '01_faq_dni.txt'}
    )
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter


@dataclass
class ChunkConfig:
    """Configuración de chunking por tipo de documento"""
    chunk_size: int
    overlap: int
    separators: List[str]
    preserve_structure: bool = True


class FAQChunker:
    """
    Chunking especializado para documentos FAQ

    Estrategia:
    - Detecta patrones de pregunta-respuesta
    - Cada Q&A es un chunk completo (sin truncar)
    - Mantiene contexto de sección si existe
    """

    def __init__(self):
        # Patrones para detectar preguntas FAQ
        self.question_patterns = [
            r'¿[^?]+\?',  # Pregunta con signos españoles
            r'Pregunta\s*\d*:',  # "Pregunta:" o "Pregunta 1:"
            r'Q\d*:',  # "Q:" o "Q1:"
        ]

        # Patrones para detectar secciones
        self.section_patterns = [
            r'={3,}.*={3,}',  # === SECCIÓN ===
            r'[A-ZÁÉÍÓÚÑ\s]{5,}',  # TEXTO EN MAYÚSCULAS (títulos)
        ]

    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunking de documento FAQ

        Args:
            text: Texto del documento FAQ
            metadata: Metadata base del documento

        Returns:
            Lista de chunks con Q&A completas
        """
        chunks = []

        # Detectar sección actual
        current_section = metadata.get('section', 'General')

        # Split por líneas para procesar
        lines = text.split('\n')

        # Buffers
        current_question = None
        current_answer = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # ¿Es una nueva sección?
            if self._is_section_header(line):
                # Guardar Q&A anterior si existe
                if current_question and current_answer:
                    chunks.append(self._create_chunk(
                        current_question,
                        current_answer,
                        current_section,
                        metadata
                    ))
                    current_question = None
                    current_answer = []

                # Actualizar sección
                current_section = self._clean_section_name(line)
                continue

            # ¿Es una nueva pregunta?
            if self._is_question(line):
                # Guardar Q&A anterior si existe
                if current_question and current_answer:
                    chunks.append(self._create_chunk(
                        current_question,
                        current_answer,
                        current_section,
                        metadata
                    ))

                # Nueva pregunta
                current_question = line
                current_answer = []

            # Es parte de la respuesta
            elif current_question:
                current_answer.append(line)

        # Guardar último Q&A
        if current_question and current_answer:
            chunks.append(self._create_chunk(
                current_question,
                current_answer,
                current_section,
                metadata
            ))

        return chunks

    def _is_section_header(self, line: str) -> bool:
        """Detecta si la línea es un encabezado de sección"""
        for pattern in self.section_patterns:
            if re.match(pattern, line):
                return True
        return False

    def _is_question(self, line: str) -> bool:
        """Detecta si la línea es una pregunta"""
        for pattern in self.question_patterns:
            if re.search(pattern, line):
                return True
        return False

    def _clean_section_name(self, line: str) -> str:
        """Limpia el nombre de la sección"""
        # Remover símbolos de separación
        cleaned = re.sub(r'[=\-_*]+', '', line)
        cleaned = cleaned.strip()
        return cleaned if cleaned else 'General'

    def _create_chunk(
        self,
        question: str,
        answer_lines: List[str],
        section: str,
        base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea un chunk FAQ completo"""

        answer = '\n'.join(answer_lines).strip()

        # Contenido completo: pregunta + respuesta
        content = f"{question}\n{answer}"

        # Metadata enriquecida
        chunk_metadata = {
            **base_metadata,
            'type': 'faq',
            'section': section,
            'question': question,
            'answer': answer,
            'chunk_type': 'faq_qa_pair'
        }

        return {
            'content': content,
            'metadata': chunk_metadata
        }


class NarrativeChunker:
    """
    Chunking para documentos narrativos

    Estrategia:
    - Respeta párrafos y estructura
    - Overlapping inteligente (100-150 chars)
    - Prioriza separadores semánticos (\n\n > \n > . > espacio)
    """

    def __init__(
        self,
        chunk_size: int = 600,  # Aumentado de 500 a 600 (más contexto)
        overlap: int = 120  # Aumentado de 100 a 120 (mejor continuidad)
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunking de documento narrativo
        """

        # RecursiveCharacterTextSplitter con separadores semánticos
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=[
                "\n\n",  # Párrafos (prioridad alta)
                "\n",    # Líneas
                ". ",    # Frases
                ", ",    # Cláusulas
                " ",     # Palabras
                ""       # Caracteres (último recurso)
            ],
            length_function=len,
            is_separator_regex=False
        )

        # Crear chunks
        langchain_chunks = splitter.create_documents(
            [text],
            metadatas=[{**metadata, 'chunk_type': 'narrative'}]
        )

        # Convertir a formato estándar
        chunks = []
        for i, chunk in enumerate(langchain_chunks):
            chunks.append({
                'content': chunk.page_content,
                'metadata': {
                    **chunk.metadata,
                    'chunk_id': f"{metadata.get('source', 'doc')}_narrative_{i+1}",
                    'position': i + 1,
                    'total_chunks': len(langchain_chunks)
                }
            })

        return chunks


class StructuredChunker:
    """
    Chunking para documentos estructurados (tablas, listas)

    Estrategia:
    - Detecta tablas y las mantiene intactas
    - Preserva listas completas
    - Split por secciones lógicas
    """

    def __init__(self, max_chunk_size: int = 800):
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunking de documento estructurado
        """
        chunks = []

        # Detectar tablas (líneas con | o múltiples columnas)
        table_pattern = r'^\|.*\|$'

        # Split por secciones
        sections = re.split(r'\n\s*\n', text)

        current_section = []
        section_type = 'text'

        for section in sections:
            lines = section.strip().split('\n')

            # Detectar si es una tabla
            is_table = any(re.match(table_pattern, line.strip()) for line in lines)

            # Si cambia el tipo de sección, guardar la anterior
            if current_section and ((is_table and section_type != 'table') or
                                  (not is_table and section_type == 'table')):

                chunk_content = '\n\n'.join(current_section)
                if len(chunk_content) <= self.max_chunk_size:
                    chunks.append(self._create_structured_chunk(
                        chunk_content,
                        section_type,
                        metadata,
                        len(chunks) + 1
                    ))
                else:
                    # Si es muy grande, subdividir
                    sub_chunks = self._subdivide_large_content(
                        chunk_content,
                        section_type,
                        metadata
                    )
                    chunks.extend(sub_chunks)

                current_section = []

            current_section.append(section.strip())
            section_type = 'table' if is_table else 'text'

        # Guardar última sección
        if current_section:
            chunk_content = '\n\n'.join(current_section)
            if len(chunk_content) <= self.max_chunk_size:
                chunks.append(self._create_structured_chunk(
                    chunk_content,
                    section_type,
                    metadata,
                    len(chunks) + 1
                ))
            else:
                sub_chunks = self._subdivide_large_content(
                    chunk_content,
                    section_type,
                    metadata
                )
                chunks.extend(sub_chunks)

        return chunks

    def _create_structured_chunk(
        self,
        content: str,
        section_type: str,
        base_metadata: Dict[str, Any],
        chunk_id: int
    ) -> Dict[str, Any]:
        """Crea un chunk estructurado"""

        chunk_metadata = {
            **base_metadata,
            'type': 'structured',
            'section_type': section_type,
            'chunk_type': f'structured_{section_type}',
            'chunk_id': f"{base_metadata.get('source', 'doc')}_structured_{chunk_id}"
        }

        return {
            'content': content,
            'metadata': chunk_metadata
        }

    def _subdivide_large_content(
        self,
        content: str,
        section_type: str,
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Subdivide contenido muy grande"""

        # Para tablas: dividir por filas manteniendo encabezado
        if section_type == 'table':
            return self._subdivide_table(content, base_metadata)

        # Para texto: usar RecursiveCharacterTextSplitter
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.max_chunk_size - 100,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". "]
            )

            langchain_chunks = splitter.create_documents([content])

            chunks = []
            for i, chunk in enumerate(langchain_chunks):
                chunks.append(self._create_structured_chunk(
                    chunk.page_content,
                    section_type,
                    base_metadata,
                    i + 1
                ))

            return chunks

    def _subdivide_table(self, table_content: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Divide tabla grande manteniendo encabezado"""
        lines = table_content.strip().split('\n')

        if len(lines) < 3:  # Encabezado + separador + al menos 1 fila
            return [self._create_structured_chunk(table_content, 'table', base_metadata, 1)]

        header = lines[0]
        separator = lines[1] if len(lines) > 1 else ''
        rows = lines[2:] if len(lines) > 2 else []

        chunks = []
        current_rows = []
        current_size = len(header) + len(separator) + 10  # Buffer

        for row in rows:
            row_size = len(row)

            # Si agregar esta fila excede el límite y ya hay filas, guardar chunk
            if current_size + row_size > self.max_chunk_size and current_rows:
                chunk_content = f"{header}\n{separator}\n" + '\n'.join(current_rows)
                chunks.append(self._create_structured_chunk(
                    chunk_content, 'table', base_metadata, len(chunks) + 1
                ))

                # Reset para siguiente chunk
                current_rows = [row]  # Incluir fila actual
                current_size = len(header) + len(separator) + row_size + 10
            else:
                current_rows.append(row)
                current_size += row_size

        # Guardar último chunk
        if current_rows:
            chunk_content = f"{header}\n{separator}\n" + '\n'.join(current_rows)
            chunks.append(self._create_structured_chunk(
                chunk_content, 'table', base_metadata, len(chunks) + 1
            ))

        return chunks


class SemanticChunker:
    """
    Chunker principal que selecciona la estrategia adecuada según el tipo de documento
    """

    def __init__(self):
        self.faq_chunker = FAQChunker()
        self.narrative_chunker = NarrativeChunker()
        self.structured_chunker = StructuredChunker()

        # Configuraciones por tipo
        self.type_configs = {
            'faq': ChunkConfig(
                chunk_size=0,  # No limita FAQ chunks
                overlap=0,
                separators=[],
                preserve_structure=True
            ),
            'narrative': ChunkConfig(
                chunk_size=600,
                overlap=120,
                separators=["\n\n", "\n", ". ", ", "],
                preserve_structure=True
            ),
            'structured': ChunkConfig(
                chunk_size=800,
                overlap=50,
                separators=["\n\n", "\n"],
                preserve_structure=True
            )
        }

    def chunk_document(
        self,
        doc_text: str,
        doc_type: str = 'narrative',
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunking principal según tipo de documento

        Args:
            doc_text: Texto completo del documento
            doc_type: Tipo ('faq', 'narrative', 'structured', 'auto')
            metadata: Metadata base del documento

        Returns:
            Lista de chunks con metadata enriquecida
        """
        if metadata is None:
            metadata = {}

        # Auto-detectar tipo si es 'auto'
        if doc_type == 'auto':
            doc_type = self._detect_document_type(doc_text)

        # Seleccionar chunker apropiado
        if doc_type == 'faq':
            chunks = self.faq_chunker.chunk(doc_text, metadata)
        elif doc_type == 'structured':
            chunks = self.structured_chunker.chunk(doc_text, metadata)
        else:  # narrative por defecto
            chunks = self.narrative_chunker.chunk(doc_text, metadata)

        # Enriquecer metadata global
        for i, chunk in enumerate(chunks):
            chunk['metadata'].update({
                'document_type': doc_type,
                'total_chunks': len(chunks),
                'chunk_index': i,
                'chunking_strategy': f'{doc_type}_chunker'
            })

        return chunks

    def _detect_document_type(self, text: str) -> str:
        """
        Detecta automáticamente el tipo de documento

        Returns:
            'faq', 'structured' o 'narrative'
        """
        text_lower = text.lower()

        # Detectar FAQ
        faq_indicators = ['¿', '?', 'pregunta', 'respuesta', 'q:', 'a:']
        faq_score = sum(1 for indicator in faq_indicators if indicator in text_lower)

        # Detectar estructurado (tablas)
        table_indicators = ['|', '-', 'columna', 'fila']
        table_score = sum(1 for indicator in table_indicators if text_lower.count(indicator) > 2)

        # Detectar listas
        list_indicators = ['1.', '2.', '•', '-', '*']
        list_score = sum(1 for indicator in list_indicators if text_lower.count(indicator) > 3)

        # Decidir basado en scores
        if faq_score >= 3:
            return 'faq'
        elif table_score >= 2 or list_score >= 3:
            return 'structured'
        else:
            return 'narrative'

    def get_chunking_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera estadísticas del chunking realizado
        """
        if not chunks:
            return {}

        # Estadísticas básicas
        total_chunks = len(chunks)
        chunk_lengths = [len(chunk['content']) for chunk in chunks]

        # Estadísticas por tipo
        types = {}
        for chunk in chunks:
            chunk_type = chunk['metadata'].get('document_type', 'unknown')
            if chunk_type not in types:
                types[chunk_type] = 0
            types[chunk_type] += 1

        # Metadata única
        unique_sources = set(chunk['metadata'].get('source', 'unknown') for chunk in chunks)

        return {
            'total_chunks': total_chunks,
            'avg_chunk_length': sum(chunk_lengths) / len(chunk_lengths),
            'min_chunk_length': min(chunk_lengths),
            'max_chunk_length': max(chunk_lengths),
            'total_characters': sum(chunk_lengths),
            'chunk_types': types,
            'unique_sources': len(unique_sources),
            'has_faq_chunks': any(chunk['metadata'].get('type') == 'faq' for chunk in chunks),
            'has_narrative_chunks': any(chunk['metadata'].get('type') == 'narrative' for chunk in chunks),
            'has_structured_chunks': any(chunk['metadata'].get('type') == 'structured' for chunk in chunks)
        }


# Función de conveniencia para uso rápido
def chunk_document_smart(
    text: str,
    doc_type: str = 'auto',
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Función de conveniencia para chunking inteligente

    Args:
        text: Texto del documento
        doc_type: Tipo de documento ('auto', 'faq', 'narrative', 'structured')
        metadata: Metadata adicional

    Returns:
        Lista de chunks procesados
    """
    chunker = SemanticChunker()
    return chunker.chunk_document(text, doc_type, metadata or {})


if __name__ == "__main__":
    # Ejemplo de uso
    sample_faq = """
    === DESAYUNOS ===

    ¿Dónde se realizan los desayunos?
    Los desayunos se realizan en la Porta de la Mar de Valencia.

    ¿A qué hora son?
    Los desayunos son los sábados a las 8 de la mañana.

    ¿Cómo me apunto?
    Para apuntarte, rellena el formulario que se publica los miércoles.
    """

    chunker = SemanticChunker()
    chunks = chunker.chunk_document(
        sample_faq,
        doc_type='faq',
        metadata={'source': 'faq_sample.txt'}
    )

    print(f"📊 Generados {len(chunks)} chunks FAQ:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Tipo: {chunk['metadata']['type']}")
        print(f"Sección: {chunk['metadata']['section']}")
        print(f"Longitud: {len(chunk['content'])} caracteres")
        print(f"Contenido: {chunk['content'][:100]}...")