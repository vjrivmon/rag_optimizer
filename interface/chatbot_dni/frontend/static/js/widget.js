/**
 * Widget Controller - Manejo del botón flotante
 * ==============================================
 */

class WidgetController {
    constructor() {
        this.widgetButton = document.getElementById('chat-widget-button');
        this.chatWindow = document.getElementById('chat-window');
        this.closeButton = document.getElementById('close-chat');
        this.isOpen = false;
        
        this.init();
    }
    
    init() {
        console.log('🔵 Inicializando Widget Controller...');
        
        // Event listeners
        this.widgetButton.addEventListener('click', () => this.toggleChat());
        this.closeButton.addEventListener('click', () => this.closeChat());
        
        // Conectar WebSocket cuando se abre por primera vez
        this.widgetButton.addEventListener('click', () => {
            if (!window.chatWebSocket.isConnected) {
                window.chatWebSocket.connect();
            }
        }, { once: true });
        
        console.log('✅ Widget Controller inicializado');
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        this.chatWindow.classList.remove('hidden');
        this.widgetButton.style.display = 'none';
        this.isOpen = true;

        // Cargar sugerencias dinámicas al abrir
        this.loadInitialSuggestions();

        // Focus en el input
        setTimeout(() => {
            document.getElementById('user-input').focus();
        }, 300);

        console.log('💬 Chat abierto');
    }

    async loadInitialSuggestions() {
        try {
            const response = await fetch('/api/suggestions');
            if (response.ok) {
                const data = await response.json();
                if (data.suggestions && window.chatController) {
                    window.chatController.updateSuggestions(data.suggestions);
                    console.log('💡 Sugerencias iniciales cargadas:', data.suggestions.length);
                }
            }
        } catch (error) {
            console.warn('⚠️ No se pudieron cargar sugerencias iniciales:', error);
            // No es crítico, el chat funciona igual con las sugerencias hardcodeadas
        }
    }
    
    closeChat() {
        this.chatWindow.classList.add('hidden');
        this.widgetButton.style.display = 'flex';
        this.isOpen = false;
        
        console.log('🔴 Chat cerrado');
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.widgetController = new WidgetController();
});

