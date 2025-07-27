# 🤖 IND_AI — Intelligent Chatbot with Group Co-Memory

![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10+-blue)

IND_AI is a modern AI-powered chatbot application built with **FastAPI**, **Tailwind CSS**, and **local LLMs (via HuggingFace or Ollama)**. It features secure user authentication, session-based chat memory, and an advanced **"Live AI Co-Memory"** system that enables real-time, shared memory across user groups.

---

## 🌟 Features

- 🔒 **Authentication**: Secure login & signup system with session management.
- 🌗 **Dark Mode**: Fully responsive UI with toggle support.
- 🧠 **Chat Memory**: Maintains multi-turn conversations.
- 👥 **Live AI Co-Memory**: Shared memory across user groups for collaborative context building.
- 🧾 **Chat History**: Persists all chats and allows reviewing past conversations.
- 🧬 **Model Switcher**: Dynamically select between different local/hosted LLMs (GPT-4, Claude, Mistral, etc).
- 🌐 **Fully Deployable**: Optimized for deployment on Render, Vercel, or self-hosted Linux servers.

---

## 🛠️ Tech Stack

| Layer       | Tools Used                          |
|-------------|-------------------------------------|
| Backend     | Python, FastAPI, SQLite, bcrypt     |
| Frontend    | HTML, Tailwind CSS, Vanilla JS      |
| LLM Support | HuggingFace Transformers, Ollama    |
| Deployment  | Render / Localhost / Docker         |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ind_ai-chatbot.git
cd ind_ai-chatbot
2. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Run the Application
bash
Copy
Edit
uvicorn main:app --reload
Visit: http://localhost:8000/login

🧠 Live AI Co-Memory (How it works)
Co-Memory enables multiple users in the same group to build a shared context. Each message from any member updates the memory visible to the group, enabling collaborative interactions with the AI.

Example:
Group Name: dev-team

User A and User B join dev-team during signup.

Any prompt by User A is remembered when User B interacts next.

Great for teams working on shared documents, code, or storytelling.

📁 Project Structure
php
Copy
Edit
ind_ai_chatbot/
│
├── static/                 # CSS, JS files
├── templates/              # HTML (Jinja2)
│   ├── login.html
│   ├── signup.html
│   └── chat.html
│
├── db.py                   # Database models and logic
├── main.py                 # FastAPI routes and backend logic
├── auth.py                 # Login/signup/session logic
├── model_handler.py        # Switch and call different LLMs
├── requirements.txt
└── README.md
🧩 Roadmap
 Auth with session management

 Chat memory per session

 Group-based AI co-memory

 Dark mode toggle

 Model switcher

 Admin dashboard for monitoring users & groups

 Real-time updates with WebSockets

 File uploads & multimodal LLM support (PDF, images)

🛡️ License
Licensed under the MIT License.

🙌 Credits
FastAPI

Tailwind CSS

Ollama

HuggingFace Transformers

💬 Feedback & Contributions
If you find this useful, give a ⭐ star on GitHub. Contributions, ideas, and improvements are always welcome! Fork and create a PR.

Built with 💡 by Your Name

yaml
Copy
Edit

---

### ✅ Next Steps

Would you like a `LICENSE` file (MIT) and `requirements.txt` template as well?

Let me know your GitHub username so I can personalize the footer!
