/**
 * Chatbot RAG - Aplicación Principal
 * ===================================
 * 
 * Maneja la lógica principal de la interfaz de chat:
 * - Carga de perfiles de modelos
 * - Actualización de UI según modelo seleccionado
 * - Envío de preguntas y recepción de respuestas
 * - Visualización de mensajes y fuentes
 */

class ChatApp {
  constructor() {
    this.currentModel = 'gemma2:27b';
    this.modelProfiles = {};
    this.wsClient = null;
    this.isProcessing = false;
    this.isFirstMessage = true;  // NUEVO: Para ocultar card
    
    // Frases para estado "pensando" (mejoradas)
    this.thinkingPhrases = [
      'Conectando...',
      'Buscando información...',
      'Pensando...',
      'Razonando...',
      'Analizando contexto...',
      'Procesando respuesta...',
      'Ya casi lo tengo...'
    ];
    this.thinkingIndex = 0;
    this.thinkingInterval = null;
    this.placeholderInterval = null; // Para animación de placeholder
  }

  /**
   * Inicializa la aplicación
   */
  async init() {
    console.log('🚀 Iniciando Chatbot RAG...');
    
    // Cargar perfiles de modelos
    await this.loadModelProfiles();
    
    // Inicializar WebSocket client
    this.wsClient = new ChatWebSocketClient();
    
    // Configurar event listeners
    this.setupEventListeners();
    
    // Actualizar UI con modelo por defecto
    this.updateModelInfo(this.currentModel);
    
    // Marcar área de chat como "solo bienvenida" (sin scroll)
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.classList.add('welcome-only');
    
    // Iniciar animación typewriter en placeholder
    this.startPlaceholderAnimation();
    
    console.log('✅ Chatbot inicializado correctamente');
  }

  /**
   * Carga perfiles de modelos desde el backend
   */
  async loadModelProfiles() {
    try {
      const response = await fetch('/api/models');
      const data = await response.json();
      
      this.modelProfiles = data.models;
      
      // Actualizar indicador de estado del servidor
      this.updateServerStatus(data.server_status);
      
      console.log(`✓ ${Object.keys(this.modelProfiles).length} modelos cargados`);
    } catch (error) {
      console.error('❌ Error cargando perfiles:', error);
      this.updateServerStatus('offline');
    }
  }

  /**
   * Actualiza indicador de estado del servidor
   */
  updateServerStatus(status) {
    const liveBadge = document.getElementById('live-badge');
    const liveText = liveBadge.querySelector('.live-text');
    const statusText = document.getElementById('status-text');
    
    liveBadge.className = 'live-badge';
    
    if (status === 'connected') {
      // Servidor ONLINE
      liveText.textContent = 'ONLINE';
      statusText.textContent = 'Conectado servidor UPV';
    } else {
      // Servidor OFFLINE
      liveBadge.classList.add('offline');
      liveText.textContent = 'OFFLINE';
      statusText.textContent = 'Sin conexión al servidor';
    }
  }

  /**
   * Configura event listeners
   */
  setupEventListeners() {
    // Selector de modelo en card (mantener por compatibilidad)
    const modelSelector = document.getElementById('model-selector');
    if (modelSelector) {
      modelSelector.addEventListener('change', (e) => {
        this.currentModel = e.target.value;
        this.updateModelInfo(this.currentModel);
        this.syncHeaderDropdown();
      });
    }
    
    // NUEVO: Selector de modelo en header
    const headerSelector = document.getElementById('header-model-selector');
    headerSelector.addEventListener('change', (e) => {
      this.currentModel = e.target.value;
      this.updateModelInfo(this.currentModel);
      // Sincronizar con selector del card si existe
      if (modelSelector) {
        modelSelector.value = e.target.value;
      }
    });

    // Botón de enviar
    const sendButton = document.getElementById('send-button');
    sendButton.addEventListener('click', () => this.sendQuestion());
    
    // Input de pregunta (Enter para enviar, Shift+Enter para nueva línea)
    const questionInput = document.getElementById('question-input');
    
    questionInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendQuestion();
      }
    });
    
    // Auto-resize del textarea + control de scrollbar
    questionInput.addEventListener('input', (e) => {
      e.target.style.height = 'auto';
      e.target.style.height = e.target.scrollHeight + 'px';
      
      // Detectar si necesita scroll
      this.updateScrollbarVisibility(e.target);
    });
    
    // NUEVO: Botón de info y modal
    const infoButton = document.getElementById('info-button');
    const overlay = document.getElementById('modal-overlay');
    const modalClose = document.getElementById('modal-close');
    
    infoButton.addEventListener('click', () => {
      this.showModelInfo();
    });
    
    modalClose.addEventListener('click', () => {
      this.hideModelInfo();
    });
    
    overlay.addEventListener('click', () => {
      this.hideModelInfo();
    });
  }
  
  /**
   * NUEVO: Sincroniza el selector del header con el modelo actual
   */
  syncHeaderDropdown() {
    const headerSelector = document.getElementById('header-model-selector');
    headerSelector.value = this.currentModel;
  }
  
  /**
   * NUEVO: Controla visibilidad del scrollbar en textarea
   */
  updateScrollbarVisibility(textarea) {
    // Añadir un margen de tolerancia para evitar scrollbar fantasma
    const hasScroll = textarea.scrollHeight > (textarea.clientHeight + 2);
    if (hasScroll) {
      textarea.setAttribute('data-has-scroll', 'true');
    } else {
      textarea.setAttribute('data-has-scroll', 'false');
    }
  }

  /**
   * Actualiza información del modelo seleccionado
   */
  updateModelInfo(modelKey) {
    const profile = this.modelProfiles[modelKey];
    
    if (!profile) {
      console.warn(`⚠️ Perfil no encontrado para: ${modelKey}`);
      return;
    }
    
    // Actualizar logo
    const logo = document.getElementById('current-model-logo');
    logo.src = `/static/images/logos/${profile.logo}.svg`;
    logo.alt = profile.name;
    
    // NUEVO: Sincronizar selector del header
    this.syncHeaderDropdown();
    
    // Actualizar nombre y proveedor
    document.getElementById('model-name').textContent = profile.name;
    
    const providerSpan = document.getElementById('model-provider');
    if (profile.provider) {
      providerSpan.textContent = profile.provider;
      providerSpan.style.display = 'inline-block';
    } else {
      providerSpan.style.display = 'none';
    }
    
    // Actualizar descripción
    document.getElementById('model-description').textContent = profile.description;
    
    // Actualizar stats
    document.getElementById('model-score').textContent = profile.score;
    document.getElementById('model-correct').textContent = profile.correctas;
    
    // Actualizar pros
    const prosList = document.getElementById('pros-list');
    prosList.innerHTML = profile.pros.map(pro => `<li>${pro}</li>`).join('');
    
    // Actualizar contras
    const contrasList = document.getElementById('contras-list');
    contrasList.innerHTML = profile.contras.map(contra => `<li>${contra}</li>`).join('');
    
    // Actualizar "mejor para"
    document.getElementById('best-for-text').textContent = profile.best_for;
    
    // Mostrar/ocultar "cómo funciona" (solo para ensemble)
    const howItWorksSection = document.getElementById('how-it-works-section');
    if (profile.how_it_works) {
      document.getElementById('how-it-works-text').textContent = profile.how_it_works;
      howItWorksSection.style.display = 'block';
    } else {
      howItWorksSection.style.display = 'none';
    }
    
    // Cambiar color de acento
    document.documentElement.style.setProperty('--accent-color', profile.color);
    
    console.log(`✓ Modelo actualizado: ${profile.name}`);
  }

  /**
   * Envía pregunta al backend
   */
  async sendQuestion() {
    if (this.isProcessing) {
      console.log('⏳ Ya hay una pregunta en proceso');
      return;
    }
    
    const input = document.getElementById('question-input');
    const question = input.value.trim();
    
    if (!question) {
      console.log('⚠️ Pregunta vacía');
      return;
    }
    
    // Deshabilitar input
    this.isProcessing = true;
    input.disabled = true;
    document.getElementById('send-button').disabled = true;
    
    // Limpiar input y resetear altura
    input.value = '';
    input.style.height = 'auto';
    
    // NUEVO: Ocultar card y mostrar desplegable del header al enviar primera pregunta
    if (this.isFirstMessage) {
      const card = document.querySelector('.model-selector-container');
      if (card) {
        card.classList.add('hidden');
      }
      
      // Mostrar desplegable del header con animación
      const headerModelInfo = document.getElementById('header-model-info');
      if (headerModelInfo) {
        headerModelInfo.style.display = 'flex';
        // Pequeño delay para la animación
        setTimeout(() => {
          headerModelInfo.style.opacity = '1';
        }, 50);
      }
      
      // NUEVO: Quitar clase welcome-only para permitir scroll
      const messagesContainer = document.getElementById('chat-messages');
      messagesContainer.classList.remove('welcome-only');
      
      // Remover mensaje de bienvenida DESPUÉS de quitar welcome-only
      const welcomeMsg = document.querySelector('.welcome-message');
      if (welcomeMsg) {
        welcomeMsg.style.display = 'none';
      }
      
      // Detener animación de placeholder y restaurar estático
      if (this.placeholderInterval) {
        clearTimeout(this.placeholderInterval);
        this.placeholderInterval = null;
      }
      
      // Restaurar placeholder estático
      const input = document.getElementById('question-input');
      input.placeholder = 'Escribe tu pregunta...';
      
      this.isFirstMessage = false;
    }
    
    // Añadir mensaje de usuario
    this.addMessage('user', question);
    
    // Añadir indicador de "pensando"
    const thinkingId = this.addThinkingIndicator();
    
    // Enviar pregunta via WebSocket
    await this.wsClient.sendQuestion(question, this.currentModel, {
      onStatus: (status) => {
        this.updateThinkingText(thinkingId, status);
      },
      onComplete: (response) => {
        this.handleResponse(thinkingId, response);
      },
      onError: (error) => {
        this.handleError(thinkingId, error);
      }
    });
  }

  /**
   * Añade mensaje al chat
   */
  addMessage(type, content, avatar = null) {
    const messagesContainer = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    // Burbuja del mensaje
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.textContent = content;
    messageDiv.appendChild(bubbleDiv);
    
    // NUEVO: Avatar automático para usuario
    if (type === 'user') {
      const avatarDiv = document.createElement('div');
      avatarDiv.className = 'user-avatar';
      avatarDiv.textContent = '👤';
      messageDiv.appendChild(avatarDiv);
    }
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll al final
    this.scrollToBottom();
  }

  /**
   * Añade indicador de "pensando" con animación tipo Claude Code
   */
  addThinkingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    
    const thinkingDiv = document.createElement('div');
    const thinkingId = `thinking-${Date.now()}`;
    thinkingDiv.id = thinkingId;
    thinkingDiv.className = 'message bot';
    
    thinkingDiv.innerHTML = `
      <div class="thinking-indicator">
        <div class="thinking-spinner"></div>
        <span class="thinking-text"></span>
      </div>
    `;
    
    messagesContainer.appendChild(thinkingDiv);
    this.scrollToBottom();
    
    // Iniciar animación tipo Claude Code (escribir letra por letra)
    this.thinkingIndex = 0;
    this.startTypingAnimation(thinkingDiv, thinkingId);
    
    return thinkingId;
  }
  
  /**
   * NUEVO: Animación de escritura tipo Claude Code
   */
  startTypingAnimation(thinkingDiv, thinkingId) {
    const textSpan = thinkingDiv.querySelector('.thinking-text');
    let currentPhraseIndex = 0;
    let currentCharIndex = 0;
    let isDeleting = false;
    
    const typeNextChar = () => {
      const currentPhrase = this.thinkingPhrases[currentPhraseIndex];
      
      if (!isDeleting) {
        // Escribir
        textSpan.textContent = currentPhrase.substring(0, currentCharIndex + 1);
        currentCharIndex++;
        
        if (currentCharIndex === currentPhrase.length) {
          // Pausa al completar la frase
          setTimeout(() => {
            isDeleting = true;
            this.thinkingInterval = setInterval(typeNextChar, 30);
          }, 1500);
          return;
        }
      } else {
        // Borrar
        textSpan.textContent = currentPhrase.substring(0, currentCharIndex - 1);
        currentCharIndex--;
        
        if (currentCharIndex === 0) {
          isDeleting = false;
          currentPhraseIndex = (currentPhraseIndex + 1) % this.thinkingPhrases.length;
          setTimeout(() => {
            this.thinkingInterval = setInterval(typeNextChar, 80);
          }, 200);
          return;
        }
      }
      
      this.thinkingInterval = setTimeout(typeNextChar, isDeleting ? 30 : 80);
    };
    
    // Iniciar animación
    this.thinkingInterval = setTimeout(typeNextChar, 200);
  }

  /**
   * Actualiza texto del indicador de pensando
   */
  updateThinkingText(thinkingId, status) {
    const thinkingDiv = document.getElementById(thinkingId);
    if (!thinkingDiv) return;
    
    const textSpan = thinkingDiv.querySelector('.thinking-text');
    if (!textSpan) return;
    
    const statusTexts = {
      'connecting': 'Conectando...',
      'retrieving': 'Buscando información...',
      'thinking': this.thinkingPhrases[0],  // Se rotará con interval
      'processing': 'Procesando contexto...',
      'finalizing': 'Ya casi lo tengo...'
    };
    
    textSpan.textContent = statusTexts[status] || 'Procesando...';
  }

  /**
   * Maneja respuesta completa del backend
   */
  handleResponse(thinkingId, response) {
    // Detener interval/timeout de frases (puede ser interval o timeout)
    if (this.thinkingInterval) {
      clearInterval(this.thinkingInterval);
      clearTimeout(this.thinkingInterval);
      this.thinkingInterval = null;
    }
    
    // Remover indicador de "pensando"
    const thinkingDiv = document.getElementById(thinkingId);
    if (thinkingDiv) {
      thinkingDiv.remove();
    }
    
    // Añadir respuesta del bot
    this.addBotResponse(response);
    
    // Rehabilitar input
    this.isProcessing = false;
    const input = document.getElementById('question-input');
    input.disabled = false;
    document.getElementById('send-button').disabled = false;
    input.focus();
  }

  /**
   * Maneja errores
   */
  handleError(thinkingId, error) {
    console.error('❌ Error:', error);
    
    this.handleResponse(thinkingId, {
      answer: `Lo siento, hubo un error: ${error}`,
      time: 0,
      sources: []
    });
  }

  /**
   * Añade respuesta del bot al chat
   */
  addBotResponse(response) {
    const messagesContainer = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    // Respuesta principal
    const answerP = document.createElement('p');
    answerP.textContent = response.answer;
    bubbleDiv.appendChild(answerP);
    
    // Tiempo de respuesta
    if (response.time) {
      const timeSpan = document.createElement('span');
      timeSpan.className = 'response-time';
      timeSpan.textContent = `⏱️ ${response.time.toFixed(2)}s`;
      bubbleDiv.appendChild(timeSpan);
    }
    
    // Fuentes consultadas (si existen)
    if (response.sources && response.sources.length > 0) {
      const sourcesDiv = this.createSourcesSection(response.sources);
      bubbleDiv.appendChild(sourcesDiv);
    }
    
    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);
    
    this.scrollToBottom();
  }

  /**
   * Crea sección de fuentes consultadas
   */
  createSourcesSection(sources) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'sources-section';
    
    const header = document.createElement('div');
    header.className = 'sources-header';
    
    const headerText = document.createElement('h4');
    headerText.textContent = 'Fuentes Consultadas:';
    
    // NUEVO: Icono +/- que cambia al expandir/colapsar
    const toggleIcon = document.createElement('span');
    toggleIcon.className = 'sources-toggle-icon';
    toggleIcon.textContent = '+';
    
    header.appendChild(headerText);
    header.appendChild(toggleIcon);
    sourcesDiv.appendChild(header);
    
    const sourcesList = document.createElement('div');
    sourcesList.className = 'sources-list collapsed';
    
    sources.forEach((source, idx) => {
      const sourceItem = document.createElement('div');
      sourceItem.className = 'source-item';
      
      const strongTag = document.createElement('strong');
      strongTag.textContent = `[${idx + 1}]`;
      sourceItem.appendChild(strongTag);
      
      const textP = document.createElement('p');
      textP.textContent = source.text;
      sourceItem.appendChild(textP);
      
      if (source.score) {
        const scoreSpan = document.createElement('span');
        scoreSpan.className = 'score';
        scoreSpan.textContent = `Score: ${source.score.toFixed(2)}`;
        sourceItem.appendChild(scoreSpan);
      }
      
      sourcesList.appendChild(sourceItem);
    });
    
    sourcesDiv.appendChild(sourcesList);
    
    // Toggle expandir/colapsar con cambio de icono
    header.addEventListener('click', () => {
      const isCollapsed = sourcesList.classList.toggle('collapsed');
      toggleIcon.textContent = isCollapsed ? '+' : '−';  // Usar − (menos matemático) no -
    });
    
    return sourcesDiv;
  }

  /**
   * Scroll al final del chat
   */
  scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  
  /**
   * NUEVO: Muestra modal con información del modelo actual
   */
  showModelInfo() {
    const profile = this.modelProfiles[this.currentModel];
    if (!profile) {
      console.warn(`⚠️ No se puede mostrar info del modelo: ${this.currentModel}`);
      return;
    }
    
    // Actualizar contenido del modal
    document.getElementById('modal-model-name').textContent = profile.name;
    document.getElementById('modal-model-description').textContent = profile.description;
    document.getElementById('modal-score').textContent = profile.score;
    document.getElementById('modal-correct').textContent = profile.correctas;
    
    const prosList = document.getElementById('modal-pros');
    prosList.innerHTML = profile.pros.map(pro => `<li>${pro}</li>`).join('');
    
    const contrasList = document.getElementById('modal-contras');
    contrasList.innerHTML = profile.contras.map(contra => `<li>${contra}</li>`).join('');
    
    document.getElementById('modal-best-for').textContent = profile.best_for;
    
    // Mostrar "Cómo funciona" solo para estrategias ensemble
    const howItWorksSection = document.getElementById('modal-how-it-works-section');
    if (profile.how_it_works) {
      document.getElementById('modal-how-it-works').textContent = profile.how_it_works;
      howItWorksSection.style.display = 'block';
    } else {
      howItWorksSection.style.display = 'none';
    }
    
    // Mostrar modal
    document.getElementById('modal-overlay').style.display = 'block';
    document.getElementById('model-info-modal').style.display = 'block';
  }
  
  /**
   * NUEVO: Oculta modal de información
   */
  hideModelInfo() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.getElementById('model-info-modal').style.display = 'none';
  }
  
  /**
   * NUEVO: Animación typewriter en placeholder
   */
  startPlaceholderAnimation() {
    const input = document.getElementById('question-input');
    const phrases = [
      'Escribe aquí...',
      '¿A qué hora son los desayunos?',
      '¿Cómo me apunto?',
      '¿Qué significa Para-Mira-Ayuda?',
      '¿Dónde es el punto de encuentro?',
      '¿Qué actividades hay con ancianos?'
    ];
    
    let currentPhraseIndex = 0;
    let currentCharIndex = 0;
    let isDeleting = false;
    let isFirstPhrase = true;
    
    const type = () => {
      const currentPhrase = phrases[currentPhraseIndex];
      
      if (!isDeleting) {
        // Escribir
        input.placeholder = currentPhrase.substring(0, currentCharIndex + 1);
        currentCharIndex++;
        
        if (currentCharIndex === currentPhrase.length) {
          // Pausa al completar la frase
          const pauseTime = isFirstPhrase ? 3000 : 2000; // 3s para "Escribe aquí...", 2s para el resto
          isFirstPhrase = false;
          
          this.placeholderInterval = setTimeout(() => {
            isDeleting = true;
            this.placeholderInterval = setTimeout(type, 50);
          }, pauseTime);
          return;
        }
      } else {
        // Borrar
        input.placeholder = currentPhrase.substring(0, currentCharIndex - 1);
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
}

// ============================================
// INICIALIZACIÓN
// ============================================

// Inicializar app cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  const app = new ChatApp();
  app.init();
});

