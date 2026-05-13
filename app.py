import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE SUPABASE
# Make sure SUPABASE_URL and SUPABASE_KEY are in your Streamlit Secrets
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

# 4. ADVANCED CSS (Mobile Fix & Dark Theme)
st.markdown("""
    <style>
    /* 1. HIDE DEFAULT UI ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppToolbar {visibility: hidden;}
    
    /* 2. FORCE MOBILE SIDEBAR BUTTON VISIBILITY */
    /* This overrides the 'header hidden' rule just for the toggle button */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
        background-color: rgba(201, 168, 76, 0.15) !important;
        border-radius: 8px !important;
        color: #c9a84c !important;
        top: 15px !important;
        left: 15px !important;
    }

    /* 3. THEME STYLING */
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
    
    /* Input & Message Styling */
    .stChatInput input { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #c9a84c !important; border-radius: 12px !important; }
    .stChatMessage { background-color: #111111 !important; border-radius: 12px !important; border-left: 3px solid #c9a84c !important; margin-bottom: 12px !important; }
    
    /* Typography */
    h1, h2, h3 { color: #c9a84c !important; font-family: 'Georgia', serif !important; }
    p { font-size: 16px !important; line-height: 1.6 !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR SECTION
with st.sidebar:
    # Logo Logic
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align:center;'>🤖</h1>", unsafe_allow_html=True)
        
    st.markdown("<div style='text-align:center;'><h2 style='margin:0;'>Feemo AI</h2><p style='color:#8b6914;font-size:12px;'>Your Smart AI Assistant</p></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # PERMANENT MEMORY BOX
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>🧠 Assistant Memory</p>", unsafe_allow_html=True)
    user_input_memory = st.sidebar.text_area(
        "Long-term context (Saved to Cloud):",
        value=st.session_state.bot_memory,
        height=180,
        key="memory_box"
    )

    if st.sidebar.button("💾 Save to Cloud"):
        try:
            supabase.table("user_memory").upsert({
                "id": 1, 
                "user_name": "Faheem", 
                "memory_context": user_input_memory
            }).execute()
            st.session_state.bot_memory = user_input_memory
            st.sidebar.success("Memory updated in Supabase!")
        except Exception as e:
            st.sidebar.error(f"Save failed: {e}")

    st.sidebar.markdown("---")
    st.sidebar.write("👤 **Developer**")
    st.sidebar.write("Muhammad Faheem Riaz")
    
    if st.sidebar.button("🗑️ Clear Current Chat"):
        st.session_state.messages = []
        st.rerun()

# 6. MAIN CHAT INTERFACE
st.markdown("<div style='text-align:center; padding-top:20px;'><h1 style='font-size:42px; letter-spacing:2px;'>✦ FEEMO AI ✦</h1><p style='color:#8b6914; font-size:14px;'>Powered by Groq AI — Ultra Fast</p><hr style='border-color:#c9a84c; opacity:0.2;'></div>", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Message History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<p style='color:#ffffff;'>{msg['content']}</p>", unsafe_allow_html=True)

# 7. CHAT LOGIC (Date + Memory Injection)
if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"<p style='color:#ffffff;'>{prompt}</p>", unsafe_allow_html=True)
    
    try:
        # Dynamic Date Calculation
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # System Message: Gives the AI the Date and your Supabase Memory
        system_instruction = f"You are Feemo AI. Today's date is {today}."
        if st.session_state.bot_memory:
            system_instruction += f" Important information about the user: {st.session_state.bot_memory}"
        
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_instruction}] + st.session_state.messages,
            "max_tokens": 1024,
            "temperature": 0.6
        }
        
        with st.chat_message("assistant"):
            with st.spinner("✦ Thinking..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                result = response.json()
                
                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    
                    # Typing Animation Effect
                    placeholder = st.empty()
                    chunk = ""
                    for char in reply:
                        chunk += char
                        placeholder.markdown(f"<p style='color:#c9a84c;'>{chunk}▌</p>", unsafe_allow_html=True)
                        time.sleep(0.005)
                    placeholder.markdown(f"<p style='color:#ffffff;'>{reply}</p>", unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    st.error("API Error: Check Groq Console.")

    except Exception as e:
        st.error(f"Error: {e}")
