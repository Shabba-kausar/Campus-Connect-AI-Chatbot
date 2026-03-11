document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBody = document.getElementById('chat-body');
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    const typingIndicator = document.getElementById('typing-indicator');
    const clearChatBtn = document.getElementById('clear-chat-btn');

    // Attempt to get logo from global variable, default to standard image
    let logoSrc = '/static/images/manuu_logo.png';
    if (window.STATIC_URL) {
        logoSrc = window.STATIC_URL + 'images/manuu_logo.png';
    }

    // Scroll to bottom helper
    const scrollToBottom = () => {
        chatBody.scrollTo({
            top: chatBody.scrollHeight,
            behavior: 'smooth'
        });
    };

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    clearChatBtn.addEventListener('click', () => {
        // Leave the first greeting message and remove others
        while (chatBody.children.length > 1) {
            chatBody.removeChild(chatBody.lastChild);
        }
    });

    suggestionChips.forEach((chip) => {
        chip.addEventListener('click', () => {
            const action = chip.getAttribute('data-action');
            if(action) {
                messageInput.value = action;
                sendMessage();
            }
        });
    });

    function formatTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        // Reset input immediately
        messageInput.value = '';

        // Add User Message
        const userHTML = `
            <div class="message-wrapper user fade-in">
                <div class="message">
                    <div class="message-content">
                        <p>${escapeHtml(text)}</p>
                    </div>
                    <span class="time">${formatTime()}</span>
                </div>
            </div>
        `;
        chatBody.insertAdjacentHTML('beforeend', userHTML);
        scrollToBottom();

        // Show Typing Indicator
        typingIndicator.style.display = 'flex';
        chatBody.appendChild(typingIndicator); // move to bottom
        scrollToBottom();

        // Send to backend
        fetch('/process_message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({ message: text })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            typingIndicator.style.display = 'none';
            const botReply = data.message || 'Sorry, no response.';
            renderBotMessage(botReply);
        })
        .catch(err => {
            typingIndicator.style.display = 'none';
            renderBotMessage('Sorry, the server encountered an error. Please try again.');
        });
    }

    function renderBotMessage(markdownText) {
        const renderedText = renderMarkdown(markdownText);
        const botHTML = `
            <div class="message-wrapper bot fade-in">
                <img src="${logoSrc}" alt="AI" class="avatar" onerror="this.src='https://manuu.edu.in/sites/default/files/logo-english-2023.png'">
                <div class="message">
                    <div class="message-content">
                        ${renderedText}
                    </div>
                    <span class="time">${formatTime()}</span>
                </div>
            </div>
        `;
        chatBody.insertAdjacentHTML('beforeend', botHTML);
        scrollToBottom();
    }

    // CSRF Token Helper
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Security Helpers
    function escapeHtml(str) {
        let div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function linkifyEscaped(escapedText) {
        const urlRegex = /(https?:\/\/[^\s)]+)/g;
        return escapedText.replace(urlRegex, function(url) {
            const clean = url.replace(/[.,;:]$/, '');
            return `<a href="${clean}" target="_blank" rel="noopener">${clean}</a>`;
        });
    }

    // Custom Markdown Renderer (handles single heading and bullets nicely)
    function renderMarkdown(text) {
        if (!text) return '<p>Sorry, no response.</p>';
        const raw = text.replace(/\r/g, '');
        const lines = raw.split('\n').map(l => l.trim()).filter(l => l !== '');
        
        let html = '';
        
        if (lines.length > 0) {
            const firstLine = lines[0];
            let headingText = null;
            // Check for **Heading** or # Heading
            const boldMatch = firstLine.match(/^\*\*(.+)\*\*$/);
            const hashMatch = firstLine.match(/^#+\s*(.+)$/);
            
            if (boldMatch) headingText = escapeHtml(boldMatch[1]);
            else if (hashMatch) headingText = escapeHtml(hashMatch[1]);
            else if (firstLine.length < 100 && firstLine.endsWith(':')) headingText = escapeHtml(firstLine.slice(0, -1));

            if (headingText) {
                html += `<h3 class="bot-heading">${headingText}</h3>`;
                lines.shift();
            }
        }

        const bullets = lines.filter(l => /^(-|\*|•|\d+\.)\s+/.test(l));
        if (bullets.length > 0) {
            html += '<ul class="bot-bullets">';
            let inList = false;
            
            for(let i=0; i<lines.length; i++) {
                const line = lines[i];
                if (/^(-|\*|•|\d+\.)\s+/.test(line)) {
                    if (!inList) {
                        inList = true;
                    }
                    let cleaned = line.replace(/^(-|\*|•|\d+\.)\s+/, '');
                    
                    if (cleaned.startsWith('[IMAGE]')) {
                        const parts = cleaned.split(/\s+/, 2);
                        const imgUrl = parts.length > 1 ? parts[1] : null;
                        if (imgUrl) {
                            html += `<img src="${escapeHtml(imgUrl)}" alt="image" style="max-width:260px;display:block;margin:8px 0; border-radius: 8px;"/>`;
                        }
                    } else {
                         // bold highlights inside bullets
                         cleaned = escapeHtml(cleaned);
                         cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                         cleaned = linkifyEscaped(cleaned);
                         html += `<li>${cleaned}</li>`;
                    }
                } else {
                    if (inList) {
                        inList = false;
                    }
                    let cleaned = escapeHtml(line);
                    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    cleaned = linkifyEscaped(cleaned);
                    html += `<p style="margin-top: 8px;">${cleaned}</p>`;
                }
            }
            if (inList) { html += '</ul>'; }
            return html;
        }

        // Fallback to pure paragraphs
        text.split('\n').forEach(block => {
            if(block.trim() !== '') {
               let safe = escapeHtml(block);
               safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
               safe = linkifyEscaped(safe);
               html += `<p style="margin-bottom: 8px;">${safe}</p>`;
            }
        });
        
        return html;
    }
});