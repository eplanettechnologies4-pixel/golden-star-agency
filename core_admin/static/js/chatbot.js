// Chatbot UI Toggle
let isChatOpen = false;
const sessionId = Math.random().toString(36).substring(2, 15);

function toggleChatWindow() {
    const consoleEl = document.getElementById('chatbot-console');
    const openIcon = document.getElementById('chat-btn-icon-open');
    const closeIcon = document.getElementById('chat-btn-icon-close');
    
    isChatOpen = !isChatOpen;
    
    if (isChatOpen) {
        consoleEl.classList.remove('hidden');
        setTimeout(() => {
            consoleEl.classList.remove('scale-95', 'opacity-0');
            consoleEl.classList.add('scale-100', 'opacity-100');
        }, 10);
        openIcon.classList.add('hidden');
        closeIcon.classList.remove('hidden');
    } else {
        consoleEl.classList.remove('scale-100', 'opacity-100');
        consoleEl.classList.add('scale-95', 'opacity-0');
        setTimeout(() => {
            consoleEl.classList.add('hidden');
        }, 200);
        openIcon.classList.remove('hidden');
        closeIcon.classList.add('hidden');
    }
}

function handleChatKeydown(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const inputEl = document.getElementById('chat-user-input');
    const messageText = inputEl.value.trim();
    if (!messageText) return;

    // Clear input
    inputEl.value = '';

    // Append user message
    appendMessage(messageText, 'user');

    // Show typing indicator
    const typingIndicator = document.getElementById('chat-typing-indicator');
    typingIndicator.classList.remove('hidden');

    // Scroll to bottom
    scrollToBottom();

    try {
        // Call FastAPI Chatbot Endpoint
        const response = await fetch(`http://127.0.0.1:8000/chatbot/message?message=${encodeURIComponent(messageText)}&session_id=${sessionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            appendMessage(data.reply, 'bot');
        } else {
            appendMessage("I'm sorry, I'm having trouble connecting to the service right now. Please try again later.", 'bot');
        }
    } catch (error) {
        console.error("Chatbot API error:", error);
        // Fallback simulated answer if local server isn't running
        setTimeout(() => {
            appendMessage("Thank you for your message! To learn more about our Hajj & Umrah services, please register an account or contact us at info@goldenstar.pk.", 'bot');
            scrollToBottom();
        }, 1000);
    } finally {
        typingIndicator.classList.add('hidden');
        scrollToBottom();
    }
}

function appendMessage(text, sender) {
    const logsContainer = document.getElementById('chat-logs-container');
    const wrapper = document.createElement('div');
    wrapper.className = 'flex gap-2 ' + (sender === 'user' ? 'justify-end' : '');

    if (sender === 'bot') {
        wrapper.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-brand-orange flex items-center justify-center text-white font-extrabold flex-shrink-0 text-xs">
                <i class="fa-solid fa-star-and-crescent"></i>
            </div>
            <div class="bg-white border border-slate-200 text-slate-700 px-3 py-2 rounded-2xl rounded-tl-none max-w-[80%] shadow-sm leading-relaxed">
                ${text}
            </div>
        `;
    } else {
        wrapper.innerHTML = `
            <div class="bg-brand-orange text-white px-3 py-2 rounded-2xl rounded-tr-none max-w-[80%] shadow-sm font-medium leading-relaxed">
                ${text}
            </div>
        `;
    }

    logsContainer.appendChild(wrapper);
}

function scrollToBottom() {
    const logsContainer = document.getElementById('chat-logs-container');
    logsContainer.scrollTop = logsContainer.scrollHeight;
}
