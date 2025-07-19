from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import json
import openai
from app import auth
from itsdangerous import URLSafeSerializer

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"  # required for OpenRouter

SECRET_KEY = "supersecretkey"
serializer = URLSafeSerializer(SECRET_KEY)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Enable CORS
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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...)):
    if auth.register_user(username, password):
        return RedirectResponse("/login", status_code=302)
    return HTMLResponse("User already exists.", status_code=400)

@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    if auth.verify_user(username, password):
        token = auth.create_session(username)
        res = RedirectResponse("/", status_code=302)
        res.set_cookie("session", token, httponly=True)
        return res
    return HTMLResponse("Invalid credentials.", status_code=401)

@app.get("/logout")
async def logout():
    res = RedirectResponse("/login", status_code=302)
    res.delete_cookie("session")
    return res

@app.post("/chat")
async def chat(request: Request, user_message: str = Form(...), model: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"reply": "Unauthorized"}, status_code=401)

    history_file = f"chat_history_{user}.json"

    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = [{"role": "system", "content": "You are a helpful assistant."}]
    else:
        history = [{"role": "system", "content": "You are a helpful assistant."}]

    history.append({"role": "user", "content": user_message})

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=history
        )
        reply = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": reply})

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

        return JSONResponse({"reply": reply})
    except Exception as e:
        print("Chat error:", e)
        return JSONResponse({"reply": "Something went wrong."})

