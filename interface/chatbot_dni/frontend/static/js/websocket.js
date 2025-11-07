/**
 * WebSocket Client - Manejo de conexión con el backend
 * ======================================================
 */

class ChatWebSocket {
    constructor() {
        this.ws = null;
        this.sessionId = this.generateSessionId();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket conectado');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                if (window.chatApp) {
                    window.chatApp.onConnectionChange(true);
                }
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parseando mensaje:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.isConnected = false;
                if (window.chatApp) {
                    window.chatApp.showError('Error de conexión. Intentando reconectar...');
                }
            };
            
            this.ws.onclose = () => {
                console.log('🔌 WebSocket desconectado');
                this.isConnected = false;
                if (window.chatApp) {
                    window.chatApp.onConnectionChange(false);
                }
                this.attemptReconnect();
            };
            
        } catch (error) {
            console.error('Error creando WebSocket:', error);
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reintento de conexión ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
            
            setTimeout(() => {
                this.connect();
            }, 2000 * this.reconnectAttempts);  // Backoff exponencial
        } else {
            console.error('❌ Máximo de reintentos alcanzado');
            if (window.chatApp) {
                window.chatApp.showError('No se pudo conectar con el servidor. Por favor, recarga la página.');
            }
        }
    }
    
    sendQuestion(question) {
        if (!this.isConnected || !this.ws) {
            console.error('WebSocket no conectado');
            if (window.chatApp) {
                window.chatApp.showError('No hay conexión con el servidor');
            }
            return false;
        }
        
        try {
            this.ws.send(JSON.stringify({
                question: question,
                session_id: this.sessionId
            }));
            return true;
        } catch (error) {
            console.error('Error enviando pregunta:', error);
            return false;
        }
    }
    
    handleMessage(data) {
        if (!window.chatApp) {
            console.error('ChatApp no inicializado');
            return;
        }

        switch (data.type) {
            case 'status':
                window.chatApp.updateStatus(data.status);
                // También capturar log si viene con el status
                if (data.log) {
                    window.chatApp.handleLog(data.log);
                }
                break;
            case 'log':
                // NUEVO: Capturar logs del backend
                window.chatApp.handleLog(data.log);
                break;
            case 'chunk':
                // Streaming progresivo de texto
                window.chatApp.handleChunk(data.chunk, data.is_final);
                break;
            case 'complete':
                window.chatApp.handleResponse(data.response);
                break;
            case 'error':
                window.chatApp.showError(data.error);
                break;
            default:
                console.warn('Tipo de mensaje desconocido:', data.type);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.isConnected = false;
        }
    }
}

// Instancia global
window.chatWebSocket = new ChatWebSocket();

