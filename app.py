import streamlit as st
import requests
import time
from PIL import Image

# 1. SET PAGE CONFIG (Must be the very first Streamlit command)
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="logo.png", 
    layout="centered"
)

# 2. HIDE STREAMLIT ELEMENTS (GitHub icon, MainMenu, Footer)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stAppToolbar {visibility: hidden;}
            
            /* Your Existing Custom Styles */
            .stApp { background-color: #0a0a0a; color: #ffffff; }
            .stChatInput input { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #c9a84c !important; border-radius: 12px !important; font-size: 15px !important; }
            .stChatMessage { background-color: #1a1a1a !important; border-radius: 12px !important; padding: 15px !important; border-left: 3px solid #c9a84c !important; margin-bottom: 10px !important; }
            .stChatMessage p { color: #ffffff !important; font-size: 16px !important; line-height: 1.8 !important; font-weight: 500 !important; }
            section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
            h1 { color: #c9a84c !important; font-family: Georgia, serif !important; letter-spacing: 2px !important; }
            p { color: #ffffff !important; font-size: 15px !important; }
            ::-webkit-scrollbar { width: 4px; }
            ::-webkit-scrollbar-thumb { background: #c9a84c; border-radius: 4px; }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 3. SIDEBAR WITH NEW LOGO
try:
    logo = Image.open("logo.png")
    st.sidebar.image(logo, use_container_width=True)
except:
    # Fallback if image isn't uploaded yet
    st.sidebar.markdown("<h1 style='text-align:center;'>🤖</h1>", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style='text-align:center;padding:0 0 20px 0;'>
<h2 style='color:#c9a84c;margin:0;'>Feemo AI</h2>
<p style='color:#8b6914;font-size:12px;'>Your Smart AI Assistant</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>👤 Created by</p>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#ffffff;font-size:15px;font-weight:bold;'>Muhammad Faheem Riaz</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>💡 You can ask me about</p>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#cccccc;font-size:13px;line-height:2;'>✦ General knowledge<br>✦ Writing and emails<br>✦ Coding help<br>✦ Study and learning<br>✦ Business ideas<br>✦ Anything else!</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# 4. MAIN INTERFACE
st.markdown("""
<div style='text-align:center;padding:10px 0 20px 0;'>
<h1 style='color:#c9a84c;font-size:42px;letter-spacing:3px;'>✦ FEEMO AI ✦</h1>
<p style='color:#8b6914;font-size:14px;'>Powered by Groq AI — Fast and Intelligent</p>
<hr style='border-color:#c9a84c;opacity:0.3;'>
</div>
""", unsafe_allow_html=True)

# 5. LOGIC & API
API_KEY = st.secrets["GROQ_API_KEY"]

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.markdown("""
<div style='text-align:center;padding:40px 20px;'>
<p style='font-size:40px;'>✦</p>
<p style='color:#c9a84c;font-size:18px;font-weight:bold;'>Welcome to Feemo AI</p>
<p style='color:#aaaaaa;font-size:14px;'>Ask me anything — I am here to help you 24/7</p>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown("<p style='color:#ffffff;font-size:16px;line-height:1.8;font-weight:500;'>" + msg["content"] + "</p>", unsafe_allow_html=True)

if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown("<p style='color:#ffffff;font-size:16px;line-height:1.8;font-weight:500;'>" + prompt + "</p>", unsafe_allow_html=True)
    try:
        headers = {
            "Authorization": "Bearer " + API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": st.session_state.messages,
            "max_tokens": 1000
        }
        with st.chat_message("assistant"):
            with st.spinner("✦ Feemo AI is thinking..."):
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                result = response.json()
                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    placeholder = st.empty()
                    typed = ""
                    for char in reply:
                        typed += char
                        placeholder.markdown("<p style='color:#c9a84c;font-size:16px;line-height:1.8;font-weight:500;'>" + typed + "▌</p>", unsafe_allow_html=True)
                        time.sleep(0.008)
                    placeholder.markdown("<p style='color:#ffffff;font-size:16px;line-height:1.8;font-weight:500;'>" + reply + "</p>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                elif "error" in result:
                    st.error("Error: " + result["error"]["message"])
                    st.session_state.messages.pop()
    except Exception as e:
        st.error("Error: " + str(e))
        st.session_state.messages.pop()
