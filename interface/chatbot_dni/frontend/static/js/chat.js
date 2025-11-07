/**
 * Chat Application - Lógica principal del chatbot con streaming
 * ============================================================
 */

class ChatApp {
    constructor() {
        this.currentQuestion = null;
        this.isProcessing = false;
        this.messageHistory = [];
        this.currentStreamingMessage = null;
        this.streamingBubble = null;
        this.hasMessages = false;
        this.sessionLogs = [];  // NUEVO: Para almacenar logs de consola
        this.currentQuestionLogs = [];  // NUEVO: Logs de la pregunta actual
        this.placeholderInterval = null;  // NUEVO: Para animación de placeholder
        this.thinkingInterval = null;  // NUEVO: Para animación de pensando
        this.thinkingPhrases = [
            'Conectando...',
            'Analizando tu pregunta...',
            'Buscando información...',
            'Procesando contexto...',
            'Generando respuesta...',
            'Verificando información...'
        ];

        // Referencias a elementos DOM
        this.messagesArea = document.getElementById('messages-area');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-button');
        this.suggestionsArea = document.getElementById('suggestions-area');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.welcomeMessage = document.getElementById('welcome-message');
        this.exportButton = document.getElementById('export-chat');

        this.init();
    }
    
    init() {
        console.log('🚀 Inicializando ChatApp...');

        // Event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = this.userInput.scrollHeight + 'px';
        });

        // Sugerencias
        this.suggestionsArea.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-chip')) {
                const question = e.target.getAttribute('data-question') || e.target.textContent;
                this.userInput.value = question;
                this.sendMessage();
            }
        });

        // Exportar conversación
        this.exportButton.addEventListener('click', () => this.exportConversation());

        // NUEVO: Iniciar animación de placeholder
        this.startPlaceholderAnimation();

        console.log('✅ ChatApp inicializado');
    }
    
    sendMessage() {
        const question = this.userInput.value.trim();

        if (!question || this.isProcessing) {
            return;
        }

        // Detener animación de placeholder si está activa
        if (this.placeholderInterval) {
            clearTimeout(this.placeholderInterval);
            this.placeholderInterval = null;
            this.userInput.placeholder = 'Escribe tu pregunta...';
        }

        // Ocultar mensaje de bienvenida
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'none';
        }

        // Resetear logs de la pregunta actual
        this.currentQuestionLogs = [];

        // Añadir mensaje del usuario
        this.addMessage(question, 'user');
        this.hasMessages = true;

        // Mostrar botón de exportar
        this.exportButton.classList.add('visible');

        // Limpiar input
        this.userInput.value = '';
        this.userInput.style.height = 'auto';

        // Deshabilitar controles
        this.setProcessing(true);

        // Guardar pregunta actual
        this.currentQuestion = question;

        // Enviar via WebSocket
        window.chatWebSocket.sendQuestion(question);
    }
    
    addMessage(text, type, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';

        // Formatear texto (links Markdown y saltos de línea)
        const formattedText = text
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>') // [texto](url) → link
            .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>') // ***texto*** → negrita+cursiva
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') // **texto** → negrita
            .replace(/\*(.+?)\*/g, '<em>$1</em>') // *texto* → cursiva
            .replace(/\n/g, '<br>');
        bubbleDiv.innerHTML = formattedText;
        
        // Si es mensaje del bot, añadir confidence badge
        if (type === 'bot' && metadata.confidence !== undefined) {
            const confidence = metadata.confidence;
            const confidenceClass = confidence > 0.7 ? 'high' : 'medium';
            const confidenceIcon = confidence > 0.7 ? '✓' : '○';
            
            const badge = document.createElement('span');
            badge.className = `confidence-badge ${confidenceClass}`;
            badge.textContent = confidenceIcon;
            bubbleDiv.appendChild(badge);
        }
        
        // Si es mensaje del bot, añadir feedback buttons
        if (type === 'bot' && metadata.responseId) {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback-buttons';
            
            const positiveBtn = document.createElement('button');
            positiveBtn.className = 'feedback-btn';
            positiveBtn.innerHTML = '👍 Útil';
            positiveBtn.onclick = () => this.sendFeedback(metadata.responseId, 'positive', positiveBtn, negativeBtn);
            
            const negativeBtn = document.createElement('button');
            negativeBtn.className = 'feedback-btn';
            negativeBtn.innerHTML = '👎 No útil';
            negativeBtn.onclick = () => this.sendFeedback(metadata.responseId, 'negative', negativeBtn, positiveBtn);
            
            feedbackDiv.appendChild(positiveBtn);
            feedbackDiv.appendChild(negativeBtn);
            bubbleDiv.appendChild(feedbackDiv);
        }
        
        // Si hay fuentes, añadirlas (colapsables)
        if (metadata.sources && metadata.sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-section';
            
            const sourcesToggle = document.createElement('div');
            sourcesToggle.className = 'sources-toggle';
            sourcesToggle.innerHTML = `
                <span class="sources-toggle-icon">▶</span>
                <span>Ver fuentes (${metadata.sources.length})</span>
            `;
            
            const sourcesList = document.createElement('div');
            sourcesList.className = 'sources-list';
            
            metadata.sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.textContent = source.text;
                sourcesList.appendChild(sourceItem);
            });
            
            sourcesToggle.onclick = () => {
                sourcesToggle.classList.toggle('expanded');
                sourcesList.classList.toggle('visible');
            };
            
            sourcesDiv.appendChild(sourcesToggle);
            sourcesDiv.appendChild(sourcesList);
            bubbleDiv.appendChild(sourcesDiv);
        }
        
        messageDiv.appendChild(bubbleDiv);
        this.messagesArea.appendChild(messageDiv);
        
        // Scroll al final
        this.scrollToBottom();
        
        // Guardar en historial
        this.messageHistory.push({
            text: text,
            type: type,
            timestamp: Date.now(),
            metadata: metadata
        });
        
        return bubbleDiv;
    }
    
    startStreamingMessage() {
        // Crear una burbuja vacía para streaming
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-bot';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.textContent = '';
        
        messageDiv.appendChild(bubbleDiv);
        this.messagesArea.appendChild(messageDiv);
        
        this.streamingBubble = bubbleDiv;
        this.currentStreamingMessage = '';
        
        this.scrollToBottom();
    }
    
    appendToStreamingMessage(chunk) {
        if (!this.streamingBubble) {
            this.startStreamingMessage();
        }

        this.currentStreamingMessage += chunk;
        // Formatear texto: links, ** → <strong>, \n → <br>
        let formattedText = this.currentStreamingMessage
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>') // [texto](url) → link
            .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>') // ***texto*** → negrita+cursiva
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') // **texto** → negrita
            .replace(/\*(.+?)\*/g, '<em>$1</em>') // *texto* → cursiva
            .replace(/\n/g, '<br>');

        this.streamingBubble.innerHTML = formattedText;

        this.scrollToBottom();
    }
    
    finishStreamingMessage(metadata = {}) {
        if (!this.streamingBubble) return;
        
        // Añadir confidence badge
        if (metadata.confidence !== undefined) {
            const confidence = metadata.confidence;
            const confidenceClass = confidence > 0.7 ? 'high' : 'medium';
            const confidenceIcon = confidence > 0.7 ? '✓' : '○';
            
            const badge = document.createElement('span');
            badge.className = `confidence-badge ${confidenceClass}`;
            badge.textContent = confidenceIcon;
            this.streamingBubble.appendChild(badge);
        }
        
        // Añadir feedback buttons
        if (metadata.responseId) {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'feedback-buttons';
            
            const positiveBtn = document.createElement('button');
            positiveBtn.className = 'feedback-btn';
            positiveBtn.innerHTML = '👍 Útil';
            positiveBtn.onclick = () => this.sendFeedback(metadata.responseId, 'positive', positiveBtn, negativeBtn);
            
            const negativeBtn = document.createElement('button');
            negativeBtn.className = 'feedback-btn';
            negativeBtn.innerHTML = '👎 No útil';
            negativeBtn.onclick = () => this.sendFeedback(metadata.responseId, 'negative', negativeBtn, positiveBtn);
            
            feedbackDiv.appendChild(positiveBtn);
            feedbackDiv.appendChild(negativeBtn);
            this.streamingBubble.appendChild(feedbackDiv);
        }
        
        // Añadir fuentes colapsables
        if (metadata.sources && metadata.sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-section';
            
            const sourcesToggle = document.createElement('div');
            sourcesToggle.className = 'sources-toggle';
            sourcesToggle.innerHTML = `
                <span class="sources-toggle-icon">▶</span>
                <span>Ver fuentes (${metadata.sources.length})</span>
            `;
            
            const sourcesList = document.createElement('div');
            sourcesList.className = 'sources-list';
            
            metadata.sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.textContent = source.text;
                sourcesList.appendChild(sourceItem);
            });
            
            sourcesToggle.onclick = () => {
                sourcesToggle.classList.toggle('expanded');
                sourcesList.classList.toggle('visible');
            };
            
            sourcesDiv.appendChild(sourcesToggle);
            sourcesDiv.appendChild(sourcesList);
            this.streamingBubble.appendChild(sourcesDiv);
        }
        
        // Guardar en historial
        this.messageHistory.push({
            text: this.currentStreamingMessage,
            type: 'bot',
            timestamp: Date.now(),
            metadata: metadata
        });
        
        // Reset
        this.streamingBubble = null;
        this.currentStreamingMessage = '';
    }
    
    async sendFeedback(responseId, feedbackType, activeBtn, otherBtn) {
        try {
            // Marcar botón como activo
            activeBtn.classList.add(feedbackType === 'positive' ? 'active-positive' : 'active-negative');
            activeBtn.disabled = true;
            otherBtn.disabled = true;

            // GUARDAR feedback en el historial local
            // ARREGLO: Buscar el mensaje correcto por responseId, no solo el último
            const message = this.messageHistory.find(msg =>
                msg.type === 'bot' &&
                msg.metadata &&
                msg.metadata.responseId === responseId
            );

            if (message) {
                message.metadata.feedback = feedbackType;  // 'positive' o 'negative'
                console.log(`📝 Feedback guardado localmente para ${responseId}: ${feedbackType}`);
            } else {
                console.warn(`⚠️ No se encontró mensaje con responseId: ${responseId}`);
            }
            
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: window.chatWebSocket.sessionId,
                    question: this.currentQuestion,
                    answer: lastMessage.text,
                    feedback_type: feedbackType,
                    confidence: lastMessage.metadata.confidence,
                    response_id: responseId
                })
            });
            
            if (response.ok) {
                console.log('✅ Feedback enviado al servidor');
            }
        } catch (error) {
            console.error('❌ Error enviando feedback:', error);
        }
    }
    
    updateStatus(status) {
        const statusTexts = {
            'connecting': 'Conectando...',
            'thinking': 'Pensando...',
            'searching': 'Buscando información...',
            'processing': 'Generando respuesta...',
            'complete': 'Completado'
        };

        if (status !== 'complete') {
            this.typingIndicator.classList.remove('hidden');

            // Detener animación anterior si existe
            if (this.thinkingInterval) {
                clearTimeout(this.thinkingInterval);
                this.thinkingInterval = null;
            }

            // Iniciar animación de escritura tipo Claude Code
            this.startThinkingAnimation(statusTexts[status] || 'Procesando...');
        } else {
            this.typingIndicator.classList.add('hidden');
            if (this.thinkingInterval) {
                clearTimeout(this.thinkingInterval);
                this.thinkingInterval = null;
            }
        }
    }

    startThinkingAnimation(initialPhrase) {
        const textSpan = this.typingIndicator.querySelector('.typing-text');
        let currentPhraseIndex = 0;
        let currentCharIndex = 0;
        let isDeleting = false;

        // Asegurar que la frase inicial esté en el array
        const phrases = [initialPhrase, ...this.thinkingPhrases.filter(p => p !== initialPhrase)];

        const typeNextChar = () => {
            const currentPhrase = phrases[currentPhraseIndex % phrases.length];

            if (!isDeleting) {
                // Escribir
                textSpan.textContent = currentPhrase.substring(0, currentCharIndex + 1);
                currentCharIndex++;

                if (currentCharIndex === currentPhrase.length) {
                    // Pausa al completar la frase
                    this.thinkingInterval = setTimeout(() => {
                        isDeleting = true;
                        this.thinkingInterval = setTimeout(typeNextChar, 30);
                    }, 1200);
                    return;
                }
            } else {
                // Borrar
                textSpan.textContent = currentPhrase.substring(0, currentCharIndex - 1);
                currentCharIndex--;

                if (currentCharIndex === 0) {
                    isDeleting = false;
                    currentPhraseIndex++;
                    this.thinkingInterval = setTimeout(typeNextChar, 200);
                    return;
                }
            }

            this.thinkingInterval = setTimeout(typeNextChar, isDeleting ? 20 : 60);
        };

        // Iniciar animación
        this.thinkingInterval = setTimeout(typeNextChar, 100);
    }
    
    handleChunk(chunk, isFinal) {
        this.appendToStreamingMessage(chunk);
        
        if (isFinal) {
            // No hacer nada aquí, esperamos el mensaje "complete"
        }
    }
    
    handleResponse(response) {
        // Ocultar typing indicator
        this.typingIndicator.classList.add('hidden');

        // Guardar logs actuales en sessionLogs con la pregunta
        if (this.currentQuestionLogs.length > 0) {
            this.sessionLogs.push({
                question: this.currentQuestion,
                answer: this.currentStreamingMessage,
                logs: [...this.currentQuestionLogs],  // Copiar logs
                timestamp: Date.now()
            });
        }

        // Finalizar mensaje streaming
        this.finishStreamingMessage({
            confidence: response.confidence,
            responseId: response.response_id,
            sources: response.sources || [],
            logs: [...this.currentQuestionLogs],  // Guardar logs en metadata
            suggestions: response.suggestions || []  // NUEVO: Guardar sugerencias en metadata
        });

        // Actualizar sugerencias
        if (response.suggestions && response.suggestions.length > 0) {
            this.updateSuggestions(response.suggestions);
        }

        // Habilitar controles
        this.setProcessing(false);
    }
    
    updateSuggestions(suggestions) {
        // Animación de salida (fade out)
        this.suggestionsArea.style.opacity = '0';
        this.suggestionsArea.style.transform = 'translateY(-10px)';

        setTimeout(() => {
            // Limpiar y agregar nuevas sugerencias
            this.suggestionsArea.innerHTML = '';

            suggestions.forEach((suggestion, index) => {
                const chip = document.createElement('button');
                chip.className = 'suggestion-chip';
                chip.setAttribute('data-question', suggestion);
                chip.textContent = suggestion;

                // Animación escalonada de entrada
                chip.style.opacity = '0';
                chip.style.transform = 'translateX(-20px)';

                this.suggestionsArea.appendChild(chip);

                // Animar entrada con delay escalonado
                setTimeout(() => {
                    chip.style.transition = 'all 0.3s ease';
                    chip.style.opacity = '1';
                    chip.style.transform = 'translateX(0)';
                }, index * 100); // 100ms delay entre cada chip
            });

            // Animación de entrada del área completa
            this.suggestionsArea.style.transition = 'all 0.3s ease';
            this.suggestionsArea.style.opacity = '1';
            this.suggestionsArea.style.transform = 'translateY(0)';
        }, 200); // Esperar a que termine la animación de salida
    }
    
    showError(errorMessage) {
        this.typingIndicator.classList.add('hidden');
        this.addMessage(`⚠️ ${errorMessage}`, 'bot');
        this.setProcessing(false);
        
        // Reset streaming si estaba activo
        this.streamingBubble = null;
        this.currentStreamingMessage = '';
    }
    
    setProcessing(processing) {
        this.isProcessing = processing;
        this.sendButton.disabled = processing;
        this.userInput.disabled = processing;
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        }, 50);
    }
    
    onConnectionChange(connected) {
        // No mostrar mensaje de conexión perdida si acabamos de conectar
        // Solo mostrar si realmente perdemos conexión después de estar conectados
        if (!connected && this.hasMessages) {
            console.log('⚠️ Conexión perdida - intentando reconectar...');
        }
    }
    
    // Función para limpiar markdown del texto (para exportación TXT plana)
    cleanMarkdown(text) {
        if (!text) return '';

        return text
            // Limpiar markdown de énfasis
            .replace(/\*\*\*(.+?)\*\*\*/g, '$1') // ***texto*** → texto
            .replace(/\*\*(.+?)\*\*/g, '$1')     // **texto** → texto
            .replace(/\*(.+?)\*/g, '$1')         // *texto* → texto
            // Limpiar bullets y listas
            .replace(/^[•\-\*]\s+/gm, '')        // • texto → texto
            // Limpiar HTML si existe
            .replace(/<br\s*\/?>/gi, '\n')       // <br> → \n
            .replace(/<\/?strong>/gi, '')        // <strong> → vacío
            .replace(/<\/?em>/gi, '')            // <em> → vacío
            .trim();
    }
    
    exportConversation() {
        if (this.messageHistory.length === 0) {
            alert('No hay conversación para exportar');
            return;
        }

        try {
            // Crear contenido del archivo
            let content = '='.repeat(80) + '\n';
            content += 'CONVERSACION CON ASISTENTE DNI\n';
            content += '='.repeat(80) + '\n\n';
            content += `Fecha: ${new Date().toLocaleString('es-ES')}\n`;
            content += `Sesion: ${window.chatWebSocket?.sessionId || 'Sin sesión'}\n\n`;
            content += '='.repeat(80) + '\n\n';

            this.messageHistory.forEach((msg, index) => {
                const role = msg.type === 'user' ? 'USUARIO' : 'ASISTENTE DNI';
                const timestamp = new Date(msg.timestamp).toLocaleTimeString('es-ES');

                content += `[${timestamp}] ${role}:\n`;
                // Limpiar markdown y HTML para texto plano
                const cleanText = this.cleanMarkdown(msg.text);
                content += cleanText + '\n\n';

                // Añadir metadata para mensajes del bot
                if (msg.type === 'bot' && msg.metadata) {
                    // Confidence
                    if (msg.metadata.confidence !== undefined) {
                        content += `  Confidence: ${(msg.metadata.confidence * 100).toFixed(0)}%\n`;
                    }

                    // Feedback REAL si existe
                    if (msg.metadata.feedback) {
                        const feedbackText = msg.metadata.feedback === 'positive' ? 'Util' : 'No util';
                        content += `  Feedback: ${feedbackText}\n`;
                    } else {
                        content += `  Feedback: No proporcionado\n`;
                    }

                    // NUEVO: Añadir logs de consola si existen
                    if (msg.metadata.logs && msg.metadata.logs.length > 0) {
                        content += '\n  --- LOGS DEL PROCESAMIENTO ---\n';
                        msg.metadata.logs.forEach(log => {
                            const logTimestamp = new Date(log.timestamp).toLocaleTimeString('es-ES');
                            content += `  [${logTimestamp}] ${log.text}\n`;
                        });
                        content += '  ' + '-'.repeat(30) + '\n';
                    }

                    // NUEVO: Añadir sugerencias si existen
                    if (msg.metadata.suggestions && msg.metadata.suggestions.length > 0) {
                        content += '\n  --- SUGERENCIAS PROPUESTAS ---\n';
                        msg.metadata.suggestions.forEach((suggestion, idx) => {
                            content += `  ${idx + 1}. ${suggestion}\n`;
                        });
                        content += '  ' + '-'.repeat(30) + '\n';
                    }

                    content += '\n';
                }

                content += '-'.repeat(80) + '\n\n';
            });

            content += '='.repeat(80) + '\n';
            content += 'Fin de la conversacion\n';
            content += '='.repeat(80) + '\n';

            // Crear blob y descargar con BOM UTF-8 para mejor compatibilidad
            const BOM = '\uFEFF';
            const blob = new Blob([BOM + content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `conversacion-dni-${Date.now()}.txt`;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();

            // Limpiar después de un delay para asegurar descarga
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);

            console.log('✅ Conversación exportada correctamente');

        } catch (error) {
            console.error('❌ Error al exportar conversación:', error);
            alert('Error al exportar la conversación. Por favor, inténtalo de nuevo.');
        }
    }

    startPlaceholderAnimation() {
        const phrases = [
            'Escribe tu pregunta aquí...',
            '¿A qué hora son los desayunos?',
            '¿Cómo me apunto?',
            '¿Qué significa PARA.MIRA.AYUDA?',
            '¿Dónde es el punto de encuentro?',
            '¿Qué actividades hay en residencias?'
        ];

        let currentPhraseIndex = 0;
        let currentCharIndex = 0;
        let isDeleting = false;
        let isFirstPhrase = true;

        const type = () => {
            const currentPhrase = phrases[currentPhraseIndex];

            if (!isDeleting) {
                // Escribir
                this.userInput.placeholder = currentPhrase.substring(0, currentCharIndex + 1);
                currentCharIndex++;

                if (currentCharIndex === currentPhrase.length) {
                    // Pausa al completar la frase
                    const pauseTime = isFirstPhrase ? 3000 : 2000;
                    isFirstPhrase = false;

                    this.placeholderInterval = setTimeout(() => {
                        isDeleting = true;
                        this.placeholderInterval = setTimeout(type, 50);
                    }, pauseTime);
                    return;
                }
            } else {
                // Borrar
                this.userInput.placeholder = currentPhrase.substring(0, currentCharIndex - 1);
                currentCharIndex--;

                if (currentCharIndex === 0) {
                    isDeleting = false;
                    currentPhraseIndex = (currentPhraseIndex + 1) % phrases.length;
                    this.placeholderInterval = setTimeout(type, 500);
                    return;
                }
            }

            this.placeholderInterval = setTimeout(type, isDeleting ? 30 : 80);
        };

        // Iniciar animación
        this.placeholderInterval = setTimeout(type, 1000);
    }

    handleLog(log) {
        // NUEVO: Capturar logs del backend
        this.currentQuestionLogs.push({
            text: log,
            timestamp: Date.now()
        });
        console.log(`📝 ${log}`);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
