# 🤖 Chatbot RAG Interactivo - Documentación Completa

## 📋 Descripción General

Sistema de chatbot interactivo que permite a los usuarios hacer preguntas y recibir respuestas generadas por diferentes modelos LLM o estrategias ensemble, con citación de fuentes y streaming de estados en tiempo real.

### Características Principales

- ✅ **4 Modelos LLM Individuales**: Gemma 2 27B, Llama 3.3 70B, Qwen 3 32B, DeepSeek R1
- ✅ **4 Estrategias Ensemble**: Voting, Weighted, Routing, Consensus
- ✅ **Streaming en Tiempo Real**: Estados intermedios (conectando, pensando, procesando)
- ✅ **Citación de Fuentes**: Chunks recuperados con scores de similitud
- ✅ **Interfaz Mobile-First**: Diseño responsive optimizado para móvil y desktop
- ✅ **Animaciones Suaves**: Indicador de "pensando" tipo Claude
- ✅ **Información Detallada**: Pros/contras de cada modelo, scores, características

---

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.8+
- Entorno virtual activado
- Acceso al servidor UPV (https://ollama.gti-ia.upv.es:443)
- Base de datos vectorial configurada en `data/vectorstore/chroma_db`

### Instalación y Lanzamiento

```bash
# Opción 1: Script automatizado (recomendado)
./run_chatbot.sh

# Opción 2: Manual
cd interface/chatbot/backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Acceso

Abre tu navegador en: **http://localhost:8000**

---

## 📁 Estructura del Proyecto

```
interface/chatbot/
├── backend/
│   ├── app.py                 # FastAPI app principal
│   ├── chat_handler.py        # Lógica de procesamiento de preguntas
│   └── model_profiles.py      # Perfiles de modelos (pros/contras)
└── frontend/
    ├── templates/
    │   └── index.html          # HTML principal
    └── static/
        ├── css/
        │   ├── styles.css      # Estilos principales
        │   └── animations.css  # Animaciones
        ├── js/
        │   ├── app.js          # Lógica principal del chat
        │   └── websocket-client.js  # Cliente WebSocket
        └── images/logos/       # Logos de modelos (SVG)
```

---

## 🎨 Interfaz de Usuario

### Componentes Principales

#### 1. Header
- **Logo del modelo activo**: Cambia según la selección
- **Estado de conexión**: Indicador con el servidor UPV
  - 🟢 Verde: Conectado
  - 🟡 Amarillo: Modo degradado
  - 🔴 Rojo: Sin conexión

#### 2. Selector de Modelo
- **Dropdown** con 8 opciones:
  - 4 modelos individuales
  - 4 estrategias ensemble
- **Card informativa expandible** con:
  - Nombre y proveedor
  - Descripción breve
  - Score y tasa de aciertos (del benchmark)
  - Pros y contras
  - "Mejor para" (casos de uso recomendados)
  - "Cómo funciona" (solo ensemble)

#### 3. Área de Chat
- **Mensajes de usuario**: Burbujas grises alineadas a la derecha
- **Mensajes del bot**: Burbujas blancas alineadas a la izquierda
- **Indicador de "pensando"**: Spinner animado con frases rotativas
- **Fuentes consultadas**: Sección expandible con chunks citados

#### 4. Input de Pregunta
- **Textarea autoajustable**: Se expande con el contenido
- **Botón de envío**: Con icono de avión de papel
- **Atajos de teclado**:
  - Enter: Enviar pregunta
  - Shift+Enter: Nueva línea

---

## 🔧 Arquitectura Técnica

### Backend (FastAPI)

#### Endpoints REST

```python
GET /
# Sirve el HTML principal

GET /api/models
# Retorna perfiles de todos los modelos y estrategias
# Response: {server_status: str, models: {...}}

GET /api/health
# Health check del servidor
# Response: {status: str, models_loaded: int, ensemble_ready: bool}
```

#### WebSocket

```python
WS /ws/chat
# Comunicación bidireccional para streaming de estados

# Cliente envía:
{
  "question": "¿Dónde es la actividad de coles?",
  "model": "gemma2:27b"
}

# Servidor envía (múltiples mensajes):
{"type": "status", "status": "connecting"}
{"type": "status", "status": "retrieving"}
{"type": "status", "status": "thinking"}
{"type": "status", "status": "finalizing"}
{"type": "complete", "response": {...}}

# O en caso de error:
{"type": "error", "error": "Descripción del error"}
```

#### Estados de Procesamiento

1. **connecting** (0.5s): Validando conexión con servidor UPV
2. **retrieving**: Recuperando chunks relevantes del vector store
3. **thinking**: Generando respuesta con el modelo
   - Frases rotativas: "Pensando...", "Razonando...", "Analizando...", etc.
4. **processing**: Aplicando estrategia ensemble (solo ensemble)
5. **finalizing** (0.5s): "Ya casi lo tengo..."
6. **done**: Respuesta completa enviada

#### Respuesta Final

```json
{
  "answer": "La actividad de coles se realiza en...",
  "sources": [
    {
      "text": "Contenido del chunk (máx 500 chars)",
      "score": 0.95
    }
  ],
  "time": 12.5
}
```

---

## 🎯 Modelos y Estrategias

### Modelos Individuales

#### 1. Gemma 2 27B (Google) 👑
- **Score**: 0.915 (22/26 correctas)
- **Color**: Azul (#4285F4)
- **Pros**:
  - Mejor rendimiento general (91.5%)
  - Alta consistencia en respuestas
  - Excelente comprensión de contexto
  - Rápido y eficiente
- **Contras**:
  - Ventana de contexto limitada (4096 tokens)
  - Puede ser muy conciso en ocasiones
- **Mejor para**: Preguntas generales, respuestas precisas y rápidas

#### 2. Llama 3.3 70B (Meta)
- **Score**: 0.886 (21/26 correctas)
- **Color**: Morado (#9333EA)
- **Pros**:
  - Excelente capacidad de razonamiento
  - Respuestas muy detalladas
  - Buen balance precisión/detalle
- **Contras**:
  - Más lento (70B parámetros)
  - Ventana de contexto más pequeña (2048)
  - Consume más recursos
- **Mejor para**: Preguntas complejas que requieren análisis profundo

#### 3. Qwen 3 32B (Alibaba)
- **Score**: 0.850 (17/26 correctas)
- **Color**: Rojo (#EF4444)
- **Pros**:
  - Soporte multilingüe nativo
  - Bueno para contextos diversos
  - Balance eficiencia/calidad
- **Contras**:
  - A veces responde en inglés
  - Menos consistente que Gemma
  - Problemas con preguntas filosóficas
- **Mejor para**: Preguntas variadas, contextos internacionales

#### 4. DeepSeek R1 (DeepSeek)
- **Score**: 0.633 (10/26 correctas)
- **Color**: Verde (#10B981)
- **Pros**:
  - Muestra proceso de razonamiento
  - Bueno para debugging
  - Transparencia en el pensamiento
- **Contras**:
  - Rendimiento más bajo (63.3%)
  - Respuestas largas con `<think>` tags
  - Menos preciso en general
- **Mejor para**: Cuando quieres ver el proceso de razonamiento

### Estrategias Ensemble

#### 1. Voting (Votación Mayoritaria) 🗳️
- **Score**: 0.915 (22/26 correctas)
- **Color**: Naranja (#F59E0B)
- **Cómo funciona**: Genera con los 4 modelos y elige la respuesta con mayor `combined_score`
- **Pros**:
  - Empata con el mejor modelo individual
  - Muy robusto y confiable
  - Simple y efectivo
- **Contras**:
  - No mejora sobre Gemma individual
  - Requiere todos los modelos (más lento)
- **Mejor para**: Máxima confiabilidad, respuestas críticas

#### 2. Weighted (Votación Ponderada) ⚖️
- **Score**: 0.913 (22/26 correctas)
- **Color**: Morado (#8B5CF6)
- **Cómo funciona**: Pondera: Gemma 40%, Qwen 30%, Llama 25%, DeepSeek 5%
- **Pros**:
  - Considera rendimiento histórico
  - Favorece modelos consistentes
  - Muy cercano al mejor individual
- **Contras**:
  - Levemente más lento
  - Pesos fijos (no adaptativos)
- **Mejor para**: Balance entre velocidad y calidad

#### 3. Routing (Enrutamiento Inteligente) 🎯
- **Score**: 0.910 (22/26 correctas)
- **Color**: Cian (#06B6D4)
- **Cómo funciona**: Clasifica pregunta y ruta a modelos recomendados según tipo
- **Pros**:
  - Adaptativo según tipo de pregunta
  - Configs especiales para P11, P20, P25
  - Optimizado para casos específicos
- **Contras**:
  - Más complejo
  - Requiere clasificación previa
- **Mejor para**: Preguntas variadas, dominio conocido

#### 4. Consensus (Consenso con Fallback) 🤝
- **Score**: 0.909 (21/26 correctas)
- **Color**: Rosa (#EC4899)
- **Cómo funciona**: Si stdev < 0.15 usa consenso, sino fallback a gemma2:27b
- **Pros**:
  - Robusto ante respuestas conflictivas
  - Fallback a Gemma si hay divergencia
  - Conservador y seguro
- **Contras**:
  - Puede ser conservador en exceso
  - Requiere todos los modelos
- **Mejor para**: Preguntas con alta incertidumbre

---

## 💻 Desarrollo y Extensión

### Añadir Nuevo Modelo

1. **Actualizar `models_config.yaml`**:
```yaml
- name: "nuevo_modelo:latest"
  endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
  context_window: 4096
  description: "Descripción del modelo"
```

2. **Añadir perfil en `model_profiles.py`**:
```python
"nuevo_modelo:latest": {
    "name": "Nuevo Modelo",
    "provider": "Proveedor",
    "description": "...",
    "score": 0.XXX,
    "correctas": "X/26",
    "pros": [...],
    "contras": [...],
    "best_for": "...",
    "color": "#XXXXXX",
    "logo": "nuevo_modelo"
}
```

3. **Crear logo SVG** en `frontend/static/images/logos/nuevo_modelo.svg`

4. **Reiniciar servidor**

### Personalizar Animaciones

Edita `frontend/static/css/animations.css`:

```css
/* Cambiar velocidad del spinner */
.thinking-spinner {
  animation: spin 1.5s linear infinite;  /* Default: 0.8s */
}

/* Añadir nueva animación */
@keyframes tuAnimacion {
  /* ... */
}
```

### Modificar Frases de "Pensando"

Edita `frontend/static/js/app.js`:

```javascript
this.thinkingPhrases = [
  'Pensando...',
  'Tu frase personalizada...',
  // Añade más frases aquí
];
```

---

## 🐛 Troubleshooting

### Problema: "WebSocket connection failed"

**Solución**:
1. Verifica que el servidor esté corriendo en puerto 8000
2. Revisa la consola del navegador para errores específicos
3. Asegúrate de que no hay firewall bloqueando WebSockets

### Problema: "No se encontraron modelos"

**Solución**:
1. Verifica que el archivo `config/models_config.yaml` existe
2. Comprueba la conectividad con el servidor UPV
3. Revisa los logs del backend para errores de carga

### Problema: "Vector store not found"

**Solución**:
1. Verifica que existe `data/vectorstore/chroma_db/`
2. Ejecuta el script de creación del vector store si es necesario
3. Comprueba permisos de lectura en el directorio

### Problema: Animación de "pensando" no rota frases

**Solución**:
1. Abre la consola del navegador
2. Verifica que no hay errores JavaScript
3. Comprueba que el interval se está iniciando correctamente

---

## 📊 Logging y Debugging

### Logs del Backend

Todos los logs detallados aparecen en la consola del servidor:

```
📥 NUEVA PREGUNTA #1
================================================================================
Pregunta: ¿Dónde es la actividad de coles?
Modelo/Estrategia: gemma2:27b
================================================================================

   🔍 Procesando con gemma2:27b...
   
✅ RESPUESTA GENERADA #1
================================================================================
Tiempo total: 12.35s
Respuesta (limpia): La actividad de coles se realiza en...
Fuentes consultadas: 15

📊 MÉTRICAS:
   - Combined Score: 0.950
   - Faithfulness: 1.000
   - Answer Relevancy: 0.980

✓ VALIDACIÓN:
   - Válida: True
   - Confianza: 0.95
================================================================================
```

### Logs del Frontend

Abre la consola del navegador (F12) para ver:
- Conexiones WebSocket
- Mensajes recibidos/enviados
- Errores JavaScript
- Estados de la aplicación

---

## 🔮 Próximos Pasos (Roadmap)

### Corto Plazo

1. **Integración WhatsApp**
   - Usar Twilio API o WhatsApp Business API
   - Mismo backend, diferente interfaz entrada/salida
   - Mantener historial de conversaciones

2. **Historial de Conversación**
   - Guardar preguntas/respuestas en SQLite
   - Mostrar historial en sidebar
   - Exportar conversaciones

3. **Feedback de Usuario**
   - Botones 👍/👎 en cada respuesta
   - Almacenar para mejorar sistema
   - Dashboard de analytics

### Largo Plazo

4. **Comparación Lado a Lado**
   - Vista especial para comparar respuestas de todos los modelos
   - Tabla comparativa con métricas
   - Exportar comparaciones

5. **Modo Conversacional**
   - Mantener contexto de preguntas anteriores
   - Chat multi-turno
   - Memoria de sesión

6. **Personalización por Usuario**
   - Perfiles de usuario
   - Modelos favoritos
   - Configuraciones personalizadas

---

## 📝 Notas Importantes

### Seguridad

- El sistema NO almacena preguntas personales ni sensibles
- Todas las comunicaciones son efímeras (no se guardan en base de datos)
- Para producción, implementar:
  - Autenticación de usuarios
  - Rate limiting
  - Sanitización de inputs
  - HTTPS obligatorio

### Rendimiento

- **Modelo individual más rápido**: Gemma 2 27B (~12s por pregunta)
- **Estrategia ensemble más rápida**: Voting (~30s por pregunta)
- Para mejorar velocidad:
  - Usar modelo individual en lugar de ensemble
  - Implementar caché de respuestas frecuentes
  - Paralelizar generación de modelos

### Costos

- El sistema usa servidor interno UPV (sin costo API)
- Para evaluación RAGAs usa OpenAI API (solo en benchmarks, NO en chat)
- Sin límites de uso para usuarios internos

---

## 🙏 Agradecimientos

Sistema desarrollado para **DNI Voluntariado** usando:
- FastAPI (backend)
- WebSockets (comunicación en tiempo real)
- Vanilla JS (frontend)
- ChromaDB (vector store)
- Ollama (servidor de modelos LLM)

---

## 📞 Soporte

Para dudas o problemas:
1. Revisa esta documentación
2. Consulta los logs del backend
3. Verifica la consola del navegador
4. Contacta al equipo de desarrollo

**¡Disfruta del chatbot! 🚀**

