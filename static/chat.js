const API_URL = "https://gpt-agent-emii.onrender.com"; // <-- твой домен
const token = localStorage.getItem("token");

if (!token) {
  alert("Требуется авторизация — перейдите на /login");
}

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
      "Authorization": token
    },
    body: JSON.stringify({ question })
  });

  const data = await res.json();
  chat.lastChild.remove();

  if (data.answer) addMessage(data.answer, "bot");
  else addMessage("⚠️ Ошибка: " + (data.error || "Неизвестная"), "bot");
});
