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

# 3. LOAD DATA (Memory + Recent Activity)
if "bot_memory" not in st.session_state:
    try:
        # Load Memory
        mem_resp = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_resp.data[0]['memory_context'] if mem_resp.data else ""
        
        # Load Recent Activity (Last 10 prompts)
        hist_resp = supabase.table("chat_history").select("user_prompt").order("created_at", desc=True).limit(10).execute()
        st.session_state.recent_activity = [item['user_prompt'] for item in hist_resp.data] if hist_resp.data else []
    except:
        st.session_state.bot_memory = ""
        st.session_state.recent_activity = []

# 4. CHATGPT STYLE CSS
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden;}
    
    /* Hamburger Menu Icon */
    button[kind="headerNoPadding"] svg { display: none; }
    button[kind="headerNoPadding"]::after { content: '☰'; font-size: 24px; color: #c9a84c; visibility: visible !important; }
    button[kind="headerNoPadding"] { background-color: transparent !important; border: 1px solid #333 !important; border-radius: 8px !important; }

    /* Layout & Colors */
    .block-container { max-width: 800px; padding-top: 2rem; }
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #2d2d2d !important; }
    
    /* Recent Activity Links */
    .activity-link {
        padding: 8px;
        color: #8e8ea0;
        font-size: 14px;
        border-radius: 5px;
        cursor: pointer;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .activity-link:hover { background-color: #2d2d2d; color: #fff; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (Activity & Memory)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("+ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("🕒 **Recent Activity**")
    for activity in st.session_state.recent_activity:
        # Show first 25 characters of recent prompts
        st.markdown(f"<div class='activity-link'>💬 {activity[:25]}...</div>", unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("🧠 **Memory**")
    user_input_memory = st.sidebar.text_area("Context:", value=st.session_state.bot_memory, height=100)
    if st.sidebar.button("💾 Save Memory"):
        supabase.table("user_memory").upsert({"id": 1, "memory_context": user_input_memory}).execute()
        st.rerun()

# 6. MAIN CHAT
st.markdown("<div style='text-align:center;'><h1>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. LOGIC: SAVE TO HISTORY ON SEND
if prompt := st.chat_input("Message Feemo AI..."):
    # SAVE TO SUPABASE IMMEDIATELY
    try:
        supabase.table("chat_history").insert({"user_prompt": prompt}).execute()
    except:
        pass
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # API CALL
    try:
        today = datetime.datetime.now().strftime("%B %d, %Y")
        system_rules = f"You are Feemo AI. Today is {today}. Context: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_rules}] + st.session_state.messages
        }
        
        with st.chat_message("assistant"):
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            reply = response.json()["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
    except:
        st.error("Error connecting to AI.")
