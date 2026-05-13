import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE SUPABASE
# Ensure these secrets are set in Streamlit Cloud Settings -> Secrets
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

# 4. CUSTOM CSS (Mobile Fix & Theme Styling)
st.markdown("""
    <style>
    /* Hiding unnecessary UI but KEEPING the sidebar toggle button for mobile */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppToolbar {visibility: hidden;}
    
    /* Force the Sidebar Toggle Button to be visible and Gold on Mobile */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        background-color: rgba(201, 168, 76, 0.1) !important;
        border-radius: 50% !important;
        color: #c9a84c !important;
    }

    /* Main Theme Colors */
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    .stChatInput input { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #c9a84c !important; border-radius: 12px !important; }
    .stChatMessage { background-color: #1a1a1a !important; border-radius: 12px !important; border-left: 3px solid #c9a84c !important; margin-bottom: 10px !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
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
    
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>🧠 Permanent Memory</p>", unsafe_allow_html=True)
    
    # Persistent Memory Area
    user_input_memory = st.sidebar.text_area(
        "Edit your long-term context:",
        value=st.session_state.bot_memory,
        height=150,
        key="memory_area"
    )

    if st.sidebar.button("💾 Save to Cloud"):
        supabase.table("user_memory").upsert({
            "id": 1, 
            "user_name": "Faheem", 
            "memory_context": user_input_memory
        }).execute()
        st.session_state.bot_memory = user_input_memory
        st.sidebar.success("Memory saved to Cloud!")

    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>👤 Created by</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#ffffff;font-size:15px;font-weight:bold;'>Muhammad Faheem Riaz</p>", unsafe_allow_html=True)
    
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# 6. MAIN CHAT INTERFACE
st.markdown("<div style='text-align:center;'><h1 style='font-size:42px; letter-spacing:3px;'>✦ FEEMO AI ✦</h1><p style='color:#8b6914; font-size:14px;'>Powered by Groq AI — Fast and Intelligent</p><hr style='border-color:#c9a84c;opacity:0.3;'></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Session Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<p style='color:#ffffff; font-size:16px;'>{msg['content']}</p>", unsafe_allow_html=True)

# 7. AI LOGIC (Date + Memory Injection)
if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"<p style='color:#ffffff; font-size:16px;'>{prompt}</p>", unsafe_allow_html=True)
    
    try:
        # Generate current date
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # System Message Construction
        system_content = f"You are Feemo AI. Today's date is {today}."
        if st.session_state.bot_memory:
            system_content += f" Remember this about the user: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_content}] + st.session_state.messages,
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        with st.chat_message("assistant"):
            with st.spinner("✦ Feemo AI is thinking..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
                result = response.json()
                
                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    
                    # Animated Typing Effect
                    placeholder = st.empty()
                    typed_text = ""
                    for char in reply:
                        typed_text += char
                        placeholder.markdown(f"<p style='color:#c9a84c; font-size:16px;'>{typed_text}▌</p>", unsafe_allow_html=True)
                        time.sleep(0.005)
                    placeholder.markdown(f"<p style='color:#ffffff; font-size:16px;'>{reply}</p>", unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    st.error("API Response Error. Check your Groq quota.")

    except Exception as e:
        st.error(f"System Error: {e}")
