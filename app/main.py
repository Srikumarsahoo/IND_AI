from fastapi import FastAPI, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sqlite3
import openai
from app import auth
from itsdangerous import URLSafeSerializer
from datetime import datetime

# --- Load environment variables ---
load_dotenv()
openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

# --- Constants ---
DB_FILE = "users.db"
SECRET_KEY = "supersecretkey"
serializer = URLSafeSerializer(SECRET_KEY)

# --- Initialize FastAPI ---
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

auth.init_db()  # initialize user/group tables

# --- Create DB tables for chat sessions/messages ---
def init_chat_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id)
            )
        ''')
        conn.commit()

init_chat_db()

# --- Auth helper to get user from session cookie ---
def get_current_user(request: Request):
    session_token = request.cookies.get("session")
    if session_token:
        return auth.decode_session(session_token)
    return None

# ---------------------------
# HOMEPAGE ROUTE
# ---------------------------

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    # Render homepage (not chat, not login!) with request and year context
    return templates.TemplateResponse("home.html", {
        "request": request,
        "year": datetime.now().year
    })

# ---------------------------
# 👤 AUTH ROUTES
# ---------------------------

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    group_name = form.get("group_name")  # Ensure your signup HTML uses name="group_name"
    if auth.register_user(username, password, group_name):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse("Signup failed. User may already exist.", status_code=400)

@app.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    user_session_data = auth.verify_user(username, password)
    if user_session_data:
        token = auth.create_session(user_session_data)
        res = RedirectResponse("/chat/new", status_code=status.HTTP_302_FOUND)
        res.set_cookie("session", token, httponly=True)
        return res
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid username or password."
    }, status_code=401)

@app.get("/logout")
async def logout():
    res = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    res.delete_cookie("session")
    return res

# ---------------------------
# 💬 CHAT ROUTES
# ---------------------------

@app.get("/chat/new")
async def new_chat(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO chat_sessions (username, title) VALUES (?, ?)", (user["username"], "New Chat"))
        session_id = c.lastrowid
        conn.commit()
    return RedirectResponse(f"/chat/{session_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/chat/{session_id}", response_class=HTMLResponse)
async def chat_room(request: Request, session_id: int):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Fetch all user sessions for sidebar
        c.execute("SELECT session_id, title, created_at FROM chat_sessions WHERE username=? ORDER BY created_at DESC", (user["username"],))
        sessions = c.fetchall()
        # Fetch current session title, validate ownership
        c.execute("SELECT title FROM chat_sessions WHERE session_id=? AND username=?", (session_id, user["username"]))
        row = c.fetchone()
        if not row:
            return RedirectResponse("/chat/new", status_code=status.HTTP_302_FOUND)
        chat_title = row[0] or "Chat"
        # Fetch messages
        c.execute("SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY created_at", (session_id,))
        # Fix: use 'personal' not 'perosnal'
        messages = [(role, content, 'personal') for (role, content) in c.fetchall()]
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user": user["username"],
        "session_id": session_id,
        "chat_title": chat_title,
        "messages": messages,
        "sessions": sessions
    })

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
            # Save conversation messages
            c.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, "user", user_message))
            c.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, "assistant", reply))
            # Auto-update session title if still "New Chat"
            c.execute("SELECT title FROM chat_sessions WHERE session_id=?", (session_id,))
            title_row = c.fetchone()
            if title_row and (title_row[0] == "New Chat" or title_row[0] is None):
                short_title = user_message.strip().split('\n')[0][:40].replace("\r", "").replace("\n", "")
                c.execute("UPDATE chat_sessions SET title=? WHERE session_id=?", (short_title, session_id))
            conn.commit()
        return JSONResponse({"reply": reply})
    except Exception as e:
        print(f"Chat error: {e}")
        return JSONResponse({"reply": "Something went wrong."})

@app.post("/chat/{session_id}/rename")
async def rename_session(request: Request, session_id: int, title: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("UPDATE chat_sessions SET title=? WHERE session_id=? AND username=?", (title, session_id, user["username"]))
        conn.commit()
    return RedirectResponse(f"/chat/{session_id}", status_code=status.HTTP_303_SEE_OTHER)
