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

# 3. LOAD PERSISTENT MEMORY
if "bot_memory" not in st.session_state:
    try:
        response = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        if response.data:
            st.session_state.bot_memory = response.data[0]['memory_context']
        else:
            st.session_state.bot_memory = ""
    except Exception:
        st.session_state.bot_memory = ""

# 4. CHATGPT LAYOUT CSS
st.markdown("""
    <style>
    /* HIDE DEFAULT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppToolbar {visibility: hidden;}
    
    /* 1. CHATGPT THREE-LINE MENU ICON (Mobile & Desktop) */
    button[kind="headerNoPadding"] svg {
        display: none; /* Hide default arrow */
    }
    button[kind="headerNoPadding"]::after {
        content: '☰'; /* The Three Lines */
        font-size: 24px;
        color: #c9a84c;
        visibility: visible !important;
        display: block;
    }
    button[kind="headerNoPadding"] {
        background-color: transparent !important;
        border: 1px solid rgba(201, 168, 76, 0.3) !important;
        border-radius: 8px !important;
        padding: 5px 10px !important;
        margin-left: 15px !important;
    }

    /* 2. CENTERED CHAT LAYOUT (ChatGPT Style) */
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }

    /* 3. DARK THEME & MESSAGE BUBBLES */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* User Message Bubble */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: transparent !important;
    }
    
    /* Assistant Message Bubble */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1a1a1a !important;
        border-radius: 12px;
    }

    /* Chat Input Styling */
    .stChatInput input { 
        background-color: #1a1a1a !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important; 
        border-radius: 12px !important;
        padding: 12px !important;
    }
    
    h1 { color: #ffffff !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (History & Memory)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("🧠 **Personalization**")
    user_input_memory = st.sidebar.text_area(
        "Memory context:",
        value=st.session_state.bot_memory,
        height=150,
        key="cloud_mem"
    )

    if st.sidebar.button("💾 Update Memory"):
        try:
            supabase.table("user_memory").upsert({
                "id": 1, 
                "user_name": "Faheem", 
                "memory_context": user_input_memory
            }).execute()
            st.session_state.bot_memory = user_input_memory
            st.sidebar.success("Updated!")
        except:
            st.sidebar.error("Cloud Error")

    st.sidebar.markdown("---")
    st.sidebar.caption("Developed by Muhammad Faheem Riaz")
    if st.sidebar.button("🗑️ New Chat"):
        st.session_state.messages = []
        st.rerun()

# 6. MAIN CHAT AREA
st.markdown("<div style='text-align:center;'><h1 style='font-size:32px;'>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. CHAT LOGIC
if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        today = datetime.datetime.now().strftime("%B %d, %Y")
        system_rules = f"You are Feemo AI. Today is {today}. Context: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_rules}] + st.session_state.messages,
            "max_tokens": 1024
        }
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            reply = response.json()["choices"][0]["message"]["content"]
            
            # Simplified typing effect for ChatGPT feel
            full_response = ""
            for char in reply:
                full_response += char
                placeholder.markdown(full_response + "●")
                time.sleep(0.005)
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
    except Exception as e:
        st.error("Connection lost.")
