const chatForm = document.getElementById("chat-form");
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const modelSelect = document.getElementById("model-select");

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const message = userInput.value.trim();
  const model = modelSelect.value;
  if (!message) return;

  // Show user bubble
  addMessage("user", message);
  userInput.value = "";

  // Show typing bubble
  const loadingBubble = addMessage("assistant", "Typing...");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        user_message: message,
        model: model
      })
    });

    const data = await response.json();
    loadingBubble.remove(); // Remove "Typing..."
    addMessage("assistant", data.reply);
  } catch (error) {
    loadingBubble.remove();
    addMessage("assistant", "⚠️ Something went wrong!");
  }
});

// Adds a bubble for user or assistant with Markdown rendering for assistant
function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("flex", "mb-3");

  if (role === "user") {
    wrapper.classList.add("justify-end");
  } else {
    wrapper.classList.add("justify-start");
  }

  const bubble = document.createElement("div");

  // Apply markdown parsing only to assistant
  if (role === "assistant") {
    bubble.innerHTML = marked.parse(text);
  } else {
    bubble.textContent = text;
  }

  bubble.className = `
    prose prose-sm px-4 py-2 max-w-[80%] text-sm rounded-xl
    ${role === "user" 
      ? "bg-blue-600 text-white rounded-br-none" 
      : "bg-gray-100 text-gray-900 rounded-bl-none"}
  `;

  wrapper.appendChild(bubble);
  chatBox.appendChild(wrapper);
  chatBox.scrollTop = chatBox.scrollHeight;

  return wrapper;
}
