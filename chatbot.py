# python.py
"""
Simple Gemini chatbot example
Supports:
 - CLI interactive chat
 - Small Flask HTTP endpoint: POST /chat  with JSON {"message": "..."}
Dependencies:
 pip install google-genai flask
Set GEMINI_API_KEY in environment before running.
Docs: https://ai.google.dev/gemini-api/docs/quickstart
"""

import os
import sys
import json
from typing import Optional

# Google Gen AI SDK
try:
    from google import genai
except Exception as e:
    print("Missing google-genai package. Install with: pip install google-genai")
    raise

# Optional: simple HTTP server
from flask import Flask, request, jsonify

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
API_KEY = os.environ.get("GEMINI_API_KEY", None)

# Create client: the client will read GEMINI_API_KEY automatically if set in environment
if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    # If user didn't set env var, try default constructor (docs say it picks up GEMINI_API_KEY)
    client = genai.Client()

# --- Helper to send a single message (stateless) ---
def send_message_stateless(prompt: str, model: str = MODEL, max_tokens: Optional[int] = 512) -> str:
    """
    Send a single request to Gemini and return text.
    This is quick to start with; for multi-turn you'd normally use client.chats.create(...)
    or store conversation state and pass it to the model.
    """
    # Simple usage via generate_content
    resp = client.models.generate_content(model=model, contents=prompt)
    # Many SDK responses expose .text
    try:
        return resp.text
    except AttributeError:
        # Fallback: try converting to dict or candidates
        try:
            return str(resp)
        except Exception:
            return ""

# --- Simple multi-turn using the SDK's chat helper (recommended for context) ---
def create_chat_and_send(initial_system_prompt: str = "You are a helpful assistant.", model: str = MODEL):
    """
    Create a chat session object (stateful) via SDK, return object with .send_message()
    Requires google-genai version that supports client.chats.create(...)
    """
    # Some SDK versions provide client.chats.create(...)
    if not hasattr(client, "chats") or not hasattr(client.chats, "create"):
        raise RuntimeError("This SDK build does not support client.chats.create(). Use generate_content or upgrade google-genai.")
    chat = client.chats.create(model=model)
    # If the SDK supports adding system message, use send_message with system role if available
    if initial_system_prompt:
        # send system prompt first (if API supports role differentiation).
        # Many SDKs accept plain text for initial system context; if not, this is still ok.
        chat.send_message(f"[System]\n{initial_system_prompt}")
    return chat

# --- CLI interactive chat loop (stateful using chat session if available) ---
def run_cli():
    print("Gemini CLI Chat — type 'exit' to quit.")
    # Try to use chat API for multi-turn if available
    use_chat_obj = hasattr(client, "chats") and hasattr(client.chats, "create")
    if use_chat_obj:
        try:
            chat = create_chat_and_send()
        except Exception as e:
            print("Warning: couldn't create chat session, falling back to stateless. Error:", e)
            use_chat_obj = False
            chat = None
    else:
        chat = None

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        try:
            if use_chat_obj and chat is not None:
                resp = chat.send_message(user_input)
                # stream support: some SDKs return chunks via send_message_stream
                text = getattr(resp, "text", str(resp))
            else:
                text = send_message_stateless(user_input)
        except Exception as e:
            text = f"[Error while calling Gemini API] {e}"

        print("\nGemini: ")
        print(text)

# --- Flask server for simple HTTP chatbot endpoint ---
app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    POST /chat
    Body: {"message": "Hello", "use_stateful": true/false}
    Response: {"reply": "..."}
    """
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "")
    use_stateful = bool(data.get("use_stateful", True))

    if not message:
        return jsonify({"error": "missing 'message' in JSON body"}), 400

    try:
        if use_stateful and hasattr(client, "chats") and hasattr(client.chats, "create"):
            # Create ephemeral chat per request or integrate session management for true multi-turn
            chat = client.chats.create(model=MODEL)
            resp = chat.send_message(message)
            reply = getattr(resp, "text", str(resp))
        else:
            reply = send_message_stateless(message)
    except Exception as e:
        return jsonify({"error": "API call failed", "detail": str(e)}), 500

    return jsonify({"reply": reply})

# --- Entrypoint ---
if __name__ == "__main__":
    # If run with "python python.py serve" -> start Flask server
    if len(sys.argv) > 1 and sys.argv[1] in ("serve", "server", "--serve"):
        port = int(os.environ.get("PORT", 5000))
        print(f"Starting Flask server on port {port} (endpoint POST /chat)")
        app.run(host="0.0.0.0", port=port)
    else:
        run_cli()
