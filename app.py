import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE SUPABASE
# Secrets: SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. SET PAGE CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. SILENT DATA LOAD (Memory & Recent Activity)
if "bot_memory" not in st.session_state:
    try:
        # Load user context silently
        mem_res = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_res.data[0]['memory_context'] if mem_res.data else ""
        
        # Load Recent Activity titles
        hist_res = supabase.table("chat_history").select("chat_title").order("created_at", desc=True).limit(10).execute()
        st.session_state.recent_activity = [row['chat_title'] for row in hist_res.data] if hist_res.data else []
    except Exception:
        st.session_state.bot_memory = ""
        st.session_state.recent_activity = []

# 4. CHATGPT-STYLE CSS
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
    }

    /* DARK THEME & LAYOUT */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* RECENT ACTIVITY LIST */
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin-top: 20px; margin-bottom: 10px; }
    .history-item {
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-size: 14px;
        color: #d1d1d1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border: 1px solid transparent;
    }
    .history-item:hover { background-color: #1a1a1a; border: 1px solid #333; }

    /* CHAT BUBBLES */
    [data-testid="stChatMessage"] { border-radius: 0px !important; border: none !important; padding: 1.5rem 1rem !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }

    /* CENTERED CONTENT BOX */
    .block-container { max-width: 850px; padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (Clean ChatGPT Style)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c; margin-bottom:20px;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<div class='history-label'>RECENT ACTIVITY</div>", unsafe_allow_html=True)
    
    # Display History from Database
    if st.session_state.recent_activity:
        for activity in st.session_state.recent_activity:
            st.markdown(f"<div class='history-item'>💬 {activity}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.caption("No recent chats found.")

    # Fixed footer for branding
    st.sidebar.markdown("""
        <div style='position: fixed; bottom: 20px; width: 220px; font-size:12px; color:#444; border-top: 1px solid #222; padding-top:10px;'>
            ML & AI Engineer<br><b>Muhammad Faheem Riaz</b>
        </div>
    """, unsafe_allow_html=True)

# 6. MAIN CHAT AREA
st.markdown("<div style='text-align:center;'><h1 style='font-size:32px; letter-spacing:1px;'>✦ FEEMO AI ✦</h1><p style='color:#666; font-size:14px;'>Intelligent Assistant Powered by Llama 3.3</p></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display current session messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. CHAT LOGIC + HISTORY SAVING
if prompt := st.chat_input("Ask Feemo AI anything..."):
    # SAVE TO HISTORY: Only if this is the start of a conversation
    if len(st.session_state.messages) == 0:
        try:
            # We insert the first message as the 'Activity Title'
            title = prompt[:35] + "..." if len(prompt) > 35 else prompt
            supabase.table("chat_history").insert({"chat_title": title}).execute()
            # Update sidebar list immediately so user sees it
            st.session_state.recent_activity.insert(0, title)
        except Exception as e:
            # Silent fail for UI, but logs for dev
            pass

    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # System Injection: Date + Silent Memory Context
        today_date = datetime.datetime.now().strftime("%B %d, %Y")
        system_msg = f"You are Feemo AI. Today's date is {today_date}."
        if st.session_state.bot_memory:
            system_msg += f" Context about user: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_msg}] + st.session_state.messages,
            "temperature": 0.6
        }
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            
            # Smooth Typing Effect
            full_reply = ""
            for char in reply:
                full_reply += char
                placeholder.markdown(full_reply + "▌")
                time.sleep(0.004)
            placeholder.markdown(full_reply)
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
    except Exception as e:
        st.error("I'm having trouble connecting to the brain. Please try again.")
