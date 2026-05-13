import streamlit as st
import requests
import time
import datetime
import uuid
from supabase import create_client

# 1. INITIALIZE DATABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. PERSISTENT IDENTITY (URL-based stability)
# This keeps your ID the same even if you refresh the browser.
query_params = st.query_params
if "id" not in query_params:
    new_id = str(uuid.uuid4())[:8]
    st.query_params["id"] = new_id
    user_id = new_id
else:
    user_id = query_params["id"]

st.session_state.user_secret_id = user_id

# 4. DATA SYNC (Filtered by User ID)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# Load memory context
if "bot_memory" not in st.session_state:
    try:
        mem_res = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_res.data[0]['memory_context'] if mem_res.data else ""
    except:
        st.session_state.bot_memory = ""

# Fetch personal history
try:
    hist_res = supabase.table("chat_history")\
        .select("id, chat_title")\
        .eq("user_id", st.session_state.user_secret_id)\
        .order("created_at", desc=True)\
        .limit(10).execute()
    recent_activity = hist_res.data if hist_res.data else []
except:
    recent_activity = []

# 5. ADVANCED CSS (Mobile Fix + Professional Theme)
st.markdown("""
    <style>
    /* HIDE STREAMLIT/GITHUB OVERLAYS (Mobile & Desktop) */
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    [data-testid="stAppToolbar"] {display: none !important;}
    
    /* CUSTOM HAMBURGER MENU */
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
        z-index: 999999 !important;
    }

    /* DARK THEME COLORS */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* SIDEBAR BUTTONS */
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 25px 0 10px 10px; }
    div[data-testid="stSidebar"] button {
        background-color: transparent !important;
        color: #d1d1d1 !important;
        border: none !important;
        text-align: left !important;
        display: block !important;
        width: 100% !important;
        padding: 10px 15px !important;
    }
    div[data-testid="stSidebar"] button:hover { background-color: #1a1a1a !important; color: #ffffff !important; }

    /* CHAT BUBBLES */
    [data-testid="stChatMessage"] { border: none !important; padding: 2.5rem 1rem !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }

    /* LAYOUT REFINEMENT */
    .block-container { max-width: 850px; padding-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 6. SIDEBAR (Navigation & History)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c; margin-left:10px;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.markdown("<div class='history-label'>MY RECENT ACTIVITY</div>", unsafe_allow_html=True)
    
    for chat in recent_activity:
        if st.sidebar.button(f"💬 {chat['chat_title'][:25]}...", key=f"btn_{chat['id']}", use_container_width=True):
            try:
                msg_res = supabase.table("chat_history").select("full_history").eq("id", chat['id']).execute()
                if msg_res.data:
                    st.session_state.messages = msg_res.data[0]['full_history']
                    st.session_state.current_chat_id = chat['id']
                    st.rerun()
            except:
                st.sidebar.error("Error loading chat.")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"ID: {st.session_state.user_secret_id}")
    st.sidebar.markdown(f"<div style='font-size:11px; color:#444; margin-left:10px;'>ML & AI Engineer<br><b>Muhammad Faheem Riaz</b></div>", unsafe_allow_html=True)

# 7. MAIN CHAT AREA
st.markdown("<div style='text-align:center; margin-bottom:20px;'><h1>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. AI LOGIC & PERSISTENCE
if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        now = datetime.datetime.now().strftime("%B %d, %Y")
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": f"You are Feemo AI. Date: {now}. Context: {st.session_state.bot_memory}"}] + st.session_state.messages,
            "temperature": 0.6
        }
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            reply = response.json()["choices"][0]["message"]["content"]
            
            # Streaming effect
            full_text = ""
            for char in reply:
                full_text += char
                placeholder.markdown(full_text + "▌")
                time.sleep(0.002)
            placeholder.markdown(full_text)
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # SAVE TO SUPABASE
        if st.session_state.current_chat_id is None:
            new_chat = supabase.table("chat_history").insert({
                "chat_title": prompt[:30],
                "full_history": st.session_state.messages,
                "user_id": st.session_state.user_secret_id 
            }).execute()
            st.session_state.current_chat_id = new_chat.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.current_chat_id).execute()
            
    except Exception as e:
        st.error("Error processing message.")
