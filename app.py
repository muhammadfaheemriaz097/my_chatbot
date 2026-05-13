import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE SUPABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. SET PAGE CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. SILENT DATA LOAD (Memory & Activity)
if "bot_memory" not in st.session_state:
    try:
        # Load memory silently behind the scenes
        mem_res = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_res.data[0]['memory_context'] if mem_res.data else ""
        
        # Load Recent Activity
        hist_res = supabase.table("chat_history").select("chat_title").order("created_at", desc=True).limit(8).execute()
        st.session_state.recent_activity = [row['chat_title'] for row in hist_res.data] if hist_res.data else []
    except:
        st.session_state.bot_memory = ""
        st.session_state.recent_activity = []

# 4. CLEAN CHATGPT UI CSS
st.markdown("""
    <style>
    /* HIDE DEFAULT ELEMENTS */
    #MainMenu, footer, .stAppToolbar {visibility: hidden;}
    
    /* HAMBURGER MENU ICON FIX */
    button[kind="headerNoPadding"] svg { display: none; }
    button[kind="headerNoPadding"]::after { 
        content: '☰'; 
        font-size: 24px; 
        color: #c9a84c; 
        visibility: visible !important; 
    }
    button[kind="headerNoPadding"] {
        background-color: transparent !important;
        border: 1px solid rgba(201, 168, 76, 0.2) !important;
        margin-left: 10px !important;
    }

    /* DARK THEME */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* RECENT ACTIVITY ITEMS */
    .history-item {
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 4px;
        font-size: 14px;
        color: #d1d1d1;
        cursor: default;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .history-item:hover { background-color: #1a1a1a; }

    /* CHAT BUBBLES */
    [data-testid="stChatMessage"] { border-radius: 0px !important; border: none !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }

    /* CENTERED CONTENT */
    .block-container { max-width: 800px; padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (Activity Only)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.sidebar.markdown("<br><p style='color:#666; font-size:12px; font-weight:bold; letter-spacing:1px;'>RECENT ACTIVITY</p>", unsafe_allow_html=True)
    
    # Show history list
    if st.session_state.recent_activity:
        for activity in st.session_state.recent_activity:
            st.sidebar.markdown(f"<div class='history-item'>💬 {activity}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.caption("No recent history")

    # Developer Credits at the bottom
    st.sidebar.markdown("<div style='position: fixed; bottom: 20px; font-size:12px; color:#444;'>Muhammad Faheem Riaz</div>", unsafe_allow_html=True)

# 6. MAIN CHAT AREA
st.markdown("<div style='text-align:center;'><h1>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. AI LOGIC
if prompt := st.chat_input("Message Feemo AI..."):
    # Save first message of session to Recent Activity
    if len(st.session_state.messages) == 0:
        try:
            supabase.table("chat_history").insert({"chat_title": prompt[:40]}).execute()
            st.session_state.recent_activity.insert(0, prompt[:40])
        except:
            pass

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        today = datetime.datetime.now().strftime("%B %d, %Y")
        # System uses memory context silently from Supabase
        system_rules = f"You are Feemo AI. Today is {today}. Context: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_rules}] + st.session_state.messages
        }
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
    except:
        st.error("Connection lost.")
