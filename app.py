import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE SUPABASE
# These must be set in Streamlit Cloud -> Settings -> Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. SET PAGE CONFIG
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="✨", 
    layout="centered"
)

# 3. LOAD PERSISTENT MEMORY FROM SUPABASE
if "bot_memory" not in st.session_state:
    try:
        response = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        if response.data:
            st.session_state.bot_memory = response.data[0]['memory_context']
        else:
            st.session_state.bot_memory = ""
    except Exception:
        st.session_state.bot_memory = ""

# 4. ADVANCED CSS (Mobile Sidebar Fix & Gold Theme)
st.markdown("""
    <style>
    /* Hiding specific UI pieces but KEEPING the sidebar toggle active */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppToolbar {visibility: hidden;}
    
    /* THE MOBILE SIDEBAR FIX: Create a visible Gold Toggle Button */
    button[kind="headerNoPadding"] {
        background-color: #c9a84c !important;
        color: #000000 !important;
        border-radius: 50% !important;
        margin-left: 10px !important;
        margin-top: 5px !important;
        visibility: visible !important;
    }

    /* Main Theme Colors */
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    section[data-testid="stSidebar"] { 
        background-color: #111111 !important; 
        border-right: 1px solid #c9a84c !important; 
    }
    
    /* Input & Chat Styling */
    .stChatInput input { 
        background-color: #1a1a1a !important; 
        color: #ffffff !important; 
        border: 1px solid #c9a84c !important; 
        border-radius: 12px !important; 
    }
    .stChatMessage { 
        background-color: #111111 !important; 
        border-radius: 12px !important; 
        border-left: 3px solid #c9a84c !important; 
        margin-bottom: 12px !important; 
    }
    
    /* Gold Headers */
    h1, h2 { color: #c9a84c !important; font-family: 'Georgia', serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR SECTION
with st.sidebar:
    # Logo Fallback
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align:center;'>🤖</h1>", unsafe_allow_html=True)
        
    st.markdown("<div style='text-align:center;'><h2 style='margin:0;'>Feemo AI</h2><p style='color:#8b6914;font-size:12px;'>Your Smart AI Assistant</p></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # CLOUD MEMORY INTERFACE
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>🧠 Permanent Memory</p>", unsafe_allow_html=True)
    user_input_memory = st.sidebar.text_area(
        "Saved context (available across sessions):",
        value=st.session_state.bot_memory,
        height=180,
        key="cloud_memory"
    )

    if st.sidebar.button("💾 Save to Cloud"):
        try:
            supabase.table("user_memory").upsert({
                "id": 1, 
                "user_name": "Faheem", 
                "memory_context": user_input_memory
            }).execute()
            st.session_state.bot_memory = user_input_memory
            st.sidebar.success("Cloud memory updated!")
        except Exception as e:
            st.sidebar.error("Failed to connect to Supabase.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>👤 Created by</p>", unsafe_allow_html=True)
    st.sidebar.write("Muhammad Faheem Riaz")
    
    if st.sidebar.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

# 6. MAIN CHAT INTERFACE
st.markdown("<div style='text-align:center; padding-top:10px;'><h1 style='font-size:42px; letter-spacing:2px;'>✦ FEEMO AI ✦</h1><p style='color:#8b6914;'>Fast & Intelligent</p></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<p style='color:#ffffff;'>{msg['content']}</p>", unsafe_allow_html=True)

# 7. CHAT LOGIC (Date + Persistent Memory)
if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"<p style='color:#ffffff;'>{prompt}</p>", unsafe_allow_html=True)
    
    try:
        # Get live date
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Inject context into the brain
        system_rules = f"You are Feemo AI. Today is {today}."
        if st.session_state.bot_memory:
            system_rules += f" Context about the user: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_rules}] + st.session_state.messages,
            "max_tokens": 1024
        }
        
        with st.chat_message("assistant"):
            with st.spinner("✦ Processing..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                result = response.json()
                
                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    
                    # Typing effect
                    placeholder = st.empty()
                    typed = ""
                    for char in reply:
                        typed += char
                        placeholder.markdown(f"<p style='color:#c9a84c;'>{typed}▌</p>", unsafe_allow_html=True)
                        time.sleep(0.005)
                    placeholder.markdown(f"<p style='color:#ffffff;'>{reply}</p>", unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"Error connecting to AI: {e}")
