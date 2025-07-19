const chatForm = document.getElementById("chat-form");
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const modelSelect = document.getElementById("model-select");

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  const model = modelSelect.value;
  if (!message) return;

  addMessage("user", message);
  userInput.value = "";

  const response = await fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: new URLSearchParams({
      user_message: message,
      model: model
    })
  });

  const data = await response.json();
  addMessage("assistant", data.reply);
});

function addMessage(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  chatBox.appendChild(bubble);
  chatBox.scrollTop = chatBox.scrollHeight;
}
