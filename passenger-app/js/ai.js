import { apiRequest } from './api.js';

export class TransitAI {
  constructor() {
    this.modal = document.getElementById('aiModal');
    this.fab = document.getElementById('aiFab');
    this.closeBtn = document.getElementById('aiCloseBtn');
    this.sendBtn = document.getElementById('aiSendBtn');
    this.input = document.getElementById('aiInput');
    this.messagesContainer = document.getElementById('aiMessages');
    this.suggestionChips = document.querySelectorAll('.suggestion-chip');
  }

  init() {
    if (!this.fab) return;

    this.fab.addEventListener('click', () => this.open());
    this.closeBtn.addEventListener('click', () => this.close());
    this.sendBtn.addEventListener('click', () => this.sendMessage());
    
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.sendMessage();
      }
    });

    this.suggestionChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.getAttribute('data-query');
        this.input.value = text;
        this.sendMessage();
      });
    });

    // Close on backdrop click
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) this.close();
    });
  }

  open() {
    this.modal.classList.add('show');
    this.input.focus();
  }

  close() {
    this.modal.classList.remove('show');
  }

  appendMessage(text, sender = 'ai') {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    
    // Quick simple formatting for bold and list items
    const formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
      
    bubble.innerHTML = formatted;
    this.messagesContainer.appendChild(bubble);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  async sendMessage() {
    const text = this.input.value.trim();
    if (!text) return;

    this.input.value = '';
    this.appendMessage(text, 'user');

    // Add typing placeholder
    const typingBubble = document.createElement('div');
    typingBubble.className = 'chat-bubble ai';
    typingBubble.id = 'aiTyping';
    typingBubble.textContent = 'TransitNow AI is querying live data...';
    this.messagesContainer.appendChild(typingBubble);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

    try {
      const res = await apiRequest('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text })
      });

      const typing = document.getElementById('aiTyping');
      if (typing) typing.remove();

      this.appendMessage(res.reply, 'ai');
    } catch (err) {
      const typing = document.getElementById('aiTyping');
      if (typing) typing.remove();
      this.appendMessage('⚠️ Sorry, I could not retrieve live transit info right now.', 'ai');
    }
  }
}
