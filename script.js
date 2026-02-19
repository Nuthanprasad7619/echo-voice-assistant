const micBtn = document.getElementById('micBtn');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const statusText = document.getElementById('statusText');
const conversationMessages = document.getElementById('conversationMessages');
const clearBtn = document.getElementById('clearBtn');
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');
const talkBackToggle = document.getElementById('talkBackToggle');

const SESSION_ID = 'user_' + Math.random().toString(36).substr(2, 9);
let isListening = false;
let recognition = null;
let isProcessing = false;
let retryCount = 0;
let talkBackEnabled = localStorage.getItem('talkBackEnabled') !== 'false'; // Default to true
talkBackToggle.checked = talkBackEnabled;
const MAX_RETRIES = 3;

// --- Voice Recognition Setup ---
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add('active');
        statusText.textContent = 'Listening...';
        statusText.style.color = 'var(--accent-secondary)';
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');

        textInput.value = transcript;

        if (event.results[event.results.length - 1].isFinal) {
            const command = transcript.trim();
            if (command) {
                processCommand(command);
                stopListening();
            }
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopListening();
        statusText.textContent = 'Voice error. Try typing.';
        statusText.style.color = 'var(--accent-primary)';

        setTimeout(() => {
            if (!isListening && !isProcessing) {
                statusText.textContent = 'Tap to speak';
                statusText.style.color = 'var(--text-secondary)';
            }
        }, 3000);
    };

    recognition.onend = () => {
        stopListening();
    };
} else {
    statusText.textContent = 'Voice not supported';
    micBtn.disabled = true;
    micBtn.style.opacity = '0.5';
}

function startListening() {
    if (recognition && !isListening) {
        try {
            recognition.start();
        } catch (e) {
            console.error('Recognition error:', e);
            statusText.textContent = 'Mic busy. Try again.';
        }
    }
}

function stopListening() {
    if (recognition && isListening) {
        recognition.stop();
        isListening = false;
        micBtn.classList.remove('active');
        if (!isProcessing) {
            statusText.textContent = 'Tap to speak';
            statusText.style.color = 'var(--text-secondary)';
        }
    }
}

// --- Chat UI Helper Functions ---

function createTypingIndicator() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg bot typing-indicator';
    msgDiv.id = 'typing-indicator';
    msgDiv.innerHTML = `
        <div class="msg-avatar">E</div>
        <div class="msg-content" style="display:flex; align-items:center; gap:5px; height:40px;">
            <span style="width:8px; height:8px; background:var(--accent-primary); border-radius:50%; animation:pulse 1s infinite;"></span>
            <span style="width:8px; height:8px; background:var(--accent-primary); border-radius:50%; animation:pulse 1s infinite 0.2s;"></span>
            <span style="width:8px; height:8px; background:var(--accent-primary); border-radius:50%; animation:pulse 1s infinite 0.4s;"></span>
        </div>
    `;
    return msgDiv;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// --- Backend Communication ---

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:5000'
    : 'https://echo-backend-to1l.onrender.com'; // Live Render Backend

async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function processCommand(command) {
    if (!command.trim() || isProcessing) return;

    isProcessing = true;
    retryCount = 0;

    addMessage(command, 'user');
    textInput.value = '';

    const typingIndicator = createTypingIndicator();
    conversationMessages.appendChild(typingIndicator);
    conversationMessages.scrollTop = conversationMessages.scrollHeight;

    statusText.textContent = 'Thinking...';
    statusText.style.color = 'var(--accent-secondary)';

    try {
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                command: command,
                session_id: SESSION_ID
            })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();

        removeTypingIndicator();

        if (data.success) {
            // Start voice playback early if enabled
            const ttsPromise = talkBackEnabled ? playBackendTTS(data.response) : Promise.resolve();
            await typeMessage(data.response, 'bot');
            await ttsPromise;
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessage("I'm having trouble reaching the server. Please check if the backend is running.", 'bot');
    } finally {
        isProcessing = false;
        statusText.textContent = 'Tap to speak';
        statusText.style.color = 'var(--text-secondary)';
    }
}

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${sender}`;

    const avatar = sender === 'bot' ? 'E' : '<i class="fas fa-user"></i>';

    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-content"><p>${escapeHtml(text)}</p></div>
    `;

    conversationMessages.appendChild(msgDiv);
    conversationMessages.scrollTop = conversationMessages.scrollHeight;
}

// Improved Typing Effect
async function typeMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${sender}`;

    const avatar = sender === 'bot' ? 'E' : '<i class="fas fa-user"></i>';

    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-content"><p></p></div>
    `;

    conversationMessages.appendChild(msgDiv);

    const p = msgDiv.querySelector('p');
    // Using a simpler splitting/typing approach for better performance
    const chars = text.split('');

    for (let i = 0; i < chars.length; i++) {
        p.textContent += chars[i];
        if (i % 5 === 0) conversationMessages.scrollTop = conversationMessages.scrollHeight;
        await new Promise(resolve => setTimeout(resolve, 20)); // Faster typing
    }
    conversationMessages.scrollTop = conversationMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// --- Backend TTS ---
async function playBackendTTS(text) {
    if (!talkBackEnabled) return;
    try {
        const response = await fetch(`${API_BASE_URL}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.success && data.audio_url) {
                const audio = new Audio(API_BASE_URL + data.audio_url);
                audio.play();
                statusText.textContent = 'Speaking...';
                statusText.style.color = 'var(--accent-primary)';

                audio.onended = () => {
                    if (!isListening) {
                        statusText.textContent = 'Tap to speak';
                        statusText.style.color = 'var(--text-secondary)';
                    }
                };
            }
        }
    } catch (e) {
        console.error("TTS Error:", e);
        speakFallback(text);
    }
}

function speakFallback(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        speechSynthesis.speak(utterance);
    }
}

// --- Event Listeners ---

micBtn.addEventListener('click', () => {
    if (isProcessing) return;
    if (isListening) stopListening();
    else startListening();
});

talkBackToggle.addEventListener('change', () => {
    talkBackEnabled = talkBackToggle.checked;
    localStorage.setItem('talkBackEnabled', talkBackEnabled);
});

sendBtn.addEventListener('click', () => {
    const command = textInput.value.trim();
    if (command && !isProcessing) processCommand(command);
});

textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !isProcessing) {
        const command = textInput.value.trim();
        if (command) processCommand(command);
    }
});

clearBtn.addEventListener('click', () => {
    conversationMessages.innerHTML = `
        <div class="msg bot">
            <div class="msg-avatar">E</div>
            <div class="msg-content"><p>Session cleared. Ready when you are!</p></div>
        </div>
    `;
    fetch(`${API_BASE_URL}/clear/${SESSION_ID}`, { method: 'POST' }).catch(console.error);
});

navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    const icon = navToggle.querySelector('i');
    if (navMenu.classList.contains('active')) {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-times');
    } else {
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
    }
});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
            navMenu.classList.remove('active');
            const icon = navToggle.querySelector('i');
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    });
});

document.querySelectorAll('.faq-header').forEach(header => {
    header.addEventListener('click', () => {
        const item = header.parentElement;
        const isActive = item.classList.contains('active');

        document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));

        if (!isActive) {
            item.classList.add('active');
        }
    });
});

window.addEventListener('load', async () => {
    const isConnected = await checkConnection();
    if (!isConnected) {
        addMessage("⚠️ Backend disconnected. Please run the Python server.", 'bot');
    }
});
