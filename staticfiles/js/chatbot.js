// static/js/assistant.js
document.addEventListener('DOMContentLoaded', () => {
  const chatArea = document.getElementById('chat-area');
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const actions = document.querySelectorAll('.action');

  // helper to scroll
  function scrollToBottom(){ chatArea.scrollTop = chatArea.scrollHeight; }

  function createBubble(text, type='bot'){
    const div = document.createElement('div');
    div.className = 'bubble ' + (type === 'user' ? 'user' : 'bot');
    if(type === 'user'){
      div.textContent = text;
    } else {
      // bot bubble with icon + text
      div.innerHTML = `<div class="icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 2C13.1046 2 14 2.89543 14 4V5H16C17.6569 5 19 6.34315 19 8V12C19 13.6569 17.6569 15 16 15H15V16C15 17.6569 13.6569 19 12 19C10.3431 19 9 17.6569 9 16V15H8C6.34315 15 5 13.6569 5 12V8C5 6.34315 6.34315 5 8 5H10V4C10 2.89543 10.8954 2 12 2Z" fill="#5A8DE6"/></svg>
        </div>
        <div class="text">${text}</div>`;
    }
    chatArea.appendChild(div);
    scrollToBottom();
    return div;
  }

  // CSRF helper (Django)
  function getCookie(name) {
    let v = null;
    if (document.cookie && document.cookie !== '') {
      const parts = document.cookie.split(';');
      for (let p of parts) {
        p = p.trim();
        if (p.startsWith(name + '=')) { v = decodeURIComponent(p.substring(name.length + 1)); break; }
      }
    }
    return v;
  }
  const csrftoken = getCookie('csrftoken');

  async function postMessage(text){
    // show user bubble
    createBubble(text, 'user');
    // show typing indicator
    const typing = createBubble('...', 'bot');

    try {
      const resp = await fetch('/bot/api/chat/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ message: text })
      });
      const data = await resp.json();
      typing.remove();
      createBubble(data.reply || 'Kuch error hua.');
    } catch(err){
      typing.remove();
      createBubble('Network error. Check console.');
      console.error(err);
    }
  }

  sendBtn.addEventListener('click', () => {
    const t = input.value.trim();
    if(!t) return;
    postMessage(t);
    input.value = '';
    input.focus();
  });
  input.addEventListener('keydown', (e) => {
    if(e.key === 'Enter'){ e.preventDefault(); sendBtn.click(); }
  });

  // quick action clicks
  actions.forEach(act => {
    act.addEventListener('click', () => {
      const key = act.dataset.action;
      let q = '';
      if(key === 'admission') q = 'Admission information';
      else if(key === 'hostel') q = 'Hostel details';
      else if(key === 'canteen') q = 'Canteen menu/timings';
      else if(key === 'exams') q = 'Exam dates';
      // fill input & send
      input.value = q;
      sendBtn.click();
    });
  });
});
