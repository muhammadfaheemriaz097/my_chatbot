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
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="centered")

# 3. LOAD PERSISTENT MEMORY FROM SUPABASE
if "bot_memory" not in st.session_state:
    try:
        # Pull the context from your user_memory table
        response = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        if response.data:
            st.session_state.bot_memory = response.data[0]['memory_context']
        else:
            st.session_state.bot_memory = ""
    except Exception:
        st.session_state.bot_memory = ""

# 4. CUSTOM CSS (Hide UI and Theme Styling)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .stAppToolbar {visibility: hidden;}
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
    .stChatInput input { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #c9a84c !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR
with st.sidebar:
    # Try to load local logo.png
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align:center;'>🤖</h1>", unsafe_allow_html=True)
        
    st.markdown("<h2 style='text-align:center;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>🧠 Permanent Memory</p>", unsafe_allow_html=True)
    
    # Editable memory box
    user_input_memory = st.sidebar.text_area(
        "Edit your long-term context:",
        value=st.session_state.bot_memory,
        height=150,
        key="memory_area"
    )

    # Save button to push to Cloud
    if st.sidebar.button("💾 Save to Cloud"):
        supabase.table("user_memory").upsert({
            "id": 1, 
            "user_name": "Faheem", 
            "memory_context": user_input_memory
        }).execute()
        st.session_state.bot_memory = user_input_memory
        st.sidebar.success("Memory saved to Supabase!")

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# 6. MAIN CHAT INTERFACE
st.markdown("<div style='text-align:center;'><h1 style='font-size:42px;'>✦ FEEMO AI ✦</h1><p style='color:#8b6914;'>Your Smart AI Assistant</p></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display current session history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<p style='color:#ffffff;'>{msg['content']}</p>", unsafe_allow_html=True)

# 7. AI LOGIC (DATE + MEMORY)
if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"<p style='color:#ffffff;'>{prompt}</p>", unsafe_allow_html=True)
    
    try:
        # Today's Date Context
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Build System Instruction with Supabase Memory
        system_content = f"You are Feemo AI. Today's date is {today}."
        if st.session_state.bot_memory:
            system_content += f" Remember this about the user: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_content}] + st.session_state.messages,
            "max_tokens": 1024
        }
        
        with st.chat_message("assistant"):
            with st.spinner("✦ Thinking..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
                result = response.json()
                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    
                    # Typing animation
                    placeholder = st.empty()
                    typed = ""
                    for char in reply:
                        typed += char
                        placeholder.markdown(f"<p style='color:#c9a84c;'>{typed}▌</p>", unsafe_allow_html=True)
                        time.sleep(0.005)
                    placeholder.markdown(f"<p style='color:#ffffff;'>{reply}</p>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"Error: {e}")
