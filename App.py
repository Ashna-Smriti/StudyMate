import os
import json
import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "***********b3FYF5tqs6xH76CYtoaEzzbz4RLd")

# Initialize Groq Client
try:
    client = Groq(
        api_key=GROQ_API_KEY,
    )
except Exception as e:
    print(f"Failed to initialize Groq client: {e}")
    client = None

app = Flask(__name__)
CORS(app)

# --- IN-MEMORY DATABASE (REPLACES SQL) ---
DB_USERS = {}
DB_PLANS = {}

# --- HELPER FUNCTIONS ---

def json_response(obj, status=200):
    return (jsonify(obj), status)

def generate_token():
    return secrets.token_urlsafe(24)

def require_token_from_header():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, (jsonify({"status":"error","message":"Missing token"}), 401)
    
    token = auth.split(" ", 1)[1].strip()
    
    for user in DB_USERS.values():
        if user.get("auth_token") == token:
            return user, None
            
    return None, (jsonify({"status":"error","message":"Invalid token"}), 401)

# --- AUTH ENDPOINTS (NO-SQL) ---

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return json_response({"status":"error","message":"Missing fields"}, 400)

    if username in DB_USERS:
        return json_response({"status":"error","message":"Username exists"}, 409)

    pwd_hash = generate_password_hash(password)
    token = generate_token()
    
    DB_USERS[username] = {
        "username": username,
        "password_hash": pwd_hash,
        "auth_token": token
    }
    
    return json_response({"status":"success", "auth_token": token, "username": username}, 201)

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = DB_USERS.get(username)
    
    if not user or not check_password_hash(user["password_hash"], password):
        return json_response({"status":"error","message":"Invalid credentials"}, 401)

    token = generate_token()
    DB_USERS[username]["auth_token"] = token
    
    return json_response({"status":"success", "auth_token": token, "username": username}, 200)

# --- AI & PLAN ENDPOINTS (GROQ) ---

@app.route("/generate_plan", methods=["POST"])
def generate_plan():
    user, err = require_token_from_header()
    if err: return err

    if not client:
        return json_response({"status":"error", "message": "Groq client not initialized."}, 500)

    data = request.get_json()
    career_goal = data.get("career_goal")
    yearly_goal = data.get("yearly_goal")

    prompt = f"""
    Act as a strict career coach. Create a 12-month study roadmap for a student.
    Career Goal: {career_goal}
    Yearly Goal: {yearly_goal}
    
    The JSON structure must be:
    {{
        "1": {{ "monthly_goal": "...", "weekly": ["Week 1 task", "Week 2 task", "Week 3 task", "Week 4 task"] }},
        "2": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "3": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "4": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "5": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "6": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "7": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "8": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "9": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "10": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "11": {{ "monthly_goal": "...", "weekly": ["...", "..."] }},
        "12": {{ "monthly_goal": "...", "weekly": ["...", "..."] }}
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # <-- Current, supported model
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON-only API. You must return a valid JSON object based on the user's request, with no other text, markdown, or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        plan_json_string = completion.choices[0].message.content
        plan_json = json.loads(plan_json_string)

    except Exception as e:
        print(f"*** GROQ PLAN ERROR: {e} ***")
        return json_response({"status":"error", "message": "Failed to generate AI plan."}, 500)

    # 2. Save to our in-memory "DB"
    DB_PLANS[user["username"]] = {
        "yearly_goal": yearly_goal,
        "plan_json": plan_json
    }
    
    return json_response({"status":"success", "message": "Plan generated!", "plan": plan_json}, 200)

@app.route("/api/chat", methods=["POST"])
def chat():
    if not client:
        return json_response({"bot_message": "Groq client not initialized."}, 500)

    data = request.get_json()
    user_message = data.get("message", "")

    try:
        chat_completion = client.chat.completions.create(
             messages=[
                {
                    "role": "system",
                    "content": "You are StudyMate, a helpful and encouraging AI mentor for students."
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="llama-3.1-8b-instant", # <-- Current, supported model
        )
        
        bot_response = chat_completion.choices[0].message.content
        return json_response({"bot_message": bot_response})
        
    except Exception as e:
        print(f"*** GROQ CHAT ERROR: {e} ***")
        return json_response({"bot_message": "I am having trouble connecting..."}, 500)

if __name__ == "__main__":
    if not client or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        print("!!! WARNING: Groq API key is missing or invalid. AI features will fail. !!!")
    
    # THE FIX: port=5000 (not 500)
    app.run(debug=True, port=5000)
