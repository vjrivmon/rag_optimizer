/**
 * WebSocket Client - Chatbot RAG
 * ===============================
 * 
 * Cliente WebSocket para comunicación en tiempo real con el backend.
 * Maneja envío de preguntas y recepción de estados y respuestas.
 */

class ChatWebSocketClient {
  constructor() {
    this.ws = null;
    this.messageHandlers = {};
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
  }

  /**
   * Envía una pregunta al backend y maneja la respuesta
   * 
   * @param {string} question - Pregunta del usuario
   * @param {string} model - Modelo o estrategia seleccionada
   * @param {Object} callbacks - Callbacks para estados y respuesta
   *   - onStatus: (status) => void
   *   - onComplete: (response) => void
   *   - onError: (error) => void
   */
  async sendQuestion(question, model, callbacks) {
    // Determinar URL del WebSocket (desarrollo o producción)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
    
    console.log(`🔌 Conectando WebSocket: ${wsUrl}`);
    
    try {
      // Crear conexión WebSocket
      this.ws = new WebSocket(wsUrl);
      
      // Handler: Conexión abierta
      this.ws.onopen = () => {
        console.log('✅ WebSocket conectado');
        this.reconnectAttempts = 0;
        
        // Enviar pregunta
        const payload = {
          question: question,
          model: model
        };
        
        console.log('📤 Enviando pregunta:', payload);
        this.ws.send(JSON.stringify(payload));
      };
      
      // Handler: Mensaje recibido
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📥 Mensaje recibido:', data.type);
          
          if (data.type === 'status') {
            // Estado intermedio (conectando, pensando, etc.)
            if (callbacks.onStatus) {
              callbacks.onStatus(data.status);
            }
          } else if (data.type === 'complete') {
            // Respuesta completa
            console.log('✅ Respuesta completa recibida');
            if (callbacks.onComplete) {
              callbacks.onComplete(data.response);
            }
            this.ws.close();
          } else if (data.type === 'error') {
            // Error
            console.error('❌ Error del servidor:', data.error);
            if (callbacks.onError) {
              callbacks.onError(data.error);
            } else if (callbacks.onComplete) {
              // Fallback: enviar respuesta de error
              callbacks.onComplete({
                answer: `Lo siento, hubo un error al procesar tu pregunta: ${data.error}`,
                time: 0,
                sources: []
              });
            }
            this.ws.close();
          }
        } catch (error) {
          console.error('❌ Error parseando mensaje:', error);
        }
      };
      
      // Handler: Error
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        
        if (callbacks.onError) {
          callbacks.onError('Error de conexión con el servidor');
        }
      };
      
      // Handler: Conexión cerrada
      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket cerrado', event.code, event.reason);
        
        // Intentar reconectar si fue cierre inesperado
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`🔄 Intentando reconectar (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
          
          setTimeout(() => {
            if (callbacks.onError) {
              callbacks.onError('Conexión perdida. Reintentando...');
            }
          }, 1000);
        }
      };
      
    } catch (error) {
      console.error('❌ Error creando WebSocket:', error);
      
      if (callbacks.onError) {
        callbacks.onError('No se pudo conectar con el servidor');
      } else if (callbacks.onComplete) {
        callbacks.onComplete({
          answer: 'Lo siento, no se pudo conectar con el servidor. Por favor, verifica tu conexión.',
          time: 0,
          sources: []
        });
      }
    }
  }

  /**
   * Cierra la conexión WebSocket
   */
  close() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.close();
    }
  }

  /**
   * Verifica si hay una conexión activa
   * @returns {boolean}
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

// Exportar para uso en app.js
window.ChatWebSocketClient = ChatWebSocketClient;

