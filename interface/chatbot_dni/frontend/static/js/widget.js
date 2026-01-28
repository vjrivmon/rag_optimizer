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

        // Cerrar chat al hacer clic fuera
        document.addEventListener('click', (e) => this.handleOutsideClick(e));

        console.log('✅ Widget Controller inicializado');
    }

    handleOutsideClick(event) {
        // Solo procesar si el chat está abierto
        if (!this.isOpen) return;

        // Verificar si el clic fue fuera del chat y del botón
        const clickedInsideChat = this.chatWindow.contains(event.target);
        const clickedButton = this.widgetButton.contains(event.target);

        // Si el clic fue fuera del chat y no fue en el botón, cerrar
        if (!clickedInsideChat && !clickedButton) {
            this.closeChat();
            console.log('🔴 Chat cerrado por clic fuera');
        }
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        // Remover clases de cierre si existen
        this.chatWindow.classList.remove('hidden', 'closing');
        this.widgetButton.style.display = 'none';
        this.isOpen = true;

        // Cargar sugerencias dinámicas al abrir
        this.loadInitialSuggestions();

        // Focus en el input
        setTimeout(() => {
            document.getElementById('user-input').focus();
        }, 400);

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
        // Aplicar animación de cierre
        this.chatWindow.classList.add('closing');
        this.isOpen = false;

        // Esperar a que termine la animación (300ms) antes de ocultar
        setTimeout(() => {
            this.chatWindow.classList.add('hidden');
            this.chatWindow.classList.remove('closing');

            // Mostrar botón con animación suave
            this.widgetButton.style.display = 'flex';
            this.widgetButton.classList.add('show');

            // Remover clase de animación después de que termine
            setTimeout(() => {
                this.widgetButton.classList.remove('show');
            }, 400);
        }, 300);

        console.log('🔴 Chat cerrado');
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.widgetController = new WidgetController();
});

