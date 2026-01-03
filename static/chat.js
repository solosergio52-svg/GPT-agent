document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ chat.js загружен и DOM готов");

  const container = document.getElementById("buildeco-chat");
  if (!container) {
    console.error("❌ Не найден элемент #buildeco-chat");
    return;
  }

  // === 1. Создаем базовую структуру чата ===
  container.innerHTML = `
    <style>
      .chat-wrapper {
        display: flex; flex-direction: column; height: 90vh;
        max-width: 800px; margin: 40px auto;
        border: 1px solid #ddd; border-radius: 12px;
        background: #fafafa; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        font-family: Inter, sans-serif;
      }
      .chat-messages {
        flex: 1; padding: 20px; overflow-y: auto;
        font-size: 15px; line-height: 1.5;
      }
      .chat-message.user { text-align: right; color: #fff; background: #007aff; padding: 10px 14px; border-radius: 10px; display: inline-block; margin: 8px 0; }
      .chat-message.bot { text-align: left; color: #222; background: #e9ecef; padding: 10px 14px; border-radius: 10px; display: inline-block; margin: 8px 0; }
      .chat-input {
        display: flex; padding: 12px; border-top: 1px solid #ddd; background: #fff;
      }
      .chat-input textarea {
        flex: 1; resize: none; height: 50px; padding: 10px;
        border: 1px solid #ccc; border-radius: 8px; font-size: 14px;
      }
      .chat-input button {
        margin-left: 10px; padding: 0 20px; background: #10a37f; border: none;
        border-radius: 8px; color: #fff; font-size: 15px; cursor: pointer;
      }
      .chat-input button:hover { background: #0e8b6e; }
    </style>

    <div class="chat-wrapper">
      <div class="chat-messages" id="chatMessages">
        <div class="chat-message bot">👋 Привет! Я ассистент компании Buildeco. Чем могу помочь?</div>
      </div>
      <div class="chat-input">
        <textarea id="chatInput" placeholder="Введите сообщение..."></textarea>
        <button id="sendBtn">Отправить</button>
      </div>
    </div>
  `;

  // === 2. Подключаем обработчики ===
  const sendBtn = document.getElementById("sendBtn");
  const chatInput = document.getElementById("chatInput");
  const chatMessages = document.getElementById("chatMessages");
  const token = localStorage.getItem("token");

  if (!token) {
    chatMessages.innerHTML = "<div class='chat-message bot'>🔒 Авторизация не выполнена. Перейдите на страницу входа.</div>";
    return;
  }

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatMessages.innerHTML += `<div class="chat-message user">${text}</div>`;
    chatInput.value = "";
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const res = await fetch("https://gpt-agent-emii.onrender.com/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": token
        },
        body: JSON.stringify({ question: text })
      });

      const data = await res.json();
      if (data.answer) {
        chatMessages.innerHTML += `<div class="chat-message bot">${data.answer}</div>`;
      } else {
        chatMessages.innerHTML += `<div class="chat-message bot">⚠️ Ошибка: ${data.error || "нет ответа"}</div>`;
      }

      chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (e) {
      console.error(e);
      chatMessages.innerHTML += `<div class="chat-message bot">⚠️ Ошибка соединения с сервером.</div>`;
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  console.log("✅ Чат инициализирован");
});
