# chatbot.py
# Chạy bằng: streamlit run chatbot.py
# Yêu cầu: pip install google-generativeai streamlit
import os
import time
import traceback
import streamlit as st
import google.generativeai as genai  # đúng import cho SDK mới

# --- LẤY API KEY ---
# Trên Streamlit Cloud: thêm GEMINI_API_KEY (hoặc GOOGLE_API_KEY) vào Secrets
API_ENV_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "API_KEY")
api_key = None
for name in API_ENV_NAMES:
    api_key = os.getenv(name) or api_key
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("API_KEY")
    except Exception:
        api_key = None

if not api_key:
    st.error("Lỗi: Không tìm thấy API key. Thêm GEMINI_API_KEY (hoặc GOOGLE_API_KEY) vào môi trường / Streamlit secrets.")
    st.stop()

# --- VAI TRÒ / SYSTEM INSTRUCTION (giữ nguyên nội dung dài của thầy) ---
SYSTEM_INSTRUCTION = """ 
Bạn là “Chatbook”, một Cố vấn Học tập Tin học AI toàn diện.
... (giữ nguyên toàn bộ nội dung SYSTEM_INSTRUCTION như trong file gốc của thầy) ...
"""

# --- MODEL ---
MODEL_NAME = st.secrets.get("MODEL_NAME", "MODEL_NAME = "gemini-1.5-pro") if isinstance(st.secrets, dict) else os.getenv("MODEL_NAME", "MODEL_NAME = "gemini-1.5-pro")

# Cấu hình SDK
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Lỗi khi cấu hình genai SDK: {e}")
    st.stop()

# Khởi tạo model object (sử dụng tên model)
try:
    # GenerativeModel chấp nhận tên model như tham số khởi tạo
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"Lỗi khi tạo model object: {e}")
    st.stop()

# --- Streamlit UI & CSS ---
st.set_page_config(page_title="Chatbot Tin học 2018", page_icon="✨", layout="centered")
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e6e6e6; }
    .main .block-container { max-width: 850px; padding-top: 2rem; padding-bottom: 5rem; }
    .welcome-message { font-size: 1.1em; color: #333; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🤖 Chatbot KTC")
    st.markdown("---")
    if st.button("➕ Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("knowledge_chunks", None)
        st.experimental_rerun()
    st.markdown("---")
    st.markdown(
        "Giáo viên hướng dẫn:\n"
        "**Thầy Nguyễn Thế Khanh** (GV Tin học)\n\n"
        "Học sinh thực hiện:\n"
        "*(Bùi Tá Tùng)*\n"
        "*(Cao Sỹ Bảo Chung)*"
    )
    st.markdown("---")
    st.caption(f"Model: {MODEL_NAME}")

# --- Khởi tạo session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge_chunks" not in st.session_state:
    st.session_state.knowledge_chunks = []

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Logo & title (không stop app nếu thiếu logo — chỉ cảnh báo)
logo_path = "LOGO.jpg"
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image(logo_path, width=80)
    except Exception:
        st.warning(f"Không tìm thấy file logo '{logo_path}' — tiếp tục chạy không có logo.")
with col2:
    st.title("KTC. Chatbot hỗ trợ môn Tin Học")

def set_prompt_from_suggestion(text):
    st.session_state.prompt_from_button = text

# Gợi ý ban đầu nếu chưa có cuộc trò chuyện
if not st.session_state.messages:
    st.markdown("<div class='welcome-message'>Xin chào! Thầy/em cần hỗ trợ gì về môn Tin học (Chương trình 2018)?</div>", unsafe_allow_html=True)
    col1_btn, col2_btn = st.columns(2)
    with col1_btn:
        st.button("Giải thích về 'biến' trong lập trình?", on_click=set_prompt_from_suggestion, args=("Giải thích về 'biến' trong lập trình?",), use_container_width=True)
        st.button("Trình bày về an toàn thông tin?", on_click=set_prompt_from_suggestion, args=("Trình bày về an toàn thông tin?",), use_container_width=True)
    with col2_btn:
        st.button("Sự khác nhau giữa RAM và ROM?", on_click=set_prompt_from_suggestion, args=("Sự khác nhau giữa RAM và ROM?",), use_container_width=True)
        st.button("Các bước chèn ảnh vào word", on_click=set_prompt_from_suggestion, args=("Các bước chèn ảnh vào word",), use_container_width=True)

# --- Xử lý input ---
prompt_from_input = st.chat_input("Mời thầy hoặc các em đặt câu hỏi về Tin học...")
prompt_from_button = st.session_state.pop("prompt_from_button", None)
prompt = prompt_from_button or prompt_from_input

def build_prompt(system_instruction, history, user_input, max_history_chars=8000):
    """
    Gom system instruction + lịch sử + user_input vào một prompt text.
    Cắt lịch sử nếu quá dài dựa trên max_history_chars (đơn giản).
    """
    # Tạo văn bản lịch sử: mỗi turn "User: ...\nAssistant: ..."
    hist_lines = []
    for m in history:
        role = "User" if m["role"] == "user" else "Assistant"
        # escape or normalize newline sequences if cần
        content = m["content"].strip()
        hist_lines.append(f"{role}: {content}")
    conversation = "\n".join(hist_lines)
    full = f"{system_instruction}\n\n{conversation}\nUser: {user_input}\nAssistant:"
    # Nếu quá dài, giữ phần cuối của conversation (đơn giản)
    if len(full) > max_history_chars:
        keep = full[-max_history_chars:]
        return keep
    return full

if prompt:
    # Add user message to history and show it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare prompt and call Gemini (synchronously)
    try:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Đang suy nghĩ...")

            prompt_text = build_prompt(SYSTEM_INSTRUCTION, st.session_state.messages[:-1], prompt)

            try:
                # Gọi API: generate_content trả về object có .text
                response = model.generate_content(prompt_text)
                bot_response_text = getattr(response, "text", str(response))
                if not bot_response_text:
                    bot_response_text = "Xin lỗi, tôi không thể tạo câu trả lời cho truy vấn này."
            except Exception as api_err:
                # Hiện lỗi chi tiết (traceback) cho người quản trị
                bot_response_text = f"⚠️ Lỗi khi gọi Gemini API: {api_err}"
                # Log chi tiết (dùng traceback để debug trên Streamlit logs)
                st.error(bot_response_text)
                st.error(traceback.format_exc())

            # Hiện kết quả
            placeholder.markdown(bot_response_text)

    except Exception as e:
        # Nếu có lỗi ngoài dự kiến
        with st.chat_message("assistant"):
            st.error(f"Xin lỗi, đã xảy ra lỗi nội bộ: {e}")
            st.error(traceback.format_exc())
        bot_response_text = f"LỖI NỘI BỘ: {e}"

    # Lưu câu trả lời nếu có
    if bot_response_text:
        st.session_state.messages.append({"role": "assistant", "content": bot_response_text})

# Nút xóa cuộc trò chuyện (lưu ý: đã đặt ở sidebar nhưng để thêm nữa)
if st.button("🔄 Xóa hội thoại"):
    st.session_state.messages = []
    st.experimental_rerun()

st.markdown("---")
st.caption("© 2025 • Chatbot Gemini | Xây dựng bởi giáo viên Tin học & AI 🤖")



