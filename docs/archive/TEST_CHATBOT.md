# 🧪 Guía de Testing - Chatbot RAG Interactivo

## ✅ Lista de Verificación Completa

Sigue esta lista para probar sistemáticamente todas las funcionalidades del chatbot.

---

## 📋 Pruebas Básicas

### 1. Lanzamiento del Servidor

```bash
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
./run_chatbot.sh
```

**Verificar**:
- [ ] El servidor inicia sin errores
- [ ] Aparece mensaje "SISTEMA LISTO"
- [ ] Muestra "Servidor disponible en http://localhost:8000"
- [ ] No hay errores de importación

### 2. Carga de la Interfaz

1. Abrir navegador en `http://localhost:8000`

**Verificar**:
- [ ] La página carga correctamente
- [ ] Header visible con logo y estado de conexión
- [ ] Selector de modelo presente
- [ ] Card de información del modelo visible
- [ ] Área de chat con mensaje de bienvenida
- [ ] Input de pregunta funcional

### 3. Estado de Conexión

**Verificar en header**:
- [ ] Indicador de estado (bolita verde/amarilla/roja)
- [ ] Texto "Conectado servidor UPV" o equivalente
- [ ] Logo del modelo actual (Gemma por defecto)

---

## 🎯 Pruebas de Modelos Individuales

### Test 1: Gemma 2 27B (Por Defecto)

1. Seleccionar "Gemma 2 27B" en el dropdown
2. Hacer pregunta: **"¿Dónde es la actividad de coles?"**

**Verificar**:
- [ ] Card muestra info de Gemma (score 0.915, 22/26 correctas)
- [ ] Pros: 4 items visibles
- [ ] Contras: 2 items visibles  
- [ ] Color de acento cambia a azul (#4285F4)
- [ ] Logo es el círculo azul con "G"

**Verificar durante generación**:
- [ ] Aparece indicador de "pensando" con spinner
- [ ] Texto cambia: "Conectando..." → "Buscando información..." → "Pensando..."
- [ ] Frases rotan ("Razonando...", "Analizando...", etc.)
- [ ] Aparece "Ya casi lo tengo..." al final

**Verificar respuesta**:
- [ ] Indicador de "pensando" desaparece
- [ ] Respuesta aparece en burbuja blanca
- [ ] Menciona "CEIP Antonio Ferrandis de la Coma"
- [ ] Tiempo mostrado (ej: "⏱️ 12.5s")
- [ ] Sección "Fuentes Consultadas" presente

**Verificar en consola backend**:
```
📥 NUEVA PREGUNTA #1
Pregunta: ¿Dónde es la actividad de coles?
Modelo/Estrategia: gemma2:27b
✅ RESPUESTA GENERADA #1
Tiempo total: XX.XXs
📊 MÉTRICAS:
   - Combined Score: X.XXX
✓ VALIDACIÓN:
   - Válida: True
```

### Test 2: Llama 3.3 70B

1. Cambiar a "Llama 3.3 70B"
2. Hacer pregunta: **"¿Qué días se hace la actividad de resis?"**

**Verificar**:
- [ ] Card actualiza a info de Llama
- [ ] Color cambia a morado (#9333EA)
- [ ] Logo cambia a "L" morado
- [ ] Respuesta es coherente y detallada

### Test 3: Qwen 3 32B

1. Cambiar a "Qwen 3 32B"
2. Hacer pregunta: **"¿A qué hora son los desayunos solidarios?"**

**Verificar**:
- [ ] Color cambia a rojo (#EF4444)
- [ ] Card muestra pros/contras específicos
- [ ] Respuesta NO está en inglés (debería ser en español)

### Test 4: DeepSeek R1

1. Cambiar a "DeepSeek R1"
2. Hacer pregunta: **"¿Cuánto dura la actividad de coles?"**

**Verificar**:
- [ ] Color cambia a verde (#10B981)
- [ ] Respuesta NO contiene tags `<think>` (deben estar limpios)
- [ ] Logging muestra proceso de limpieza

---

## 🎲 Pruebas de Estrategias Ensemble

### Test 5: Ensemble Voting

1. Seleccionar "🎲 Ensemble - Voting"
2. Hacer pregunta: **"¿Dónde es la actividad de coles?"** (misma que Test 1)

**Verificar**:
- [ ] Card muestra icon 🗳️
- [ ] Sección "Cómo funciona" visible
- [ ] Color naranja (#F59E0B)
- [ ] Tarda más tiempo (~30-45s)
- [ ] Respuesta similar a Gemma (debería seleccionar la mejor)

**Verificar en consola**:
```
🎲 Procesando con ensemble (voting)...
📝 Generando respuestas con 4 modelos...
✓ 4 respuestas individuales generadas
🎯 Aplicando estrategia voting...
✓ Estrategia voting aplicada
📌 Respuesta seleccionada de: gemma2:27b
```

### Test 6: Ensemble Weighted

1. Seleccionar "🎲 Ensemble - Weighted"
2. Hacer pregunta diferente

**Verificar**:
- [ ] Color morado (#8B5CF6)
- [ ] Texto "Cómo funciona" menciona pesos (Gemma 40%, etc.)

### Test 7: Ensemble Routing

1. Seleccionar "🎲 Ensemble - Routing"
2. Probar con P25: **"¿Qué significa Para-Mira-Ayuda?"**

**Verificar**:
- [ ] Color cian (#06B6D4)
- [ ] Respuesta maneja pregunta filosófica
- [ ] Logging muestra clasificación de pregunta

### Test 8: Ensemble Consensus

1. Seleccionar "🎲 Ensemble - Consensus"
2. Hacer pregunta

**Verificar**:
- [ ] Color rosa (#EC4899)
- [ ] Estrategia usa consenso o fallback según divergencia

---

## 💬 Pruebas de Interfaz

### Test 9: Fuentes Consultadas

1. Hacer cualquier pregunta
2. Esperar respuesta
3. Click en "Fuentes Consultadas:"

**Verificar**:
- [ ] Sección se expande/colapsa
- [ ] Muestra chunks con formato `[1]`, `[2]`, etc.
- [ ] Cada chunk tiene texto truncado (máx 500 chars)
- [ ] Algunos muestran score de similitud

### Test 10: Input de Pregunta

**Verificar**:
- [ ] Textarea se autoajusta al escribir
- [ ] Enter envía pregunta
- [ ] Shift+Enter crea nueva línea
- [ ] Placeholder "Escribe aquí..." visible
- [ ] Botón de enviar (avión de papel) responde a hover
- [ ] Input se deshabilita durante procesamiento

### Test 11: Área de Chat

**Verificar**:
- [ ] Scroll automático al recibir mensajes
- [ ] Mensaje de bienvenida desaparece al enviar primera pregunta
- [ ] Burbujas de usuario alineadas a la derecha (gris)
- [ ] Burbujas de bot alineadas a la izquierda (blanco con borde)
- [ ] Animación "slideIn" al aparecer mensajes

### Test 12: Card de Modelo

**Verificar**:
- [ ] Nombre del modelo actualiza
- [ ] Proveedor visible (Google, Meta, etc.)
- [ ] Stats (Score y Correctas) actualizan
- [ ] Pros tienen checkmark (✓)
- [ ] Contras tienen X (✗)
- [ ] "Mejor para" actualiza
- [ ] "Cómo funciona" solo visible para ensemble

---

## 📱 Pruebas Responsive (Mobile)

### Test 13: Vista Móvil

1. Abrir DevTools (F12)
2. Activar modo responsive
3. Seleccionar iPhone o Android

**Verificar**:
- [ ] Container max-width 480px
- [ ] Header compacto pero legible
- [ ] Selector dropdown usable
- [ ] Card de info no se desborda
- [ ] Burbujas de chat 80% max-width
- [ ] Input y botón de envío accesibles
- [ ] No hay scroll horizontal

### Test 14: Vista Tablet

Cambiar a iPad (768px+)

**Verificar**:
- [ ] Container max-width 800px
- [ ] Border y border-radius visibles
- [ ] Sombra del container
- [ ] Burbujas de chat 65% max-width

---

## ⚠️ Pruebas de Errores

### Test 15: Pregunta Vacía

1. Click en enviar sin escribir nada

**Verificar**:
- [ ] Nada sucede (no se envía)
- [ ] No hay errores en consola

### Test 16: Servidor Desconectado

1. Detener servidor (Ctrl+C)
2. Intentar enviar pregunta

**Verificar**:
- [ ] Indicador muestra estado offline (bolita roja)
- [ ] Mensaje de error amigable al usuario
- [ ] Consola del navegador muestra error de conexión

### Test 17: Pregunta Muy Larga

1. Escribir pregunta de >500 caracteres

**Verificar**:
- [ ] Input limita a 500 caracteres (maxlength)
- [ ] No se permiten más caracteres

### Test 18: WebSocket Interrumpido

1. Enviar pregunta
2. Detener servidor mientras procesa
3. Reiniciar servidor

**Verificar**:
- [ ] Frontend maneja desconexión
- [ ] Mensaje de error mostrado
- [ ] Posibilidad de reintentar

---

## 🔍 Pruebas de Preguntas del Benchmark

### Test 19: Preguntas Críticas

Probar con cada modelo las 3 preguntas problemáticas:

**P11**: "¿Dónde es la actividad de coles?"
- [ ] Gemma responde correctamente
- [ ] Llama responde correctamente
- [ ] Qwen puede tener problemas
- [ ] DeepSeek puede fallar

**P20**: "¿Dónde es la actividad de resis?"
- [ ] Todos deberían responder "La Acollida"
- [ ] Verificar mención de "calle Crevillente 22"

**P25**: "¿Qué significa Para-Mira-Ayuda?"
- [ ] Respuesta incluye explicación filosófica
- [ ] No solo dice "PARA. MIRA. AYUDA."

### Test 20: Preguntas Variadas

- "¿Qué es DNI Voluntariado?"
- "¿Cuántos proyectos hay?"
- "¿Cómo me apunto?"
- "¿Qué días son los desayunos?"
- "¿Quién puede participar?"

**Verificar**:
- [ ] Respuestas coherentes
- [ ] Fuentes citadas correctamente
- [ ] Tiempo razonable (<30s para individuales)

---

## 📊 Pruebas de Rendimiento

### Test 21: Velocidad por Modelo

Medir tiempo promedio de cada modelo con la misma pregunta:

| Modelo | Tiempo Esperado |
|--------|----------------|
| Gemma 2 27B | ~12-15s |
| Llama 3.3 70B | ~20-25s |
| Qwen 3 32B | ~15-20s |
| DeepSeek R1 | ~18-22s |

**Verificar**:
- [ ] Tiempos dentro del rango esperado
- [ ] No hay timeouts

### Test 22: Velocidad Ensemble

| Estrategia | Tiempo Esperado |
|-----------|----------------|
| Voting | ~30-40s |
| Weighted | ~30-40s |
| Routing | ~25-35s |
| Consensus | ~30-40s |

**Verificar**:
- [ ] Ensemble siempre más lento (genera con 4 modelos)
- [ ] Routing potencialmente más rápido (usa menos modelos)

---

## 🎨 Pruebas Visuales

### Test 23: Animaciones

**Verificar**:
- [ ] Spinner rota suavemente
- [ ] Texto de "pensando" hace fade in/out
- [ ] Mensajes hacen slideIn al aparecer
- [ ] Indicador de estado pulsa (verde)
- [ ] Botón de enviar hace hover effect
- [ ] Card de modelo hace transición de color

### Test 24: Colores

Cambiar entre modelos y verificar:

- [ ] Gemma: Azul (#4285F4)
- [ ] Llama: Morado (#9333EA)
- [ ] Qwen: Rojo (#EF4444)
- [ ] DeepSeek: Verde (#10B981)
- [ ] Voting: Naranja (#F59E0B)
- [ ] Weighted: Morado (#8B5CF6)
- [ ] Routing: Cian (#06B6D4)
- [ ] Consensus: Rosa (#EC4899)

---

## 📝 Checklist Final

### Frontend
- [ ] Todos los elementos visuales correctos
- [ ] Sin errores en consola del navegador
- [ ] Animaciones suaves
- [ ] Responsive en móvil y desktop
- [ ] Todos los logos cargan

### Backend
- [ ] Servidor inicia sin errores
- [ ] 4 modelos cargados correctamente
- [ ] Ensemble engine inicializado
- [ ] WebSocket funciona correctamente
- [ ] Logging detallado en consola

### Funcionalidad
- [ ] 4 modelos individuales funcionan
- [ ] 4 estrategias ensemble funcionan
- [ ] Cambio de modelo actualiza UI
- [ ] Fuentes se muestran correctamente
- [ ] Tiempos de respuesta razonables

### Calidad
- [ ] Respuestas son coherentes
- [ ] Tags `<think>` limpios
- [ ] Fuentes relevantes citadas
- [ ] Métricas loggeadas correctamente

---

## 🎯 Resultado Esperado

Si todas las pruebas pasan:

✅ **SISTEMA COMPLETAMENTE FUNCIONAL**

Puedes considerarlo listo para:
- Demostración a usuarios
- Testing interno con equipo
- Preparación para integración WhatsApp
- Despliegue en producción (con consideraciones de seguridad)

---

## 📞 Si Algo Falla

1. **Revisar logs del backend** en la terminal del servidor
2. **Revisar consola del navegador** (F12)
3. **Verificar conectividad** con servidor UPV
4. **Consultar** `CHATBOT_README.md` sección Troubleshooting
5. **Reiniciar** servidor y navegador

---

**¡Éxito en las pruebas! 🚀**

