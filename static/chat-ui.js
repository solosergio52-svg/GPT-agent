document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  body.innerHTML = `
  <style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');
  body {
    margin: 0;
    font-family: "Inter", "Segoe UI", Roboto, sans-serif;
    background: #f8f9fa;
    color: #202123;
  }
  .chat-layout { display: flex; height: 100vh; }
  .sidebar {
    width: 280px; background: #202123; color: #e0e0e0;
    display: flex; flex-direction: column; justify-content: space-between;
  }
  .user-info { padding: 24px; border-bottom: 1px solid #343541; }
  .user-info h3 { font-size: 15px; margin: 0; color: #fff; word-break: break-all; }
  .user-role { font-size: 13px; color: #9ca3af; margin-top: 4px; }
  .chat-list { flex: 1; padding: 20px; overflow-y: auto; }
  .chat-list h4 { font-size: 13px; text-transform: uppercase; margin-bottom: 10px; color: #9ca3af; }
  .chat-item {
    padding: 10px 12px; border-radius: 8px; cursor: pointer; margin-bottom: 8px;
    background: #2a2b32; transition: 0.2s;
  }
  .chat-item:hover { background: #3a3b44; }
  .footer { padding: 15px; border-top: 1px solid #343541; text-align: center; font-size: 12px; color: #6b7280; }
  .main-chat { flex: 1; display: flex; flex-direction: column; }
  .messages { flex: 1; padding: 24px 40px; overflow-y: auto; display: flex; flex-direction: column; }
  .message {
    max-width: 75%; padding: 12px 16px; margin-bottom: 12px; border-radius: 10px;
    white-space: pre-wrap; line-height: 1.5; font-size: 15px;
  }
  .user { background: #007aff; color: white; align-self: flex-end; margin-left: auto; }
  .bot { background: #ececf1; color: #202123; align-self: flex-start; }
  .input-area { display: flex; padding: 16px 32px; border-top: 1px solid #e5e7eb; background: #fff; }
  textarea {
    flex: 1; resize: none; height: 52px; border: 1px solid #ccc; border-radius: 8px;
    padding: 10px; font-size: 15px; font-family: inherit;
  }
  button {
    margin-left: 12px; padding: 0 20px; background: #10a37f; color: #fff;
    border: none; border-radius: 8px; font-weight: 500; cursor: pointer; font-size: 15px;
  }
  button:hover { background: #0e8b6e; }
  </style>

  <div class="chat-layout">
    <div class="sidebar">
      <div>
        <div class="user-info" id="userInfo">
          <h3>Загрузка...</h3>
          <div class="user-role"></div>
        </div>
        <div class="chat-list">
          <h4>💬 Мои чаты</h4>
          <div class="chat-item" id="newChat">+ Новый чат</div>
          <div class="chat-item">🏗️ Объект “Москва-Сити”</div>
          <div class="chat-item">📊 Финансовый отчёт</div>
        </div>
      </div>
      <div class="footer">
        Buildeco Assistant © 2026
      </div>
    </div>

    <div class="main-chat">
      <div class="messages" id="chat">
        <div class="message bot">👋 Привет! Я ассистент компании Buildeco. Задайте вопрос.</div>
      </div>
      <div class="input-area">
        <textarea id="question" placeholder="Введите сообщение..."></textarea>
        <button id="sendBtn">Отправить</button>
      </div>
    </div>
  </div>
  `;

  const API_URL = "https://gpt-agent-emii.onrender.com";
  const token = localStorage.getItem("token");

  if (!token) {
    alert("Необходима авторизация.");
    window.location.href = "/";
    return;
  }

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    document.querySelector("#userInfo h3").innerText = payload.email;
    document.querySelector(".user-role").innerText = payload.role;
  } catch (e) {
    console.error("Ошибка при чтении токена", e);
    window.location.href = "/";
  }

  const chat = document.getElementById("chat");
  const input = document.getElementById("question");
  const sendBtn = document.getElementById("sendBtn");
  const newChatBtn = document.getElementById("newChat");

  newChatBtn.onclick = () => {
    chat.innerHTML = `<div class='message bot'>🆕 Новый чат начат. Задайте вопрос.</div>`;
  };

  sendBtn.onclick = async () => {
    const text = input.value.trim();
    if (!text) return;
    chat.innerHTML += `<div class='message user'>${text}</div>`;
    chat.innerHTML += `<div class='message bot'>...</div>`;
    input.value = "";

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": token
        },
        body: JSON.stringify({ question: text })
      });
      const data = await res.json();
      chat.lastChild.remove();
      chat.innerHTML += `<div class='message bot'>${data.answer || "⚠️ Ошибка ответа"}</div>`;
      chat.scrollTop = chat.scrollHeight;
    } catch (err) {
      chat.lastChild.remove();
      chat.innerHTML += `<div class='message bot'>⚠️ Ошибка соединения с сервером.</div>`;
    }
  };
});
