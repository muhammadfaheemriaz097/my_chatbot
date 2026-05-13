import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE DATABASE
# Ensure secrets: SUPABASE_URL (no spaces!), SUPABASE_KEY, GROQ_API_KEY
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. SILENT DATA SYNC (Load Memory & Recent Activity)
if "bot_memory" not in st.session_state:
    try:
        # Load long-term context from user_memory table
        mem_res = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_res.data[0]['memory_context'] if mem_res.data else ""
        
        # Load existing history from chat_history table
        hist_res = supabase.table("chat_history").select("chat_title").order("created_at", desc=True).limit(10).execute()
        st.session_state.recent_activity = [row['chat_title'] for row in hist_res.data] if hist_res.data else []
    except Exception as e:
        st.session_state.bot_memory = ""
        st.session_state.recent_activity = []
        st.sidebar.error(f"Connection Error: {e}")

# 4. CHATGPT-STYLE CSS (Hamburger Menu & Button Styling)
st.markdown("""
    <style>
    /* UI Clean-up */
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
    
    /* RECENT ACTIVITY BUTTON STYLING */
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 25px 0 10px 10px; }
    
    /* Custom CSS to make st.button look like ChatGPT sidebar items */
    div[data-testid="stSidebar"] button {
        background-color: transparent !important;
        color: #d1d1d1 !important;
        border: 1px solid transparent !important;
        text-align: left !important;
        display: block !important;
        width: 100% !important;
        padding: 10px 15px !important;
        font-size: 14px !important;
        transition: 0.2s !important;
    }
    div[data-testid="stSidebar"] button:hover {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        color: #ffffff !important;
    }

    /* CHAT BUBBLES & LAYOUT */
    [data-testid="stChatMessage"] { border: none !important; padding: 2rem 1rem !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .block-container { max-width: 850px; padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (History with Clickable Buttons)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c; margin-left:10px;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    # New Chat Button
    if st.sidebar.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<div class='history-label'>RECENT ACTIVITY</div>", unsafe_allow_html=True)
    
    # Render Persistent History as Clickable Buttons
    if st.session_state.recent_activity:
        for idx, activity in enumerate(st.session_state.recent_activity):
            # Unique key for each button using index
            if st.sidebar.button(f"💬 {activity[:28]}...", key=f"hist_{idx}", use_container_width=True):
                # Functional placeholder: In the future, this will load the chat
                st.toast(f"Session '{activity}' selected.") 
    else:
        st.sidebar.caption("No recent activity.")

    # Developer Signature (Bottom)
    st.sidebar.markdown(f"""
        <div style='position: fixed; bottom: 20px; width: 220px; font-size:11px; color:#444; border-top: 1px solid #222; padding-top:10px; margin-left:10px;'>
            ML & AI Engineer<br><b>Muhammad Faheem Riaz</b>
        </div>
    """, unsafe_allow_html=True)

# 6. MAIN CHAT INTERFACE
st.markdown("<div style='text-align:center;'><h1>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display current chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. AI LOGIC & INSTANT HISTORY SYNC
if prompt := st.chat_input("Message Feemo AI..."):
    # Triggered only on the first message of a session
    if len(st.session_state.messages) == 0:
        try:
            title_text = prompt[:35] + "..." if len(prompt) > 35 else prompt
            
            # PUSH TO SUPABASE (Sync)
            supabase.table("chat_history").insert({"chat_title": title_text}).execute()
            
            # LOCAL UPDATE (Instant Visibility)
            if "recent_activity" not in st.session_state:
                st.session_state.recent_activity = []
            st.session_state.recent_activity.insert(0, title_text)
            
        except Exception as e:
            st.sidebar.error(f"Sync Error: {e}")

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Context Construction
        now = datetime.datetime.now().strftime("%B %d, %Y")
        system_rules = f"You are Feemo AI. Today is {now}."
        if st.session_state.bot_memory:
            system_rules += f" User Context: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_rules}] + st.session_state.messages,
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
            
    except Exception:
        st.error("Connection lost.")
