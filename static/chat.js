const API_URL = "https://gpt-agent-emii.onrender.com";
const chatBox = document.getElementById("chatbox");
const loginBox = document.getElementById("loginBox");
const chat = document.getElementById("messages");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");

function addMessage(text, type) {
  const msg = document.createElement("div");
  msg.classList.add("message", type);
  msg.textContent = text;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
}

async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const msg = document.getElementById("loginMsg");
  msg.textContent = "⏳ Проверка...";

  try {
    const res = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (res.ok && data.token) {
      localStorage.setItem("token", data.token);
      msg.textContent = "✅ Успешный вход!";
      setTimeout(() => location.reload(), 500);
    } else {
      msg.textContent = "❌ " + (data.error || "Ошибка входа");
    }
  } catch (err) {
    msg.textContent = "⚠️ Ошибка соединения с сервером.";
  }
}

function initChat() {
  const token = localStorage.getItem("token");
  if (!token) {
    loginBox.style.display = "block";
    return;
  }

  chatBox.style.display = "flex";
  addMessage("👋 Привет! Я ассистент компании Buildeco. Чем могу помочь?", "bot");

  sendBtn.addEventListener("click", async () => {
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";
    addMessage("...", "bot");

    const res = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": token,
      },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();
    chat.lastChild.remove();

    if (data.answer) addMessage(data.answer, "bot");
    else addMessage("⚠️ Ошибка: " + (data.error || "Нет ответа"), "bot");
  });
}

initChat();
