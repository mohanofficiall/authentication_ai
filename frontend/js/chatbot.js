/* Chatbot Widget */
const ChatbotWidget = {
    init: function () {
        this.createWidget();
        this.attachListeners();
    },

    createWidget: function () {
        const widget = document.createElement('div');
        widget.id = 'chatbot-widget';
        widget.innerHTML = `
            <div id="chatbot-toggle" class="fade-in-up" onclick="ChatbotWidget.toggleChat()">
                <i class="fas fa-robot"></i>
            </div>
            <div id="chatbot-window" style="display: none;">
                <div id="chatbot-header">
                    <div class="flex items-center gap-3">
                        <i class="fas fa-robot" style="font-size: 1.5rem; color: var(--primary);"></i>
                        <div>
                            <span style="display: block;">Attendo AI Assistant</span>
                            <small style="font-size: 0.75rem; color: var(--text-muted); font-weight: 400;">Ask about subjects or attendance</small>
                        </div>
                    </div>
                    <button onclick="ChatbotWidget.toggleChat()" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: white; cursor: pointer; padding: 0.5rem 1rem; border-radius: var(--radius-md); display: flex; align-items: center; gap: 0.5rem; transition: all 0.3s;" onmouseover="this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.background='rgba(255,255,255,0.05)'">
                        <i class="fas fa-arrow-left"></i> Exit Assistant
                    </button>
                </div>
                <div id="chatbot-messages">
                    <div class="message bot-message">
                        Hello! I'm your AI attendance assistant. How can I help you today?
                    </div>
                </div>
                <div id="chatbot-input-area">
                    <input type="text" id="chatbot-input" placeholder="Type a message..." onkeypress="ChatbotWidget.handleKeyPress(event)">
                    <button onclick="ChatbotWidget.sendMessage()">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            #chatbot-widget {
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                z-index: 9999;
                font-family: var(--font-primary);
            }
            #chatbot-toggle {
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: var(--shadow-xl);
                color: white;
                font-size: 1.5rem;
                transition: transform 0.3s ease;
            }
            #chatbot-toggle:hover {
                transform: scale(1.1);
            }
            #chatbot-window {
                position: fixed;
                top: 0;
                right: 0;
                width: 50vw;
                height: 100vh;
                background: rgba(15, 23, 42, 0.98);
                backdrop-filter: blur(20px);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                z-index: 10000;
                border: none;
                border-left: 1px solid rgba(255,255,255,0.1);
                animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: -10px 0 30px rgba(0,0,0,0.5);
            }
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @media (max-width: 768px) {
                #chatbot-window {
                    width: 100vw;
                }
            }
            #chatbot-header {
                background: rgba(99, 102, 241, 0.1);
                padding: 1.25rem 1.5rem;
                color: white;
                font-weight: 700;
                font-size: 1.1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            #chatbot-messages {
                flex: 1;
                padding: 1.5rem;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 1.25rem;
                width: 100%;
            }
            .message {
                padding: 1rem 1.5rem;
                border-radius: 1.5rem;
                max-width: 80%;
                font-size: 1rem;
                line-height: 1.6;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .bot-message {
                background: rgba(255, 255, 255, 0.05);
                color: #e2e8f0;
                align-self: flex-start;
                border-bottom-left-radius: 0.25rem;
                border: 1px solid rgba(255,255,255,0.1);
            }
            .user-message {
                background: var(--primary);
                color: white;
                align-self: flex-end;
                border-bottom-right-radius: 0.25rem;
            }
            #chatbot-input-area {
                padding: 1.5rem;
                background: rgba(15, 23, 42, 0.8);
                border-top: 1px solid rgba(255,255,255,0.1);
                display: flex;
                gap: 1rem;
                width: 100%;
                align-items: center;
            }
            #chatbot-input {
                flex: 1;
                padding: 1rem 1.5rem;
                border-radius: var(--radius-full);
                border: 1px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.05);
                color: white;
                outline: none;
                font-size: 1.1rem;
                transition: border-color 0.3s;
            }
            #chatbot-input:focus {
                border-color: var(--primary);
            }
            #chatbot-input-area button {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                border: none;
                background: var(--primary);
                color: white;
                cursor: pointer;
                transition: transform 0.2s, background 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
            }
            #chatbot-input-area button:hover {
                background: var(--primary-light);
                transform: scale(1.05);
            }
            .typing-indicator {
                display: flex;
                gap: 0.5rem;
                padding: 1rem 1.5rem;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 1.5rem;
                align-self: flex-start;
                width: fit-content;
            }
            .typing-dot {
                width: 10px;
                height: 10px;
                background: var(--primary);
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }
            .typing-dot:nth-child(1) { animation-delay: 0s; }
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            @keyframes typing {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-5px); }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(widget);
    },

    attachListeners: function () {
        // Already attached inline for simplicity in createWidget
    },

    toggleChat: function () {
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');

        if (window.style.display === 'none') {
            window.style.display = 'flex';
            toggle.style.display = 'none';
            document.getElementById('chatbot-input').focus();
        } else {
            window.style.display = 'none';
            toggle.style.display = 'flex';
        }
    },

    openWithText: function (text) {
        if (!text.trim()) return;
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');

        if (window.style.display === 'none') {
            window.style.display = 'flex';
            toggle.style.display = 'none';
        }

        const input = document.getElementById('chatbot-input');
        input.value = text;
        this.sendMessage();
        input.focus();
    },

    handleKeyPress: function (event) {
        if (event.key === 'Enter') {
            this.sendMessage();
        }
    },

    sendMessage: async function () {
        const input = document.getElementById('chatbot-input');
        const text = input.value.trim();

        if (!text) return;

        // Add user message
        this.addMessage(text, 'user');
        input.value = '';

        // Show typing indicator
        this.showTyping();

        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/chatbot/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: text })
            });

            this.removeTyping();

            if (response.ok) {
                const data = await response.json();
                data.response.forEach(msg => {
                    this.addMessage(msg.text, 'bot');
                });
            } else {
                this.addMessage("Sorry, I'm having trouble connecting to the server.", 'bot');
            }
        } catch (error) {
            this.removeTyping();
            this.addMessage("Network error. Please try again.", 'bot');
        }
    },

    addMessage: function (text, sender) {
        const messagesDiv = document.getElementById('chatbot-messages');
        const message = document.createElement('div');
        message.className = `message ${sender}-message fade-in`;
        message.textContent = text;
        messagesDiv.appendChild(message);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    },

    showTyping: function () {
        const messagesDiv = document.getElementById('chatbot-messages');
        const typing = document.createElement('div');
        typing.className = 'typing-indicator fade-in';
        typing.id = 'typing-indicator';
        typing.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        messagesDiv.appendChild(typing);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    },

    removeTyping: function () {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    }
};

// Initialize only after DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    if (localStorage.getItem('token')) {
        ChatbotWidget.init();
    }
});
