import streamlit as st
import requests
import time
import datetime

# 1. SET PAGE CONFIG (Favicon and Title)
# Using a stable emoji until your logo.png is confirmed in the GitHub root
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="✨", 
    layout="centered"
)

# 2. CUSTOM CSS (Hide UI and Theme Styling)
st.markdown("""
    <style>
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppToolbar {visibility: hidden;}
    
    /* Dark Theme Styles */
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    .stChatInput input { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #c9a84c !important; border-radius: 12px !important; }
    .stChatMessage { background-color: #1a1a1a !important; border-radius: 12px !important; border-left: 3px solid #c9a84c !important; margin-bottom: 10px !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
    h1, h2 { color: #c9a84c !important; font-family: 'Georgia', serif !important; }
    
    /* Memory Box Styling */
    .stTextArea textarea { background-color: #1a1a1a !important; color: #c9a84c !important; border: 1px solid #333 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR SECTION
with st.sidebar:
    # --- LOGO ---
    # Using the local file method with a fallback
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align:center;'>🤖</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align:center;'><h2 style='margin:0;'>Feemo AI</h2><p style='color:#8b6914;font-size:12px;'>Your Smart AI Assistant</p></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # --- MEMORY FEATURE ---
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>🧠 Assistant Memory</p>", unsafe_allow_html=True)
    if "bot_memory" not in st.session_state:
        st.session_state.bot_memory = ""
    
    st.session_state.bot_memory = st.sidebar.text_area(
        "Tell Feemo AI what to remember about you:",
        value=st.session_state.bot_memory,
        placeholder="e.g. My name is Faheem, I'm an ML Engineer...",
        height=120
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>👤 Created by</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#ffffff;font-size:14px;'>Muhammad Faheem Riaz</p>", unsafe_allow_html=True)
    
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# 4. MAIN INTERFACE HEADER
st.markdown("<div style='text-align:center;'><h1 style='font-size:42px;'>✦ FEEMO AI ✦</h1><p style='color:#8b6914;'>Powered by Groq AI — Fast & Intelligent</p></div>", unsafe_allow_html=True)

# 5. CORE CHAT LOGIC
API_KEY = st.secrets["GROQ_API_KEY"]

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<p style='color:#ffffff; font-size:16px;'>{msg['content']}</p>", unsafe_allow_html=True)

# 6. INPUT AND API CALL
if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"<p style='color:#ffffff; font-size:16px;'>{prompt}</p>", unsafe_allow_html=True)

    try:
        # Get Current Date to give to the AI
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Build System Instructions (Date + Memory)
        system_content = f"You are Feemo AI, a helpful assistant. Today's date is {current_date}."
        if st.session_state.bot_memory:
            system_content += f" User Context to remember: {st.session_state.bot_memory}"
        
        # Merge System prompt with chat history
        api_messages = [{"role": "system", "content": system_content}] + st.session_state.messages

        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": api_messages,
            "max_tokens": 1024,
            "temperature": 0.7
        }

        with st.chat_message("assistant"):
            with st.spinner("✦ Thinking..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                result = response.json()
                
                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    
                    # Typing Effect
                    placeholder = st.empty()
                    full_response = ""
                    for char in reply:
                        full_response += char
                        placeholder.markdown(f"<p style='color:#c9a84c; font-size:16px;'>{full_response}▌</p>", unsafe_allow_html=True)
                        time.sleep(0.005)
                    placeholder.markdown(f"<p style='color:#ffffff; font-size:16px;'>{reply}</p>", unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    st.error("API Error. Please check your Groq API key.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
