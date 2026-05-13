import streamlit as st
import requests
import time

# 1. THE LOGO LINK
# This is the Raw GitHub URL. 
# IMPORTANT: Ensure your GitHub Repository is set to "PUBLIC"
logo_url = "https://raw.githubusercontent.com/muhammadfaheemriaz097/my_chatbot/main/logo.png"

# 2. SET PAGE CONFIG
st.set_page_config(
    page_title="Feemo AI", 
    page_icon=logo_url, 
    layout="centered"
)

# 3. HIDE UI ELEMENTS & CUSTOM CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppToolbar {visibility: hidden;}
    
    .stApp { background-color: #0a0a0a; color: #ffffff; }
    .stChatInput input { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #c9a84c !important; border-radius: 12px !important; }
    .stChatMessage { background-color: #1a1a1a !important; border-radius: 12px !important; border-left: 3px solid #c9a84c !important; margin-bottom: 10px !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
    h1 { color: #c9a84c !important; font-family: 'Georgia', serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. SIDEBAR SECTION
with st.sidebar:
    # This is the simplest way to show an image in Streamlit
    st.image(logo_url, use_container_width=True)
    
    st.markdown("""
    <div style='text-align:center;padding:0 0 20px 0;'>
        <h2 style='color:#c9a84c;margin:0;'>Feemo AI</h2>
        <p style='color:#8b6914;font-size:12px;'>Your Smart AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>👤 Created by</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#ffffff;font-size:15px;font-weight:bold;'>Muhammad Faheem Riaz</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>💡 You can ask me about</p>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='color:#cccccc;font-size:13px;line-height:2;'>✦ General knowledge<br>✦ Writing and emails<br>✦ Coding help<br>✦ Study and learning</p>", unsafe_allow_html=True)

    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# 5. MAIN INTERFACE
st.markdown("<div style='text-align:center;'><h1 style='font-size:42px;'>✦ FEEMO AI ✦</h1><p style='color:#8b6914;'>Powered by Groq AI — Fast and Intelligent</p></div>", unsafe_allow_html=True)

# 6. API LOGIC
API_KEY = st.secrets["GROQ_API_KEY"]

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(f"<p style='color:#ffffff;'>{msg['content']}</p>", unsafe_allow_html=True)

if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"<p style='color:#ffffff;'>{prompt}</p>", unsafe_allow_html=True)
    
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        data = {"model": "llama-3.3-70b-versatile", "messages": st.session_state.messages, "max_tokens": 1000}
        
        with st.chat_message("assistant"):
            with st.spinner("✦ Thinking..."):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
                result = response.json()
                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    st.markdown(f"<p style='color:#c9a84c;'>{reply}</p>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        st.error(f"Error: {str(e)}")
