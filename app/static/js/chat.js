const chatForm = document.getElementById('chatForm');
const chatWindow = document.getElementById('chatWindow');
const messageInput = document.getElementById('messageInput');
const statusEl = document.getElementById('status');

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatBotMessage(text) {
  let safe = escapeHtml(text || '');
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/\n/g, '<br/>');
  return safe;
}

function appendMessage(text, role) {
  const div = document.createElement('div');
  div.className = `msg ${role === 'user' ? 'msg-user' : 'msg-bot'}`;
  if (role === 'bot') {
    div.innerHTML = formatBotMessage(text);
  } else {
    div.textContent = text;
  }
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

appendMessage('Hello! I can help with admissions, fees, exams, attendance, placements, and academics.', 'bot');

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage(message, 'user');
  messageInput.value = '';
  statusEl.textContent = 'Thinking...';

  try {
    const response = await fetch('/chat/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    const data = await response.json();
    appendMessage(data.answer, 'bot');
    statusEl.textContent = `Intent: ${data.detected_intent} | Confidence: ${data.confidence}`;
  } catch (error) {
    appendMessage('Request failed. Please try again.', 'bot');
    statusEl.textContent = 'Network error';
  }
});
