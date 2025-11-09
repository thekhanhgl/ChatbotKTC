# chatbot.py
"""
Simple Gemini chatbot (Google Generative AI)
Supports CLI and Streamlit / Flask server.
Install:
    pip install google-generativeai flask
Set your API key:
    export GEMINI_API_KEY="your_api_key_here"
Docs:
    https://ai.google.dev/gemini-api/docs
"""

import os
import sys
import json
from flask import Flask, request, jsonify
import google.generativeai as genai

# --- CONFIG ---
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ Missing GEMINI_API_KEY. Please set it in environment variables.")

genai.configure(api_key=API_KEY)

# --- Stateless chat ---
def send_message(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {e}"

# --- Flask server (optional) ---
app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("message", "")
    if not prompt:
        return jsonify({"error": "Missing 'message' field"}), 400
    reply = send_message(prompt)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("serve", "--serve"):
        app.run(host="0.0.0.0", port=5000)
    else:
        print("Gemini Chat CLI (type 'exit' to quit)")
        while True:
            user = input("You: ").strip()
            if user.lower() == "exit":
                break
            print("Gemini:", send_message(user))
