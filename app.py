import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE DATABASE CONNECTION
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. SILENT DATA SYNC (Memory & Recent Activity)
if "bot_memory" not in st.session_state:
    try:
        # Fetch user context silently from Supabase
        mem_res = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_res.data[0]['memory_context'] if mem_res.data else ""
        
        # Fetch last 10 chat titles for the sidebar
        hist_res = supabase.table("chat_history").select("chat_title").order("created_at", desc=True).limit(10).execute()
        st.session_state.recent_activity = [row['chat_title'] for row in hist_res.data] if hist_res.data else []
    except Exception:
        st.session_state.bot_memory = ""
        st.session_state.recent_activity = []

# 4. CHATGPT-STYLE CSS INTERFACE
st.markdown("""
    <style>
    /* UI Clean-up */
    #MainMenu, footer, .stAppToolbar {visibility: hidden;}
    
    /* THE THREE-LINE (HAMBURGER) MENU ICON */
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

    /* DARK THEME COLORS */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* RECENT ACTIVITY ITEMS */
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 25px 0 10px 10px; }
    .history-item {
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 4px;
        font-size: 14px;
        color: #d1d1d1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: 0.2s;
    }
    .history-item:hover { background-color: #1a1a1a; cursor: default; }

    /* CHAT BUBBLE STYLING */
    [data-testid="stChatMessage"] { border: none !important; padding: 2rem 1rem !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }

    /* CENTERED CHAT CONTAINER */
    .block-container { max-width: 850px; padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (Activity List)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c; margin-left:10px;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<div class='history-label'>RECENT ACTIVITY</div>", unsafe_allow_html=True)
    
    # Render Persistent History
    if st.session_state.recent_activity:
        for activity in st.session_state.recent_activity:
            st.markdown(f"<div class='history-item'>💬 {activity}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.caption("No recent activity found.")

    # Sidebar Branding
    st.sidebar.markdown(f"""
        <div style='position: fixed; bottom: 20px; width: 220px; font-size:11px; color:#333; border-top: 1px solid #222; padding-top:10px; margin-left:10px;'>
            ML & AI Engineer<br><b style='color:#555;'>Muhammad Faheem Riaz</b>
        </div>
    """, unsafe_allow_html=True)

# 6. MAIN CHAT AREA
st.markdown("<div style='text-align:center;'><h1>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display session chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. AI LOGIC & PERMANENT STORAGE
if prompt := st.chat_input("Message Feemo AI..."):
    # HISTORY LOGIC: Save the first message as a "Recent Activity" title
    if len(st.session_state.messages) == 0:
        try:
            title_text = prompt[:35] + "..." if len(prompt) > 35 else prompt
            supabase.table("chat_history").insert({"chat_title": title_text}).execute()
            # Update the sidebar state immediately
            st.session_state.recent_activity.insert(0, title_text)
        except Exception:
            pass # Fails silently to prevent UI disruption

    # UI Update
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Context Injection: Date + Silent Memory
        now = datetime.datetime.now().strftime("%B %d, %Y")
        system_context = f"You are Feemo AI. Today is {now}."
        if st.session_state.bot_memory:
            system_context += f" User Context: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_context}] + st.session_state.messages,
            "temperature": 0.6
        }
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            
            # Smooth Typing Animation
            full_text = ""
            for char in reply:
                full_text += char
                placeholder.markdown(full_text + "▌")
                time.sleep(0.003)
            placeholder.markdown(full_text)
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
    except Exception as e:
        st.error("I'm having trouble connecting right now. Please check your internet or API key.")
