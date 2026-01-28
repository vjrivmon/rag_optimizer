# Skill: TFG Cap 2 - Marco Teorico

## Descripcion

Skill especializado para documentar el Capitulo 2 (Marco Teorico) del TFG
"Desarrollo de un Chatbot Conversacional con RAG para DNI Valencia". Genera
secciones con formato profesional, citaciones numericas y conexion con el
proyecto.

## Activacion

- Comando: `/tfg-cap2 <seccion>`
- Triggers: "escribe seccion", "documenta capitulo", "marco teorico"

## Archivo Destino

`docs/tfg/capitulos/02-marco-teorico.tex`

## Estado Actual

### Secciones Completadas

- [x] 2.1 Sistemas de Recuperacion de Informacion (completo en LaTeX)
- [x] 2.2 Retrieval-Augmented Generation (completo en LaTeX)
- [x] 2.3 Modelos de Lenguaje de Gran Escala (completo en LaTeX)
- [x] 2.4 Gestion de Contexto Multi-turn (completo en LaTeX)
- [x] 2.5 Evaluacion de Sistemas RAG (completo en LaTeX)
- [x] 2.6 Bases de Datos Vectoriales (completo en LaTeX)
- [x] 2.7 Trabajos Relacionados (completo en LaTeX)

### Pendiente

- [ ] Figuras reales (actualmente hay TODOs para reemplazar)
- [ ] Revision de citas (verificar que todas las \cite{} coincidan con
      bibliography.bib)
- [ ] Revision de acentos LaTeX

## Contexto del Proyecto

```yaml
titulo: "Desarrollo de un Chatbot Conversacional con RAG para DNI Valencia"
autor: Vicente Rivas Monferrer
universidad: UPV - Grado en Tecnologias Interactivas / IA
curso: 2025-2026
```

### Componentes Tecnicos a Documentar

1. **Arquitectura RAG** - Pipeline completo de Retrieval-Augmented Generation
2. **Context Tracker** - Ventana deslizante de 4 turnos para memoria
   conversacional
3. **Sistema Ensemble** - 4 estrategias (Voting, Weighted, Routing, Consensus)
   con 4 LLMs
4. **Framework RAGAs** - Evaluacion automatizada con metricas cientificas
5. **ChromaDB** - Base de datos vectorial para embeddings
6. **Busqueda Hibrida** - BM25 + Semantic search combinados
7. **LangChain** - Framework de orquestacion de LLMs

### Modelos LLM Utilizados

- gemma2:27b (Google)
- llama3.3:70b (Meta)
- qwen3:32b (Alibaba)
- deepseek-r1 (DeepSeek)

---

## Patron de Escritura Academica

Cada seccion sigue este patron (basado en TFGs de Joan y Rosa):

### 1. Contexto Introductorio (1-2 parrafos)

- Por que es relevante este tema
- Problema que aborda
- Conexion inicial con el proyecto

### 2. Definicion Clara (1 parrafo)

```latex
Segun [Autor]~\cite{key}, [concepto] se define como ``[definicion textual]''.
Este termino fue acunado en [ano] y ha evolucionado para abarcar [ampliacion].
```

### 3. Ampliacion Conceptual (2-3 parrafos)

- Subtipos o variantes del concepto
- Teorias relacionadas
- Evolucion historica si aplica
- Comparativa con alternativas

### 4. Ejemplos Practicos (1-2 parrafos)

- Casos reales de uso
- Implementaciones conocidas
- Datos o estadisticas de impacto

### 5. Conexion con el Proyecto (1 parrafo)

```latex
En el contexto del Chatbot RAG para DNI Valencia, esta tecnica permite
[aplicacion especifica], lo cual justifica su seleccion frente a alternativas
como [otras opciones].
```

---

## Formato LaTeX

### Citas

```latex
Segun Lewis et al.~\cite{lewis2020rag}, la arquitectura RAG...
Estudios recientes~\cite{gao2023retrieval,es2023ragas} demuestran que...
```

### Figuras

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{nombre-figura.png}
    \caption{Titulo descriptivo.}
    \label{fig:nombre}
\end{figure}
```

### Tablas

```latex
\begin{table}[H]
\centering
\caption{Titulo descriptivo.}
\label{tab:nombre}
\begin{tabular}{@{}lll@{}}
\toprule
\textbf{Col1} & \textbf{Col2} & \textbf{Col3} \\
\midrule
Dato & Dato & Dato \\
\bottomrule
\end{tabular}
\end{table}
```

### Ecuaciones

```latex
\begin{equation}
\label{eq:nombre}
\text{score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{...}
\end{equation}
```

---

## Estructura Marco Teorico (Capitulo 2) - ~13 paginas

### 2.1 Sistemas de Recuperacion de Informacion (2.5 pags)

- 2.1.1 Busqueda Lexica: BM25 y TF-IDF
- 2.1.2 Busqueda Semantica: Embeddings y Modelos Transformer
- 2.1.3 Busqueda Hibrida: Combinando lo Mejor de Ambos Mundos

### 2.2 Retrieval-Augmented Generation (RAG) (2.5 pags)

- 2.2.1 Arquitectura General del Pipeline RAG
- 2.2.2 Componentes: Indexacion, Retrieval, Generacion
- 2.2.3 Ventajas sobre Fine-tuning de LLMs
- 2.2.4 RAG vs Chatbots Tradicionales (Rule-based)

### 2.3 Modelos de Lenguaje de Gran Escala (LLMs) (2 pags)

- 2.3.1 Evolucion: GPT, LLaMA, Gemma, Qwen
- 2.3.2 LLMs Open-Source y Ollama como Runtime
- 2.3.3 Ensemble de Modelos: Voting, Weighted, Routing, Consensus

### 2.4 Gestion de Contexto en Conversaciones Multi-turn (2 pags)

- 2.4.1 El Problema del Olvido en RAG
- 2.4.2 Context Tracker: Ventana Deslizante de N Interacciones
- 2.4.3 Query Enrichment y Expansion de Consultas
- 2.4.4 Confidence Dinamico: 6 Factores de Evaluacion

### 2.5 Evaluacion de Sistemas RAG (1.5 pags)

- 2.5.1 Framework RAGAs: Evaluacion Automatizada
- 2.5.2 Metricas Clave: Faithfulness, Answer Relevancy, Context Precision/Recall
- 2.5.3 Benchmarking Cientifico vs Evaluacion Manual

### 2.6 Bases de Datos Vectoriales (1 pag)

- 2.6.1 Concepto de Vector Store
- 2.6.2 ChromaDB: Caracteristicas y Ventajas
- 2.6.3 Estrategias de Chunking para FAQ

### 2.7 Trabajos Relacionados (1.5 pags)

- 2.7.1 Chatbots Conversacionales en ONGs y Salud
- 2.7.2 Sistemas RAG en Produccion: Casos de Exito
- 2.7.3 Posicionamiento del Proyecto DNI

---

## Figuras Requeridas

1. Diagrama comparativo BM25 vs Busqueda Semantica
2. Arquitectura general del pipeline RAG (3 fases)
3. Diagrama de ventana deslizante (Context Tracker)
4. Tabla comparativa de LLMs utilizados
5. Esquema del sistema Ensemble con routing

---

## Checklist de Calidad por Seccion

- [ ] Minimo 2 referencias academicas
- [ ] Incluye figura o tabla si supera 1 pagina
- [ ] Termina conectando con el proyecto DNI
- [ ] Vocabulario tecnico pero accesible
- [ ] Numeracion correlativa (2.X, 2.X.1)
- [ ] Sin errores ortograficos ni gramaticales
- [ ] Citas con `\cite{}` referenciando bibliography.bib

---

## Referencias Base (Obligatorias)

1. Lewis et al. (2020) - `\cite{lewis2020rag}`
2. Robertson & Zaragoza (2009) - `\cite{robertson2009bm25}`
3. Devlin et al. (2019) - `\cite{devlin2019bert}`
4. Es et al. (2023) - `\cite{es2023ragas}`
5. Vaswani et al. (2017) - `\cite{vaswani2017attention}`
6. Brown et al. (2020) - `\cite{brown2020gpt3}`
7. Touvron et al. (2023) - `\cite{touvron2023llama}`
