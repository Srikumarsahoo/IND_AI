const chatForm = document.getElementById("chat-form");
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const modelSelect = document.getElementById("model-select");

// Event listener for sending message
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  const model = modelSelect.value;
  if (!message) return;

  // Show user message
  addMessage("user", message);
  userInput.value = "";

  // Show typing bubble
  const loadingBubble = addMessage("assistant", "Typing...");

  try {
    // USE session-based API endpoint if using chat history feature
    const url = typeof session_id !== "undefined" && session_id !== null
      ? `/chat/${session_id}`
      : "/chat";
    const response = await fetch(url, {
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

// Add a new message bubble
function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("flex", "mb-3");

  if (role === "user") {
    wrapper.classList.add("justify-end");
  } else {
    wrapper.classList.add("justify-start");
  }

  const bubble = document.createElement("div");

  // Use Markdown for assistant replies
  if (role === "assistant") {
    bubble.innerHTML = marked.parse(text);
  } else {
    bubble.textContent = text;
  }

  bubble.className = `
    px-4 py-2 max-w-[80%] rounded-xl text-sm shadow
    prose prose-sm dark:prose-invert
    ${role === "user"
      ? "bg-blue-600 text-white rounded-br-none"
      : "bg-gray-100 dark:bg-gray-700 dark:text-white text-gray-900 rounded-bl-none"}
  `;

  wrapper.appendChild(bubble);
  chatBox.appendChild(wrapper);

  // Scroll to bottom smoothly
  chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });

  return wrapper;
}
