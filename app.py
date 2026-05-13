import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE DATABASE
# Ensure SUPABASE_URL, SUPABASE_KEY, and GROQ_API_KEY are in Streamlit Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. DATA LOAD (History & Silent Memory)
if "bot_memory" not in st.session_state:
    try:
        # Load user context from user_memory
        mem_res = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_res.data[0]['memory_context'] if mem_res.data else ""
        
        # Load Recent Activity titles from chat_history
        hist_res = supabase.table("chat_history").select("chat_title").order("created_at", desc=True).limit(10).execute()
        st.session_state.recent_activity = [row['chat_title'] for row in hist_res.data] if hist_res.data else []
    except Exception:
        st.session_state.bot_memory = ""
        st.session_state.recent_activity = []

# 4. CHATGPT-STYLE CSS (Hamburger Menu Fix)
st.markdown("""
    <style>
    /* HIDE DEFAULT UI */
    #MainMenu, footer, .stAppToolbar {visibility: hidden;}
    
    /* HAMBURGER MENU ICON (Three Lines) */
    button[kind="headerNoPadding"] svg { display: none; }
    button[kind="headerNoPadding"]::after { 
        content: '☰'; 
        font-size: 26px; 
        color: #c9a84c; 
        visibility: visible !important; 
        display: block;
    }
    button[kind="headerNoPadding"] {
        background-color: transparent !important;
        border: 1px solid rgba(201, 168, 76, 0.2) !important;
        border-radius: 8px !important;
        margin-left: 15px !important;
        width: 45px !important;
        height: 45px !important;
    }

    /* DARK THEME & LAYOUT */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* RECENT ACTIVITY LIST */
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 25px 0 10px 10px; }
    .history-item {
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-size: 14px;
        color: #d1d1d1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .history-item:hover { background-color: #1a1a1a; }

    /* CHAT BUBBLES */
    [data-testid="stChatMessage"] { border: none !important; padding: 2rem 1rem !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }

    /* CENTERED CONTAINER */
    .block-container { max-width: 850px; padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (History List)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c; margin-left:10px;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<div class='history-label'>RECENT ACTIVITY</div>", unsafe_allow_html=True)
    
    if st.session_state.recent_activity:
        for activity in st.session_state.recent_activity:
            st.markdown(f"<div class='history-item'>💬 {activity}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.caption("No recent activity found.")

    st.sidebar.markdown(f"""
        <div style='position: fixed; bottom: 20px; width: 220px; font-size:11px; color:#444; border-top: 1px solid #222; padding-top:10px; margin-left:10px;'>
            ML & AI Engineer<br><b>Muhammad Faheem Riaz</b>
        </div>
    """, unsafe_allow_html=True)

# 6. MAIN CHAT AREA
st.markdown("<div style='text-align:center;'><h1>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. CHAT LOGIC
if prompt := st.chat_input("Message Feemo AI..."):
    # If starting a new session, save the title to Supabase
    if len(st.session_state.messages) == 0:
        try:
            title_text = prompt[:35] + "..." if len(prompt) > 35 else prompt
            supabase.table("chat_history").insert({"chat_title": title_text}).execute()
            st.session_state.recent_activity.insert(0, title_text)
        except Exception:
            pass # Silent fail for clean UI

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        now = datetime.datetime.now().strftime("%B %d, %Y")
        system_rules = f"You are Feemo AI. Today is {now}. Context: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_rules}] + st.session_state.messages,
            "temperature": 0.6
        }
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            reply = response.json()["choices"][0]["message"]["content"]
            
            # Smooth Typing Effect
            full_text = ""
            for char in reply:
                full_text += char
                placeholder.markdown(full_text + "▌")
                time.sleep(0.003)
            placeholder.markdown(full_text)
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
    except Exception:
        st.error("Connection Error.")
