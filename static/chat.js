document.addEventListener("DOMContentLoaded", () => {
  const API_URL = "https://gpt-agent-emii.onrender.com";
  const token = localStorage.getItem("token");
  const chatBox = document.getElementById("messages");
  const input = document.getElementById("input");
  const form = document.getElementById("chatForm");

  if (!token) {
    alert("Необходима авторизация.");
    window.location.href = "/";
    return;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    addMessage("...", "bot");
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
      chatBox.lastChild.remove();
      addMessage(data.answer || "⚠️ Ошибка ответа", "bot");
    } catch (err) {
      chatBox.lastChild.remove();
      addMessage("⚠️ Ошибка соединения с сервером", "bot");
    }
  });

  function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  document.getElementById("newChat").addEventListener("click", () => {
    chatBox.innerHTML = `<div class='message bot'>🆕 Новый чат начат.</div>`;
  });
});
