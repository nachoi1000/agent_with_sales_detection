let conversationId = null;
const chatbox = document.getElementById('chatbox');
const userInput = document.getElementById('userInput');
const chatForm = document.getElementById('chatForm');
const resetButton = document.getElementById('resetButton');
const themeToggle = document.getElementById('themeToggle');

function appendMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex mb-4 ${sender === 'user' ? 'justify-end' : 'justify-start'}`;
    messageDiv.innerHTML = `
        <div class="max-w-[75%] p-3 rounded-lg ${
            sender === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-white'
        }">
            ${text}
        </div>
    `;
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
}

async function sendMessage(e) {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage(message, 'user');
    userInput.value = '';

    if (!conversationId) {
        const convResponse = await fetch('/conversation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_input: message })
        });
        const convData = await convResponse.json();
        conversationId = convData.conversation_id;
    }

    const response = await fetch('/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId, user_input: message })
    });
    const data = await response.json();

    appendMessage(data.answer, 'bot');
}

function resetConversation() {
    conversationId = null;
    chatbox.innerHTML = '';
    userInput.value = '';
}

function toggleTheme() {
    document.body.classList.toggle('dark');
}

chatForm.addEventListener('submit', sendMessage);
resetButton.addEventListener('click', resetConversation);
themeToggle.addEventListener('click', toggleTheme);