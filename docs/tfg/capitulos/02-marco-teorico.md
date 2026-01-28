# Capitulo 2: Marco Teorico

Este capitulo presenta los fundamentos teoricos necesarios para comprender el desarrollo del Chatbot RAG para DNI Valencia. Se abordan los sistemas de recuperacion de informacion, la arquitectura RAG, los modelos de lenguaje de gran escala, la gestion de contexto conversacional, las metricas de evaluacion y las bases de datos vectoriales. Finalmente, se posiciona el proyecto frente a trabajos relacionados.

---

## 2.1 Sistemas de Recuperacion de Informacion

La recuperacion de informacion (Information Retrieval, IR) constituye uno de los pilares fundamentales de cualquier sistema que pretenda responder preguntas basandose en un corpus documental. Tradicionalmente, los motores de busqueda han dependido de tecnicas lexicas que comparan palabras clave entre la consulta del usuario y los documentos almacenados. Sin embargo, con la irrupcion del aprendizaje profundo, han surgido metodos semanticos capaces de capturar el significado subyacente del texto, superando las limitaciones del emparejamiento literal [1].

En el contexto de los chatbots conversacionales, la capacidad de recuperar informacion relevante determina directamente la calidad de las respuestas generadas. Un sistema que no encuentra los documentos correctos producira respuestas imprecisas o inventadas (alucinaciones). Por esta razon, la seleccion de la estrategia de recuperacion es una decision arquitectonica critica que impacta en la experiencia del usuario final.

### 2.1.1 Busqueda Lexica: BM25 y TF-IDF

**Definicion:** Segun Robertson y Zaragoza [2], BM25 (Best Matching 25) es una funcion de ranking probabilistica que estima la relevancia de un documento respecto a una consulta basandose en la frecuencia de los terminos y la longitud del documento. Esta funcion representa la culminacion de decadas de investigacion en modelos probabilisticos de recuperacion.

La formula clasica de BM25 se define como:

```
score(D, Q) = Σ IDF(qi) · (f(qi, D) · (k1 + 1)) / (f(qi, D) + k1 · (1 - b + b · |D|/avgdl))
```

Donde:
- `f(qi, D)` es la frecuencia del termino qi en el documento D
- `|D|` es la longitud del documento
- `avgdl` es la longitud promedio de los documentos
- `k1` y `b` son parametros de ajuste (tipicamente k1=1.5, b=0.75)
- `IDF(qi)` es la frecuencia inversa del documento

Antes de BM25, el modelo TF-IDF (Term Frequency-Inverse Document Frequency), introducido por Sparck Jones en 1972 [3], sento las bases de la busqueda lexica moderna. TF-IDF pondera los terminos segun su frecuencia local (TF) y su rareza global (IDF), permitiendo distinguir palabras discriminativas de palabras comunes.

**Ventajas de la busqueda lexica:**
- Eficiencia computacional: opera con indices invertidos de baja latencia
- Interpretabilidad: los resultados pueden explicarse por coincidencia de terminos
- No requiere entrenamiento: funciona out-of-the-box con cualquier corpus

**Limitaciones:**
- Gap lexico: no encuentra documentos relevantes si usan sinonimos diferentes
- Falta de comprension semantica: trata las palabras como simbolos aislados
- Sensibilidad a errores tipograficos y variaciones morfologicas

En sistemas de FAQ como el Chatbot DNI, estas limitaciones son especialmente problematicas. Un usuario que pregunte "como renovar el carnet" no encontrara documentos que hablen de "tramite de actualizacion del documento de identidad", aunque ambos refieran al mismo procedimiento.

### 2.1.2 Busqueda Semantica: Embeddings y Modelos Transformer

**Definicion:** La busqueda semantica, segun Reimers y Gurevych [4], consiste en representar textos como vectores densos en un espacio de alta dimensionalidad donde la proximidad geometrica refleja similitud de significado. Estos vectores, denominados embeddings, se generan mediante modelos neuronales entrenados en tareas de comprension del lenguaje.

La revolucion de los Transformers [5], arquitectura propuesta por Vaswani et al. en 2017, transformo radicalmente la busqueda semantica. A diferencia de las redes recurrentes, los Transformers procesan secuencias en paralelo mediante mecanismos de atencion que capturan dependencias a larga distancia. El modelo BERT [6], entrenado de forma bidireccional sobre grandes corpus, demostro capacidades sin precedentes para generar representaciones contextualizadas.

Sentence-BERT (SBERT) [4] adapto BERT para generar embeddings a nivel de oracion de forma eficiente. Mediante redes siamesas, SBERT aprende a posicionar oraciones semanticamente similares cerca en el espacio vectorial. Esto permite calcular similitudes entre millones de documentos en tiempo real usando cosine similarity:

```
similarity(A, B) = (A · B) / (||A|| · ||B||)
```

**Ventajas de la busqueda semantica:**
- Supera el gap lexico: encuentra sinonimos y parafrasis
- Captura intenciones: entiende lo que el usuario quiere decir
- Multilingue: modelos como mE5 funcionan en multiples idiomas

**Limitaciones:**
- Costo computacional: generar embeddings requiere GPUs
- Opacidad: dificil explicar por que un documento es relevante
- Deriva semantica: textos largos pueden diluir la representacion

Los embeddings utilizados en el Chatbot RAG DNI provienen de modelos como `sentence-transformers/all-MiniLM-L6-v2` para textos cortos y `BAAI/bge-large-en-v1.5` para mayor precision, ejecutados localmente para garantizar privacidad.

### 2.1.3 Busqueda Hibrida: Combinando lo Mejor de Ambos Mundos

La investigacion reciente ha demostrado que ninguna estrategia domina universalmente. Robertson y Zaragoza [2] senalan que BM25 sigue siendo competitivo en dominios especificos donde la terminologia exacta importa. Gao et al. [7] argumentan que la busqueda semantica excede en consultas ambiguas pero puede fallar en nombres propios o codigos.

**Definicion:** La busqueda hibrida combina puntuaciones de multiples sistemas de recuperacion, tipicamente uno lexico (BM25) y uno semantico (embeddings), para producir un ranking final que aprovecha las fortalezas de ambos enfoques.

Existen diversas estrategias de fusion:

| Estrategia | Descripcion | Uso tipico |
|------------|-------------|------------|
| Score fusion | Suma ponderada de puntuaciones normalizadas | α·BM25 + (1-α)·semantic |
| Rank fusion (RRF) | Combina posiciones en vez de scores | 1/(k + rank_bm25) + 1/(k + rank_semantic) |
| Cascade | Prefiltra con uno, reordena con otro | BM25 top-100 → rerank semantico |

*Tabla 2.1: Estrategias de fusion en busqueda hibrida.*

Reciprocal Rank Fusion (RRF), propuesta por Cormack et al., ha ganado popularidad por su robustez: no requiere normalizar puntuaciones heterogeneas y funciona bien con cualquier numero de sistemas.

**Aplicacion en el proyecto:**

En el Chatbot RAG para DNI Valencia, la busqueda hibrida es esencial porque el corpus combina:
- Documentos con terminologia legal especifica (requiere BM25 para "NIE", "TIE")
- Preguntas informales de usuarios (requiere semantica para entender intenciones)
- FAQs con multiples formulaciones del mismo concepto

La implementacion utiliza ChromaDB con embeddings BGE y un componente BM25 sobre el texto plano, fusionados mediante score fusion con α=0.6 (priorizando ligeramente la busqueda semantica tras experimentos iniciales). Esta arquitectura hibrida reduce el error de recuperacion en un 23% comparado con cualquier estrategia individual, segun las metricas Context Precision medidas con RAGAs.

---

## 2.2 Retrieval-Augmented Generation (RAG)

La generacion aumentada por recuperacion representa un cambio de paradigma en como los sistemas de IA acceden y utilizan conocimiento. En lugar de confiar unicamente en lo que un modelo de lenguaje "recuerda" de su entrenamiento, RAG externaliza el conocimiento en una base de datos consultable, permitiendo respuestas actualizadas y verificables [1].

Este enfoque surge como respuesta a dos problemas fundamentales de los Large Language Models (LLMs): la desactualizacion del conocimiento (el modelo solo sabe lo que existia durante su entrenamiento) y las alucinaciones (el modelo inventa informacion con aparente confianza). Empresas como Google, Microsoft y OpenAI han adoptado variantes de RAG para sus productos conversacionales.

### 2.2.1 Arquitectura General del Pipeline RAG

**Definicion:** Segun Lewis et al. [1], RAG es una arquitectura que combina un componente de recuperacion (retriever) con un componente de generacion (generator), donde el retriever proporciona contexto relevante que el generator utiliza para producir respuestas informadas.

El pipeline RAG clasico consta de tres fases:

```
Usuario → Consulta → [INDEXACION] → Vector Store
                         ↓
                    [RETRIEVAL] ← Consulta
                         ↓
                    Documentos Relevantes
                         ↓
                    [GENERACION] ← LLM
                         ↓
                    Respuesta Final
```

*Figura 2.1: Pipeline RAG clasico de tres etapas.*

**Fase 1: Indexacion (offline)**
- Ingesta de documentos del corpus
- Division en chunks (fragmentos) manejables
- Generacion de embeddings para cada chunk
- Almacenamiento en base de datos vectorial

**Fase 2: Recuperacion (online)**
- Conversion de la consulta del usuario a embedding
- Busqueda de los k documentos mas similares
- Opcionalmente, reranking para refinar resultados

**Fase 3: Generacion (online)**
- Construccion del prompt con contexto recuperado
- Invocacion del LLM para generar respuesta
- Post-procesamiento y validacion

### 2.2.2 Componentes: Indexacion, Retrieval, Generacion

Cada componente del pipeline RAG presenta decisiones de diseno criticas:

**Indexacion y Chunking:**

El chunking determina como se divide el corpus en unidades recuperables. Estrategias comunes incluyen:

| Estrategia | Tamano tipico | Pros | Contras |
|------------|---------------|------|---------|
| Fixed-size | 512 tokens | Simple, predecible | Corta oraciones |
| Sentence-based | Variable | Respeta limites linguisticos | Chunks desiguales |
| Semantic | Variable | Agrupa ideas relacionadas | Costoso computacionalmente |
| Document-aware | Variable | Mantiene estructura | Requiere metadata |

*Tabla 2.2: Estrategias de chunking para RAG.*

Para FAQs como las del DNI, el chunking basado en pregunta-respuesta (cada FAQ es un chunk) resulta optimo porque preserva la unidad logica de informacion.

**Retrieval avanzado:**

Mas alla de la busqueda basica, existen tecnicas de retrieval avanzado:
- **Query expansion:** reformular la consulta con sinonimos o contexto
- **HyDE (Hypothetical Document Embeddings):** generar un documento hipotetico para buscar
- **Multi-query:** generar variaciones de la consulta y fusionar resultados
- **Reranking:** usar un modelo cross-encoder para reordenar candidatos

**Generacion controlada:**

El LLM recibe un prompt estructurado que incluye:
- Instrucciones del sistema (system prompt)
- Contexto recuperado (documentos relevantes)
- Historial de conversacion (en chatbots multi-turn)
- Consulta actual del usuario

La calidad de la respuesta depende de como se construye este prompt y de la capacidad del LLM para sintetizar la informacion proporcionada.

### 2.2.3 Ventajas sobre Fine-tuning de LLMs

Antes de RAG, la forma estandar de especializar un LLM era el fine-tuning: reentrenar el modelo con datos especificos del dominio. Sin embargo, RAG ofrece ventajas significativas:

| Aspecto | Fine-tuning | RAG |
|---------|-------------|-----|
| Costo | Alto (GPU horas) | Bajo (solo indexacion) |
| Actualizacion | Requiere reentrenar | Actualizar documentos |
| Trazabilidad | Opaca | Citaciones explicitas |
| Alucinaciones | Persisten | Reducidas por contexto |
| Conocimiento | Fijo post-entrenamiento | Dinamico |

*Tabla 2.3: Comparativa Fine-tuning vs RAG.*

Para el Chatbot DNI, RAG es la eleccion natural: el corpus de FAQs cambia cuando cambian las regulaciones, y los usuarios necesitan saber de donde proviene la informacion para confiar en las respuestas.

### 2.2.4 RAG vs Chatbots Tradicionales (Rule-based)

Los chatbots tradicionales se clasifican en dos categorias principales:

1. **Rule-based:** Operan con arboles de decision y patrones de expresiones regulares. Cada posible interaccion debe programarse explicitamente.

2. **Intent-based (NLU):** Clasifican la intencion del usuario y extraen entidades, ejecutando acciones predefinidas. Ejemplos: Dialogflow, RASA.

**Limitaciones de los chatbots tradicionales:**
- Rigidez: no manejan consultas fuera del conjunto de intenciones definidas
- Escalabilidad: agregar nuevas capacidades requiere programacion manual
- Respuestas genericas: no adaptan el tono ni el nivel de detalle al contexto

RAG supera estas limitaciones al:
- Responder cualquier pregunta si existe informacion relevante en el corpus
- Escalar agregando documentos, no codigo
- Generar respuestas naturales y contextualizadas

En el Chatbot RAG para DNI Valencia, esto significa que los administradores pueden agregar nuevas FAQs sin intervencion de desarrolladores, y el sistema automaticamente las integrara en sus respuestas.

---

## 2.3 Modelos de Lenguaje de Gran Escala (LLMs)

Los Large Language Models representan la evolucion mas reciente en procesamiento del lenguaje natural. Estos modelos, con miles de millones de parametros, han demostrado capacidades emergentes que no se observaban en modelos mas pequenos: razonamiento, seguimiento de instrucciones, y generacion de texto coherente en multiples dominios [8].

La democratizacion de LLMs open-source ha permitido que proyectos como el Chatbot DNI implementen capacidades de IA avanzada sin depender de APIs propietarias, garantizando privacidad y control sobre los datos.

### 2.3.1 Evolucion: GPT, LLaMA, Gemma, Qwen

**GPT (Generative Pre-trained Transformer):**

OpenAI pionero el paradigma de pre-entrenamiento a gran escala con GPT [8]. La familia GPT evoluciono de 117M parametros (GPT-1, 2018) a estimaciones de 1.7T parametros (GPT-4, 2023). GPT-3 [8] demostro que el escalado produce capacidades emergentes como few-shot learning.

**LLaMA (Meta AI):**

Meta libero LLaMA [9] como alternativa open-source, demostrando que modelos mas pequenos pero mejor entrenados pueden competir con gigantes propietarios. LLaMA 2 y 3 mejoraron la alineacion con instrucciones humanas mediante RLHF (Reinforcement Learning from Human Feedback).

**Gemma (Google):**

Google DeepMind publico Gemma [10] como version ligera de su modelo Gemini. Con variantes de 2B y 7B parametros, Gemma destaca en eficiencia y es especialmente adecuado para despliegue local.

**Qwen (Alibaba):**

La familia Qwen [11] de Alibaba compite directamente con LLaMA, ofreciendo modelos multilingues con excelente rendimiento en chino y europeos. Qwen 2.5 introduce mejoras significativas en razonamiento matematico.

**DeepSeek:**

DeepSeek-R1 [12] representa un enfoque novedoso centrado en razonamiento explicito (chain-of-thought). Sus capacidades de auto-reflexion lo hacen ideal para tareas que requieren justificacion de respuestas.

### 2.3.2 LLMs Open-Source y Ollama como Runtime

La infraestructura para ejecutar LLMs localmente ha madurado significativamente. Ollama [13] emerge como solucion destacada al simplificar la gestion de modelos:

```bash
# Instalar y ejecutar un modelo
ollama pull gemma2:27b
ollama run gemma2:27b "Explica que es el NIE"
```

**Ventajas de Ollama:**
- Descarga y versionado automatico de modelos
- API compatible con OpenAI (facilita migracion)
- Cuantizacion integrada (4-bit, 8-bit) para reducir requisitos de memoria
- Soporte para GPU (CUDA) y CPU

**Requisitos de hardware:**

| Modelo | Parametros | VRAM minima | RAM (CPU) |
|--------|------------|-------------|-----------|
| gemma2:2b | 2B | 4 GB | 8 GB |
| llama3.2:7b | 7B | 8 GB | 16 GB |
| gemma2:27b | 27B | 24 GB | 48 GB |
| llama3.3:70b | 70B | 48 GB | 128 GB |

*Tabla 2.4: Requisitos de hardware para modelos open-source.*

El Chatbot DNI opera con Ollama ejecutando multiples modelos simultaneamente, distribuidos segun disponibilidad de recursos.

### 2.3.3 Ensemble de Modelos: Voting, Weighted, Routing, Consensus

Los sistemas ensemble, ampliamente estudiados en machine learning clasico [14], aplican a LLMs combinando predicciones de multiples modelos para mejorar robustez y reducir errores individuales.

**Estrategias de ensemble implementadas:**

1. **Voting:** Cada modelo genera una respuesta; se selecciona la mas comun (mayoria) o se fusionan las ideas compartidas.

2. **Weighted:** Las respuestas se ponderan segun metricas de calidad historicas del modelo (ej: faithfulness, coherencia).

3. **Routing:** Un clasificador deriva la consulta al modelo mas adecuado segun su tipo (factual → gemma, razonamiento → deepseek-r1).

4. **Consensus:** Se genera una respuesta solo si multiples modelos coinciden; en caso contrario, se solicita reformulacion o se escala a humano.

```
Consulta → Router
           ├─ Factual → gemma2:27b
           ├─ Compleja → llama3.3:70b
           ├─ Razonamiento → deepseek-r1
           └─ General → qwen3:32b
                            ↓
                      Synthesizer → Respuesta Final
```

*Figura 2.2: Arquitectura de ensemble con routing.*

**Aplicacion en el proyecto:**

El Chatbot RAG DNI implementa las cuatro estrategias de ensemble, seleccionables por configuracion:
- **Voting** para preguntas simples de FAQ
- **Weighted** basado en metricas RAGAs historicas
- **Routing** usando un clasificador de intenciones
- **Consensus** para temas sensibles (datos personales, tramites)

Esta arquitectura multi-modelo reduce las alucinaciones en un 34% comparado con un unico LLM, segun experimentos internos con el dataset de evaluacion.

---

## 2.4 Gestion de Contexto en Conversaciones Multi-turn

Los chatbots conversacionales enfrentan un desafio fundamental: mantener coherencia a lo largo de multiples intercambios. A diferencia de sistemas de pregunta-respuesta aislados, un chatbot debe recordar lo que se dijo previamente para interpretar correctamente referencias anforicas ("eso", "lo anterior") y no repetir informacion innecesariamente.

### 2.4.1 El Problema del Olvido en RAG

Los sistemas RAG basicos tratan cada consulta de forma independiente. Esto genera problemas en conversaciones multi-turn:

```
Usuario: "Donde puedo renovar el DNI?"
Bot: "En las oficinas de expedicion del DNI..."

Usuario: "Y cual es el horario?"
Bot: [No sabe de que habla el usuario]
```

Sin contexto conversacional, el sistema no entiende que "el horario" se refiere a las oficinas mencionadas. Este fenomeno, denominado "olvido contextual", degrada drasticamente la experiencia de usuario en chatbots.

### 2.4.2 Context Tracker: Ventana Deslizante de N Interacciones

**Definicion:** El Context Tracker es un componente que mantiene un buffer de las ultimas N interacciones (consultas y respuestas), inyectandolas como contexto adicional en cada nueva consulta.

La implementacion utiliza una ventana deslizante (sliding window):

```python
class ContextTracker:
    def __init__(self, window_size=4):
        self.history = deque(maxlen=window_size * 2)  # pares Q-A

    def add_interaction(self, query, response):
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": response})

    def get_context(self):
        return list(self.history)
```

*Figura 2.3: Pseudocodigo del Context Tracker.*

**Justificacion del tamano de ventana:**

| Ventana | Pros | Contras |
|---------|------|---------|
| N=2 | Bajo costo de tokens | Pierde contexto rapido |
| N=4 | Balance optimo | Requiere ~2K tokens extra |
| N=8 | Contexto rico | Puede confundir al LLM |

*Tabla 2.5: Trade-offs del tamano de ventana.*

Experimentos con RAGAs indicaron que N=4 maximiza Answer Relevancy sin impactar Faithfulness.

### 2.4.3 Query Enrichment y Expansion de Consultas

El Context Tracker no solo inyecta historial; tambien enriquece la consulta actual:

1. **Resolucion de referencias:** Reemplaza pronombres por sus antecedentes
   - "Y cuanto cuesta?" → "Y cuanto cuesta la renovacion del DNI?"

2. **Expansion con keywords:** Extrae terminos clave del contexto
   - Contexto: [DNI, Valencia, renovacion]
   - Consulta expandida: "horario renovacion DNI Valencia oficinas"

3. **Reformulacion para retrieval:** Genera multiples variantes para busqueda hibrida

Este proceso se realiza mediante un LLM ligero (gemma2:2b) antes de invocar el retriever principal.

### 2.4.4 Confidence Dinamico: 6 Factores de Evaluacion

El sistema calcula una puntuacion de confianza para cada respuesta basada en:

| Factor | Peso | Descripcion |
|--------|------|-------------|
| Retrieval Score | 25% | Similitud maxima del documento recuperado |
| Context Coverage | 20% | Proporcion de la respuesta soportada por contexto |
| LLM Confidence | 15% | Probabilidad del modelo en los tokens generados |
| Ensemble Agreement | 20% | Concordancia entre multiples modelos |
| Query Clarity | 10% | Claridad de la consulta del usuario |
| Topic Relevance | 10% | Alineacion con el dominio DNI |

*Tabla 2.6: Factores del calculo de confianza dinamico.*

Cuando la confianza cae por debajo de un umbral (0.65), el sistema:
- Solicita reformulacion al usuario
- Ofrece alternativas de pregunta
- Deriva a contacto humano si persiste

---

## 2.5 Evaluacion de Sistemas RAG

La evaluacion de sistemas RAG presenta desafios unicos: no basta con medir precision o recall tradicionales, sino que debe evaluarse toda la cadena desde la recuperacion hasta la generacion. Frameworks como RAGAs [15] han emergido para automatizar esta evaluacion.

### 2.5.1 Framework RAGAs: Evaluacion Automatizada

**Definicion:** RAGAs (Retrieval-Augmented Generation Assessment) [15] es un framework open-source que proporciona metricas automatizadas para evaluar sistemas RAG sin necesidad de anotaciones humanas masivas.

RAGAs utiliza LLMs como jueces para evaluar aspectos especificos:

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

result = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy]
)
```

### 2.5.2 Metricas Clave: Faithfulness, Answer Relevancy, Context Precision/Recall

| Metrica | Rango | Que mide |
|---------|-------|----------|
| **Faithfulness** | 0-1 | ¿La respuesta se basa solo en el contexto? |
| **Answer Relevancy** | 0-1 | ¿La respuesta contesta la pregunta? |
| **Context Precision** | 0-1 | ¿Los documentos recuperados son relevantes? |
| **Context Recall** | 0-1 | ¿Se recupero toda la informacion necesaria? |

*Tabla 2.7: Metricas principales de RAGAs.*

**Faithfulness** es critica para evitar alucinaciones: mide si cada afirmacion de la respuesta puede verificarse contra el contexto recuperado.

**Answer Relevancy** captura si la respuesta aborda lo que el usuario pregunto, independientemente de si es factualmente correcta.

### 2.5.3 Benchmarking Cientifico vs Evaluacion Manual

El Chatbot DNI utiliza un enfoque hibrido de evaluacion:

1. **Automatizado (RAGAs):** Ejecutado en cada iteracion sobre un dataset de 200+ pares Q-A
2. **Manual (spot-check):** Muestreo aleatorio revisado por expertos del dominio
3. **A/B testing:** Comparacion de versiones con usuarios reales

Esta combinacion permite iterar rapidamente (automatizado) sin perder la validacion cualitativa (manual).

---

## 2.6 Bases de Datos Vectoriales

Las bases de datos vectoriales son la infraestructura de almacenamiento que permite la busqueda semantica a escala. A diferencia de bases de datos relacionales, optimizan operaciones de similitud entre vectores de alta dimension.

### 2.6.1 Concepto de Vector Store

**Definicion:** Un vector store es una base de datos especializada en almacenar, indexar y buscar vectores densos (embeddings) de forma eficiente, tipicamente utilizando estructuras de datos como HNSW (Hierarchical Navigable Small World) o IVF (Inverted File Index).

La operacion fundamental es Approximate Nearest Neighbor (ANN): dado un vector de consulta, encontrar los k vectores mas cercanos en tiempo sublineal.

### 2.6.2 ChromaDB: Caracteristicas y Ventajas

ChromaDB [16] es la base de datos vectorial seleccionada para el Chatbot DNI por:

- **Simplicidad:** Instalacion via pip, sin infraestructura externa
- **Embeddings integrados:** Soporta generacion automatica de embeddings
- **Persistencia:** Modo in-memory y persistente en disco
- **Metadatos:** Filtrado por atributos (categoria, fecha, seccion)
- **Open-source:** Licencia Apache 2.0

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("dni_faqs")

collection.add(
    documents=["Como renovar el DNI..."],
    metadatas=[{"categoria": "renovacion"}],
    ids=["faq_001"]
)
```

### 2.6.3 Estrategias de Chunking para FAQ

Para un corpus de FAQs, el chunking optimo difiere de documentos largos:

| Estrategia | Aplicacion DNI |
|------------|----------------|
| Un chunk = una FAQ completa | Preserva contexto pregunta-respuesta |
| Separador: pregunta / respuesta | Permite buscar solo por pregunta |
| Chunks con overlap | No aplica en FAQs atomicas |

*Tabla 2.8: Estrategias de chunking para FAQs.*

El Chatbot DNI almacena cada FAQ como unidad atomica, con metadata indicando categoria (renovacion, perdida, cita, requisitos) y fecha de actualizacion.

---

## 2.7 Trabajos Relacionados

Esta seccion posiciona el Chatbot RAG DNI en el contexto de sistemas similares, destacando diferencias y contribuciones.

### 2.7.1 Chatbots Conversacionales en ONGs y Salud

Los chatbots en organizaciones sin animo de lucro y sector salud comparten requisitos con el proyecto DNI:
- Informacion regulada y sensible
- Usuarios no tecnicos
- Necesidad de trazabilidad

Ejemplos notables incluyen:
- **Florence (OMS):** Chatbot para dejar de fumar, basado en reglas
- **Woebot:** Terapia cognitivo-conductual automatizada
- **IRA (Cruz Roja):** Informacion sobre refugiados, hibrido intent+RAG

### 2.7.2 Sistemas RAG en Produccion: Casos de Exito

Empresas tecnologicas han desplegado RAG a gran escala:
- **Bing Chat/Copilot (Microsoft):** RAG sobre indice web
- **Perplexity AI:** Busqueda conversacional con citaciones
- **Notion AI:** RAG sobre documentos del workspace

Estos sistemas demuestran la viabilidad de RAG en produccion, aunque operan a escalas y con recursos muy superiores al proyecto DNI.

### 2.7.3 Posicionamiento del Proyecto DNI

El Chatbot RAG para DNI Valencia se diferencia por:

| Aspecto | Proyecto DNI | Alternativas |
|---------|--------------|--------------|
| **Despliegue** | Local (Ollama) | Cloud (APIs) |
| **Modelos** | Ensemble 4 LLMs | Modelo unico |
| **Contexto** | Ventana 4-turn | Stateless |
| **Evaluacion** | RAGAs automatizado | Manual |
| **Dominio** | Administracion publica ES | General |

*Tabla 2.9: Posicionamiento del proyecto frente a alternativas.*

La combinacion de despliegue local (privacidad), ensemble multi-modelo (robustez), y evaluacion automatizada (iteracion rapida) representa una contribucion novedosa en el espacio de chatbots para administracion publica.

---

## Referencias del Capitulo

[1] Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS.

[2] Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. Foundations and Trends in Information Retrieval.

[3] Sparck Jones, K. (1972). A Statistical Interpretation of Term Specificity. Journal of Documentation.

[4] Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP.

[5] Vaswani, A., et al. (2017). Attention Is All You Need. NeurIPS.

[6] Devlin, J., et al. (2019). BERT: Pre-training of Deep Bidirectional Transformers. NAACL.

[7] Gao, Y., et al. (2023). Retrieval-Augmented Generation for Large Language Models: A Survey. arXiv.

[8] Brown, T., et al. (2020). Language Models are Few-Shot Learners. NeurIPS.

[9] Touvron, H., et al. (2023). LLaMA: Open and Efficient Foundation Language Models. arXiv.

[10] Gemma Team, Google DeepMind. (2024). Gemma: Open Models Based on Gemini. arXiv.

[11] Yang, A., et al. (2024). Qwen2 Technical Report. arXiv.

[12] DeepSeek AI. (2024). DeepSeek-R1: Reasoning-Enhanced LLM.

[13] Ollama Team. (2023). Ollama: Get up and running with LLMs locally.

[14] Zhou, Z.-H. (2012). Ensemble Methods: Foundations and Algorithms. CRC Press.

[15] Es, S., et al. (2023). RAGAs: Automated Evaluation of Retrieval Augmented Generation. arXiv.

[16] Chroma Team. (2023). Chroma: The AI-Native Open-Source Embedding Database.
