import streamlit as st
import requests
import time
import base64
import os

# 1. SET PAGE CONFIG
st.set_page_config(page_title="Feemo AI", layout="centered")

# 2. FUNCTION TO LOAD IMAGE SAFELY
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_img_with_href(local_img_path):
    img_format = os.path.splitext(local_img_path)[-1].replace('.', '')
    bin_str = get_base64_of_bin_file(local_img_path)
    return f'data:image/{img_format};base64,{bin_str}'

# 3. HIDE UI ELEMENTS & CUSTOM STYLING
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppToolbar {visibility: hidden;}
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    .stChatInput input { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #c9a84c !important; border-radius: 12px !important; }
    .stChatMessage { background-color: #1a1a1a !important; border-radius: 12px !important; border-left: 3px solid #c9a84c !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
    h1 { color: #c9a84c !important; font-family: 'Georgia', serif !important; }
    .sidebar-logo { display: block; margin: 0 auto; width: 80%; border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 4. SIDEBAR SECTION
with st.sidebar:
    # Try to load the local file using Base64
    try:
        if os.path.exists("logo.png"):
            img_base64 = get_img_with_href("logo.png")
            st.markdown(f'<img src="{img_base64}" class="sidebar-logo">', unsafe_allow_html=True)
        else:
            # Fallback if file is missing
            st.markdown("<h1 style='text-align:center;'>🤖</h1>", unsafe_allow_html=True)
    except Exception:
        st.markdown("<h1 style='text-align:center;'>🤖</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center;padding-bottom:20px;'>
        <h2 style='color:#c9a84c;margin:0;'>Feemo AI</h2>
        <p style='color:#8b6914;font-size:12px;'>Your Smart AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>👤 Created by</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#ffffff;font-size:15px;font-weight:bold;'>Muhammad Faheem Riaz</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>💡 You can ask me about</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#cccccc;font-size:13px;line-height:2;'>✦ General knowledge<br>✦ Writing and emails<br>✦ Coding help<br>✦ Study and learning</p>", unsafe_allow_html=True)
    
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# 5. MAIN INTERFACE
st.markdown("<div style='text-align:center;'><h1 style='font-size:42px;'>✦ FEEMO AI ✦</h1><p style='color:#8b6914;'>Powered by Groq AI</p></div>", unsafe_allow_html=True)

# 6. API LOGIC
API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<p style='color:#ffffff;'>{msg['content']}</p>", unsafe_allow_html=True)

if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {"model": "llama-3.3-70b-versatile", "messages": st.session_state.messages, "max_tokens": 1000}
        with st.chat_message("assistant"):
            with st.spinner("✦ Thinking..."):
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data).json()
                if "choices" in res:
                    reply = res["choices"][0]["message"]["content"]
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"Error: {e}")
