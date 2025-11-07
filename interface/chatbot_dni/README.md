# 💙 Chatbot DNI - Guía de Usuario

Bienvenido al asistente virtual de **DNI (Damos Nuestra Ilusión)**, tu compañero para conocer todo sobre nuestros proyectos de voluntariado en Valencia.

## 🚀 Inicio Rápido

### 1. Iniciar el Chatbot

Ejecuta el script de lanzamiento:

```bash
./scripts/run_chatbot.sh
```

El servidor se iniciará en `http://localhost:8000`

### 2. Abrir en el Navegador

Abre tu navegador favorito y ve a:
- **Servidor local**: http://localhost:8000
- O simplemente ejecuta: `xdg-open http://localhost:8000` (Linux)

### 3. ¡Empieza a Chatear!

1. Verás un **corazón azul flotante** 💙 en la esquina inferior derecha
2. **Click en el corazón** para abrir el chat
3. Escribe tu pregunta o selecciona una de las **sugerencias**
4. ¡Recibe respuestas instantáneas con información actualizada!

---

## ✨ Funcionalidades

### 🤖 Chat Inteligente

- **Respuestas en tiempo real**: Streaming de respuestas con estados visuales
- **Contexto conversacional**: El chatbot recuerda tu conversación
- **Sugerencias dinámicas**: Te propone preguntas relacionadas tras cada respuesta
- **Clasificación automática**: Detecta saludos, despedidas y agradecimientos

### 📊 Confidence Scores

Cada respuesta incluye un **indicador de confianza**:
- ✓ **Alta confianza** (verde): La respuesta es muy confiable
- ○ **Media confianza** (amarillo): La respuesta es parcial o aproximada

### 👍👎 Feedback

Después de cada respuesta del bot, puedes dar feedback:
- **👍 Útil**: Si la respuesta te ayudó
- **👎 No útil**: Si la respuesta no fue satisfactoria

Tu feedback nos ayuda a mejorar continuamente.

### 💬 Tipos de Preguntas

Puedes preguntar sobre:

#### **¿Qué es DNI?**
- Filosofía y valores de DNI
- Historia de la asociación
- Impacto social

#### **Proyectos de Voluntariado**
- **Desayunos Solidarios**: Repartos de comida
- **Abuelitos (RESIS)**: Visitas a residencias
- **Refuerzo Escolar (COLES)**: Apoyo a niños
- **Kayak Solidario**: Recogida de plásticos
- **Rehabilitar Valencia**: Ayuda post-DANA

#### **Cómo Participar**
- Requisitos para ser voluntario
- Cómo apuntarse a las actividades
- Proceso de inscripción

#### **Horarios y Ubicaciones**
- Cuándo son las actividades
- Dónde quedamos
- Duración de cada proyecto

#### **Contacto**
- WhatsApp: 962 025 978 / 647 440 275
- Instagram: @dnivalenciaa
- Cómo hacer donaciones

---

## 🎨 Interfaz de Usuario

### Botón Flotante 💙

- **Ubicación**: Esquina inferior derecha
- **Animación**: Pulso suave para llamar tu atención
- **Click**: Abre la ventana de chat

### Ventana de Chat

- **Header azul**: Con el logo de DNI y botón cerrar
- **Área de mensajes**: Tus preguntas (azul) y respuestas del bot (gris)
- **Sugerencias**: Chips con preguntas recomendadas
- **Input**: Escribe tu pregunta aquí

### Responsive Design

- **Desktop**: Ventana de 400x600px flotante
- **Mobile**: Pantalla completa para mejor experiencia
- **Tablet**: Adaptación automática

---

## 💡 Consejos de Uso

### ✅ Buenas Prácticas

1. **Sé específico**: "¿Cuándo son los desayunos solidarios?" es mejor que "¿cuándo?"
2. **Una pregunta a la vez**: El chatbot responde mejor con preguntas claras
3. **Usa sugerencias**: Las preguntas sugeridas están optimizadas
4. **Da feedback**: Ayuda al chatbot a mejorar

### ⚠️ Limitaciones

- El chatbot **solo sabe sobre DNI Voluntariado**
- Para temas fuera de scope, te redirigirá a contacto humano
- Las respuestas se basan en documentación actualizada a 2025

---

## 🔧 Solución de Problemas

### "No hay conexión con el servidor"

1. Verifica que el servidor esté corriendo: `./scripts/run_chatbot.sh`
2. Comprueba que estés en la red UPV o con VPN conectada
3. Recarga la página (F5)

### "Error procesando pregunta"

1. Intenta reformular tu pregunta
2. Verifica que no haya caracteres especiales raros
3. Si persiste, contacta soporte técnico

### El chat no se abre

1. Actualiza tu navegador a la última versión
2. Prueba en Chrome/Firefox (navegadores compatibles)
3. Limpia caché y cookies

### Respuestas lentas

- Es normal que algunas preguntas complejas tarden 2-5 segundos
- El indicador "Pensando..." te muestra que el chatbot está trabajando
- Si tarda más de 10s, puede haber un problema de red

---

## 📱 Contacto y Soporte

Si tienes problemas técnicos o sugerencias:

- **Email técnico**: [tu-email@upv.es]
- **WhatsApp DNI**: 962 025 978 / 647 440 275
- **Instagram**: @dnivalenciaa

---

## 🎓 Tecnología

Este chatbot está potenciado por:
- **gemma2:27b**: Modelo LLM de última generación
- **RAG Avanzado**: Recuperación de información con ChromaDB
- **Intent Classification**: Detección inteligente de intenciones
- **Conversational Memory**: Contexto persistente por sesión

---

**¡Disfruta conversando con el asistente DNI! 💙**

*Para. Mira. Ayuda.*

