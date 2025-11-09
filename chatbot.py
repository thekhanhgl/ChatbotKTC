# chatbot_streamlit.py
"""
💬 Chatbot sử dụng Google Gemini API (Generative AI)
Tác giả: Khanh Nguyen (2025)
---------------------------------------------
✅ Yêu cầu:
    pip install streamlit google-generativeai
✅ Cách chạy:
    streamlit run chatbot_streamlit.py
✅ Cách cấu hình:
    export GEMINI_API_KEY="your_api_key_here"
Hoặc tạo file .streamlit/secrets.toml và thêm:
    GEMINI_API_KEY = "your_api_key_here"
---------------------------------------------
"""

import os
import streamlit as st
import google.generativeai as genai

# --- Cấu hình API key ---
API_KEY = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", None))
if not API_KEY:
    st.error("❌ Chưa có API Key! Vui lòng đặt GEMINI_API_KEY trong môi trường hoặc secrets.toml.")
    st.stop()

genai.configure(api_key=API_KEY)

# --- Model sử dụng ---
MODEL_NAME = "gemini-2.0-flash"  # hoặc "gemini-2.0-pro" nếu bạn có quyền truy cập

# --- Hàm sinh phản hồi ---
def generate_reply(user_input, chat_history):
    """
    Gửi yêu cầu đến Gemini với ngữ cảnh trò chuyện.
    """
    model = genai.GenerativeModel(MODEL_NAME)
    # Gom toàn bộ lịch sử hội thoại để giữ ngữ cảnh
    conversation = "\n".join([f"User: {u}\nAI: {a}" for u, a in chat_history])
    prompt = conversation + f"\nUser: {user_input}\nAI:"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Lỗi gọi Gemini API: {e}"

# --- Giao diện Streamlit ---
st.set_page_config(page_title="🤖 Chatbot Gemini", page_icon="💬", layout="centered")

st.title("🤖 Chatbot AI - Google Gemini")
st.caption("Được xây dựng bằng `google-generativeai` + `Streamlit`")

# Lưu lịch sử hội thoại trong session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Khung chat ---
for user, bot in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(user)
    with st.chat_message("assistant"):
        st.markdown(bot)

# --- Ô nhập liệu ---
user_input = st.chat_input("Nhập tin nhắn của bạn...")
if user_input:
    # Hiển thị tin nhắn người dùng
    with st.chat_message("user"):
        st.markdown(user_input)

    # Gọi API Gemini
    with st.chat_message("assistant"):
        with st.spinner("Gemini đang trả lời..."):
            reply = generate_reply(user_input, st.session_state.chat_history)
            st.markdown(reply)

    # Lưu vào lịch sử
    st.session_state.chat_history.append((user_input, reply))

# --- Nút làm mới ---
if st.button("🔄 Xóa hội thoại"):
    st.session_state.chat_history = []
    st.experimental_rerun()

st.markdown("---")
st.caption("© 2025 • Chatbot Gemini | Xây dựng bởi giáo viên Tin học & AI 🤖")
