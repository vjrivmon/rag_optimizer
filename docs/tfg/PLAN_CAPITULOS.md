# Plan de Capitulos - TFG Chatbot RAG DNI Valencia

**Titulo:** Desarrollo de un Chatbot Conversacional con RAG para DNI Valencia
**Autor:** Vicente Rivas Monferrer **Universidad:** UPV - Grado en Tecnologias
Interactivas **Curso:** 2025-2026

---

## Estado General

| Capitulo  | Titulo                   | Estado                | Paginas est. | Skill                    |
| --------- | ------------------------ | --------------------- | ------------ | ------------------------ |
| 1         | Introduccion             | Esqueleto LaTeX       | 5-7          | `tfg-cap1-introduccion`  |
| 2         | Marco Teorico            | **Completo en LaTeX** | 13           | `tfg-cap2-marco-teorico` |
| 3         | Metodologia y Desarrollo | Esqueleto LaTeX       | 20-25        | `tfg-cap3-metodologia`   |
| 4         | Resultados y Evaluacion  | Esqueleto LaTeX       | 15-20        | `tfg-cap4-resultados`    |
| 5         | Conclusiones             | Esqueleto LaTeX       | 5-8          | `tfg-cap5-conclusiones`  |
| -         | Bibliografia             | Completo (30+ refs)   | 2-3          | -                        |
| **Total** |                          |                       | **60-76**    |                          |

---

## Detalle por Capitulo

### Capitulo 1: Introduccion (5-7 pags)

**Estado:** Esqueleto con TODOs

| Seccion                      | Estado    | Notas                              |
| ---------------------------- | --------- | ---------------------------------- |
| 1.1 Contexto y Motivacion    | Pendiente | Necesita datos INE/voluntariado    |
| 1.2 Definicion del Problema  | Pendiente | Requisitos DNI claros en CLAUDE.md |
| 1.3 Objetivos                | Pendiente | 6 OEs SMART definidos en skill     |
| 1.4 Alcance y Limitaciones   | Pendiente | Delimitado en skill                |
| 1.5 Estructura del Documento | Pendiente | Breve, cuando esten los demas caps |

**Figuras:** 0 **Tablas:** 1 (objetivos especificos) **Dependencias:** Ninguna
(puede escribirse primero)

---

### Capitulo 2: Marco Teorico (13 pags)

**Estado:** Completo en LaTeX (convertido de Markdown)

| Seccion                        | Estado   | Notas                                        |
| ------------------------------ | -------- | -------------------------------------------- |
| 2.1 Sistemas de Recuperacion   | Completo | BM25, semantica, hibrida                     |
| 2.2 RAG                        | Completo | Pipeline, componentes, vs fine-tuning        |
| 2.3 LLMs                       | Completo | GPT, LLaMA, Gemma, Qwen, Ollama, ensemble    |
| 2.4 Contexto Multi-turn        | Completo | ContextTracker, query enrichment, confidence |
| 2.5 Evaluacion RAG             | Completo | RAGAs, metricas, benchmarking                |
| 2.6 Bases de Datos Vectoriales | Completo | ChromaDB, chunking FAQ                       |
| 2.7 Trabajos Relacionados      | Completo | ONGs, RAG produccion, posicionamiento        |

**Figuras pendientes:**

- [ ] Diagrama comparativo BM25 vs busqueda semantica
- [ ] Arquitectura pipeline RAG (3 fases)
- [ ] Diagrama ventana deslizante (Context Tracker)
- [ ] Esquema sistema Ensemble con routing

**Tablas:** 9 tablas completas **Ecuaciones:** 2 (BM25, cosine similarity)
**Citas:** 16 referencias usadas (de 30+ disponibles)

---

### Capitulo 3: Metodologia y Desarrollo (20-25 pags)

**Estado:** Esqueleto con TODOs detallados

| Seccion                       | Estado    | Paginas est. | Datos fuente                 |
| ----------------------------- | --------- | ------------ | ---------------------------- |
| 3.1 Metodologia Desarrollo    | Pendiente | 2            | CLAUDE.md cronologia         |
| 3.2 Arquitectura Sistema      | Pendiente | 3            | CLAUDE.md arquitectura       |
| 3.3 Pipeline RAG              | Pendiente | 4            | src/core/                    |
| 3.4 Context Tracking          | Pendiente | 3            | src/core/context_tracker.py  |
| 3.5 Persistencia Cross-Sesion | Pendiente | 3            | src/services/, src/database/ |
| 3.6 Ensemble Multi-Modelo     | Pendiente | 2            | src/ensemble/                |
| 3.7 Seguridad                 | Pendiente | 1.5          | vicente_rag/security/        |
| 3.8 Infraestructura           | Pendiente | 1.5          | docker-compose, scripts/     |

**Figuras requeridas:**

- [ ] Diagrama arquitectura general (web + Telegram)
- [ ] Pipeline RAG completo (3 fases con componentes)
- [ ] Flujo del Context Tracking
- [ ] Diagrama ER base de datos (7 tablas)
- [ ] Arquitectura Ensemble con routing
- [ ] Cronograma de desarrollo (9 fases)

**Tablas requeridas:**

- [ ] Fases de desarrollo con fechas y scores
- [ ] Stack tecnologico
- [ ] Configuracion pipeline RAG
- [ ] Factores confidence dinamico
- [ ] Comparativa estrategias ensemble

**Dependencias:** Escribir ANTES de Fase 4 (seguridad modifica codigo)

---

### Capitulo 4: Resultados y Evaluacion (15-20 pags)

**Estado:** Esqueleto con TODOs

| Seccion                   | Estado    | Paginas est. | Datos fuente                           |
| ------------------------- | --------- | ------------ | -------------------------------------- |
| 4.1 Metricas Evaluacion   | Pendiente | 2            | RAGAs docs                             |
| 4.2 Benchmarks RAG        | Pendiente | 3            | results/                               |
| 4.3 Evolucion Rendimiento | Pendiente | 3            | CLAUDE.md tablas                       |
| 4.4 Resultados Ensemble   | Pendiente | 2            | results/ensemble\_\*.json              |
| 4.5 Resultados Context    | Pendiente | 2            | tests/benchmark_context_persistence.py |
| 4.6 Resultados Seguridad  | Pendiente | 2            | tests/security/ (post-Fase 3)          |
| 4.7 Discusion             | Pendiente | 2            | Sintesis de todo                       |

**Figuras requeridas:**

- [ ] Grafica evolucion scores v1.0 -> v4.1.1
- [ ] Histograma distribucion confidence
- [ ] Comparativa antes/despues anti-contaminacion
- [ ] Heatmap correlacion metricas RAGAs

**Tablas requeridas:**

- [ ] Benchmark 115 preguntas (metricas completas)
- [ ] Evolucion versiones (v1.0 a v4.1.1)
- [ ] Comparativa 4 estrategias ensemble
- [ ] Anti-contaminacion antes/despues

**Dependencias:** Seccion 4.6 depende de Fase 3 (tests seguridad)

---

### Capitulo 5: Conclusiones (5-8 pags)

**Estado:** Esqueleto con TODOs

| Seccion                | Estado    | Paginas est. |
| ---------------------- | --------- | ------------ |
| 5.1 Conclusiones       | Pendiente | 2            |
| 5.2 Contribuciones     | Pendiente | 1            |
| 5.3 Limitaciones       | Pendiente | 1            |
| 5.4 Trabajo Futuro     | Pendiente | 1.5          |
| 5.5 Reflexion Personal | Pendiente | 1            |

**Figuras:** 0 **Tablas:** 1 (objetivos vs evidencia) **Dependencias:** Caps 1 y
4 deben estar completos

---

## Orden de Escritura Recomendado

1. **Cap 3 (Metodologia)** - Primero, documenta el sistema actual
2. **Cap 1 (Introduccion)** - Segundo, con objetivos claros tras documentar
3. **Cap 4 (Resultados)** - Tercero, datos cuantitativos
4. **Cap 5 (Conclusiones)** - Ultimo, recapitula todo
5. **Cap 2 (Marco Teorico)** - Ya completo, solo revisar figuras

## Infraestructura LaTeX

```
docs/tfg/
├── main.tex                    # Documento principal
├── config/
│   └── preamble.tex           # Configuracion (adaptada de memoria_practicas)
├── capitulos/
│   ├── 01-introduccion.tex    # Esqueleto
│   ├── 02-marco-teorico.tex   # COMPLETO (convertido de .md)
│   ├── 02-marco-teorico.md    # Original en Markdown (referencia)
│   ├── 03-metodologia.tex     # Esqueleto
│   ├── 04-resultados.tex      # Esqueleto
│   └── 05-conclusiones.tex    # Esqueleto
├── figuras/                   # Directorio para imagenes
├── referencias/
│   └── bibliography.bib       # 30+ referencias BibTeX
├── plantillas/
│   └── seccion-template.md    # Template para secciones
└── PLAN_CAPITULOS.md          # Este archivo
```

## Compilacion

```bash
cd docs/tfg
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

O con latexmk:

```bash
cd docs/tfg
latexmk -pdf main.tex
```
