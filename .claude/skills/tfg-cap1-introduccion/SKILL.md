# Skill: TFG Cap 1 - Introduccion

## Descripcion

Genera el Capitulo 1 (Introduccion) del TFG "Desarrollo de un Chatbot
Conversacional con RAG para DNI Valencia". Establece contexto social, define el
problema, fija objetivos SMART y delimita el alcance.

## Activacion

- Comando: `/tfg-cap1 <seccion>`
- Triggers: "escribe introduccion", "capitulo 1", "objetivos tfg"

## Archivo Destino

`docs/tfg/capitulos/01-introduccion.tex`

## Contexto del Proyecto

```yaml
titulo: "Desarrollo de un Chatbot Conversacional con RAG para DNI Valencia"
autor: Vicente Rivas Monferrer
universidad: UPV - Grado en Tecnologias Interactivas
curso: 2025-2026
asociacion: DNI (Damos Nuestra Ilusion) - Valencia
lema: PARA. MIRA. AYUDA.
```

## Estructura del Capitulo (~5-7 paginas)

### 1.1 Contexto y Motivacion (1.5 pags)

**Patron narrativo:** General -> Especifico -> Proyecto

1. **Contexto social:** El tercer sector en Espana (ONGs, voluntariado). Citar
   datos del INE/Plataforma de Voluntariado sobre participacion juvenil.
2. **Brecha digital:** ONGs pequenas carecen de herramientas tecnologicas
   modernas. Comunicacion manual = no escalable.
3. **Oportunidad IA:** Los avances en LLMs y RAG permiten crear asistentes
   virtuales accesibles incluso para organizaciones con recursos limitados.
4. **DNI Valencia:** Asociacion de jovenes voluntarios (18-30 anos) con 5
   proyectos activos:
   - Desayunos Solidarios (personas sin hogar)
   - RESIS - Charlas con Abuelitos (residencia L'Acollida)
   - COLES - Refuerzo Escolar
   - Rehabilitar Valencia (apoyo DANA)
   - Recogida de Plasticos (kayak)
5. **Motivacion personal:** Conexion con Catedra ENIA-UPV. Aplicar IA al
   servicio del voluntariado.

**Datos fuente:** `data/documents/` (16 archivos), CLAUDE.md (resumen ejecutivo)

### 1.2 Definicion del Problema (1 pag)

**Problema concreto:**

- DNI recibe consultas repetitivas de voluntarios (horarios, ubicaciones,
  requisitos)
- Respuestas manuales por Instagram/email: no escalable, inconsistente, no 24/7
- Informacion dispersa en multiples documentos sin estructura centralizada
- Voluntarios nuevos no saben como participar ni a quien preguntar

**Requisitos derivados:**

- Multicanal: web + Telegram (canales donde estan los jovenes)
- Persistencia: recordar conversaciones entre sesiones
- Privacidad: datos de voluntarios no pueden salir de infraestructura controlada
- Actualizacion: contenido debe poder cambiarse sin programar
- Evaluacion: rendimiento medible objetivamente

### 1.3 Objetivos (1 pag)

**Objetivo General:**

> Desarrollar un chatbot conversacional basado en Retrieval-Augmented Generation
> (RAG) que atienda consultas de voluntarios de la asociacion DNI Valencia de
> forma autonoma, precisa y multicanal.

**Objetivos Especificos (SMART):**

| ID  | Objetivo                                                            | Metrica de exito                    |
| --- | ------------------------------------------------------------------- | ----------------------------------- |
| OE1 | Implementar pipeline RAG con busqueda hibrida (BM25 + semantica)    | Context Precision > 0.80            |
| OE2 | Desarrollar sistema de contexto conversacional multi-turn           | 60%+ preguntas implicitas correctas |
| OE3 | Integrar bot de Telegram con persistencia cross-sesion (PostgreSQL) | Memoria >7 dias verificada          |
| OE4 | Evaluar rendimiento con framework RAGAs automatizado                | Score combinado > 0.85              |
| OE5 | Garantizar privacidad mediante despliegue local con Ollama          | 0 datos enviados a APIs externas    |
| OE6 | Implementar sistema ensemble multi-modelo                           | Mejora >3% vs modelo unico          |

### 1.4 Alcance y Limitaciones (0.5 pags)

**Dentro del alcance:**

- Corpus: 16 documentos DNI, 263 chunks (197 FAQ + 66 regulares)
- Canales: Web (WebSocket) + Telegram (polling)
- Modelos: gemma2:27b (principal), llama3.3:70b, qwen2.5:32b, deepseek-r1
- Idioma: Espanol
- Evaluacion: RAGAs automatizado + benchmark 115 preguntas

**Fuera del alcance:**

- WhatsApp Business (trabajo futuro)
- Multimodalidad (imagenes, audio)
- Fine-tuning de modelos
- Despliegue en cloud publico
- Soporte multilingue (valenciano, ingles)

**Limitaciones conocidas:**

- Dependencia del servidor Ollama UPV (disponibilidad)
- Dataset de evaluacion limitado (115 preguntas)
- Testing con usuarios reales limitado en alcance

### 1.5 Estructura del Documento (0.5 pags)

Resumen de cada capitulo en 2-3 lineas:

- Cap 2: Marco Teorico
- Cap 3: Metodologia y Desarrollo
- Cap 4: Resultados y Evaluacion
- Cap 5: Conclusiones y Trabajo Futuro

## Patron de Escritura

Seguir el patron academico de 5 partes del skill tfg base:

1. Contexto Introductorio (1-2 parrafos)
2. Definicion Clara (con cita si aplica)
3. Ampliacion Conceptual (2-3 parrafos)
4. Ejemplos Practicos (datos concretos de DNI)
5. Conexion con el Proyecto

## Formato LaTeX

- Usar `\section`, `\subsection` con `\label{}`
- Tablas con `booktabs` (\toprule, \midrule, \bottomrule)
- Citas con `\cite{}`
- Acentos con LaTeX: \'a, \'e, \'i, \'o, \'u, \~n

## Referencias Sugeridas

- Adamopoulou & Moussiades (2020) - Chatbot overview
- Montenegro et al. (2019) - Chatbots en salud
- Lewis et al. (2020) - RAG (mencion breve)
- Es et al. (2023) - RAGAs (mencion breve)

## Checklist de Calidad

- [ ] Contexto social con datos concretos
- [ ] Problema claramente definido y acotado
- [ ] Objetivos SMART con metricas verificables
- [ ] Alcance explicitamente delimitado
- [ ] Limitaciones honestas reconocidas
- [ ] Estructura del documento completa
- [ ] Tono academico pero accesible
- [ ] Maximo 2 referencias por seccion (es introduccion, no marco teorico)
