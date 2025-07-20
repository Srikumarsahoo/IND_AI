from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import os
import openai
import sqlite3
from app import auth
from itsdangerous import URLSafeSerializer

# --- Load environment ---
load_dotenv()
openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

DB_FILE = "users.db"
SECRET_KEY = "supersecretkey"
serializer = URLSafeSerializer(SECRET_KEY)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# --- Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth.init_db()

def get_current_user(request: Request):
    session_token = request.cookies.get("session")
    if session_token:
        return auth.decode_session(session_token)
    return None

# --- DB chat schema migration ---
def init_chat_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            '''CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        )
        c.execute(
            '''CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id)
            )'''
        )
        conn.commit()

init_chat_db()

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    # Redirect to chat history page for session selection
    return RedirectResponse("/history")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    if auth.register_user(username, password):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "error": "User already exists."
    }, status_code=400)

@app.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    if auth.verify_user(username, password):
        token = auth.create_session(username)
        res = RedirectResponse("/history", status_code=302)
        res.set_cookie("session", token, httponly=True)
        return res
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid username or password."
    }, status_code=401)

@app.get("/logout")
async def logout():
    res = RedirectResponse("/login", status_code=302)
    res.delete_cookie("session")
    return res

# --- CHAT SESSION ROUTES ---

@app.get("/history", response_class=HTMLResponse)
async def chat_history(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT session_id, title, created_at FROM chat_sessions WHERE username = ? ORDER BY created_at DESC", (user,))
        sessions = c.fetchall()
    return templates.TemplateResponse("history.html", {"request": request, "sessions": sessions, "user": user})

@app.get("/chat/new")
async def new_chat(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO chat_sessions (username, title) VALUES (?, ?)", (user, "New Chat"))
        session_id = c.lastrowid
        conn.commit()
    return RedirectResponse(f"/chat/{session_id}", status_code=303)

@app.get("/chat/{session_id}", response_class=HTMLResponse)
async def chat_room(request: Request, session_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Check ownership
        c.execute("SELECT title FROM chat_sessions WHERE session_id=? AND username=?", (session_id, user))
        row = c.fetchone()
        if not row:
            return RedirectResponse("/history")
        title = row[0] or "Chat"
        c.execute("SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY id", (session_id,))
        messages = c.fetchall()
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "user": user, "session_id": session_id, "messages": messages, "chat_title": title}
    )

@app.post("/chat/{session_id}")
async def chat(session_id: int, request: Request, user_message: str = Form(...), model: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"reply": "Unauthorized"}, status_code=401)

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY id", (session_id,))
        history = [{"role": r, "content": t} for r, t in c.fetchall()]
    if not history or history[0]["role"] != "system":
        history.insert(0, {"role": "system", "content": "You are a helpful assistant."})
    history.append({"role": "user", "content": user_message})

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=history
        )
        reply = response.choices[0].message.content.strip()
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, "user", user_message))
            c.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, "assistant", reply))
            conn.commit()
        return JSONResponse({"reply": reply})
    except Exception as e:
        print("Chat error:", e)
        return JSONResponse({"reply": "Something went wrong."})

