import streamlit as st
import requests
import time

st.set_page_config(
    page_title="Feemo AI",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0a0a0a;
        color: #f5f5f5;
    }

    /* Chat input */
    .stChatInput input {
        background-color: #1a1a1a !important;
        color: #f5f5f5 !important;
        border: 1px solid #c9a84c !important;
        border-radius: 12px !important;
    }

    /* User message bubble */
    .stChatMessage[data-testid="user"] {
        background-color: #1a1a1a !important;
        border-left: 3px solid #c9a84c !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }

    /* Assistant message bubble */
    .stChatMessage[data-testid="assistant"] {
        background-color: #111111 !important;
        border-left: 3px solid #8b6914 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }

    /* Sidebar */
    .stSidebar {
        background-color: #111111 !important;
        border-right: 1px solid #c9a84c !important;
    }

    /* Sidebar text */
    .stSidebar p, .stSidebar h1, .stSidebar h2, .stSidebar h3 {
        color: #f5f5f5 !important;
    }

    /* Title */
    h1 {
        color: #c9a84c !important;
        font-family: 'Georgia', serif !important;
        letter-spacing: 2px !important;
    }

    /* Caption */
    .stCaption {
        color: #8b6914 !important;
    }

    /* Spinner */
    .stSpinner {
        color: #c9a84c !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 4px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0a0a;
    }
    ::-webkit-scrollbar-thumb {
        background: #c9a84c;
        border-radius: 4px;
    }

    /* Gold divider */
    hr {
        border-color: #c9a84c !important;
        opacity: 0.3;
    }

    /* Button */
    .stButton button {
        background-color: #c9a84c !important;
        color: #0a0a0a !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        background-color: #8b6914 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <div style='
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #c9a84c, #8b6914);
        margin: 0 auto 12px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 36px;
        box-shadow: 0 0 20px rgba(201,168,76,0.4);
    '>🤖</div>
    <h2 style='color: #c9a84c; margin: 0; font-family: Georgia, serif;'>Feemo AI</h2>
    <p style='color: #8b6914; font-size: 12px; margin: 4px 0;'>Your Smart AI Assistant</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

st.sidebar.markdown("""
<div style='padding: 10px 0;'>
    <p style='color: #c9a84c; font-size: 13px; font-weight: bold;'>👤 Created by</p>
    <p style='color: #f5f5f5; font-size: 15px; font-weight: bold;'>Muhammad Faheem Riaz</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

st.sidebar.markdown("""
<div style='padding: 8px 0;'>
    <p style='color: #c9a84c; font-size: 13px; font-weight: bold;'>💡 You can ask me about</p>
    <p style='color: #aaaaaa; font-size: 12px;'>✦ General knowledge</p>
    <p style='color: #aaaaaa; font-size: 12px;'>✦ Writing & emails</p>
    <p style='color: #aaaaaa; font-size: 12px;'>✦ Coding help</p>
    <p style='color: #aaaaaa; font-size: 12px;'>✦ Study & learning</p>
    <p style='color: #aaaaaa; font-size: 12px;'>✦ Business ideas</p>
    <p style='color: #aaaaaa; font-size: 12px;'>✦ Anything else!</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align: center; padding: 10px 0 20px 0;'>
    <h1 style='color: #c9a84c; font-size: 42px; letter-spacing: 3px;'>✦ FEEMO AI ✦</h1>
    <p style='color: #8b6914; font-size: 14px;'>Powered by Groq AI — Fast & Intelligent</p>
    <hr style='border-color: #c9a84c; opacity: 0.3;'>
</div>
""", unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────
API_KEY = st.secrets["GROQ_API_KEY"]

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.markdown("""
    <div style='text-align: center; padding: 40px 20px; color: #444;'>
        <p style='font-size: 40px;'>✦</p>
        <p style='color: #c9a84c; font-size: 18px; font-weight: bold;'>Welcome to Feemo AI</p>
        <p style='color: #666; font-size: 14px;'>Ask me anything — I am here to help you 24/7</p>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────
if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-
