import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE DATABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. ADVANCED CSS
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #2d2d2d !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .block-container { max-width: 850px; padding-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. AUTHENTICATION & PERSONALIZED WELCOME
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<div style='text-align:center;'><h1>✦ FEEMO AI ✦</h1><p>Welcome! Please sign in to access your workspace.</p></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Forgot Password"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In", use_container_width=True):
            try:
                auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if auth_res.user:
                    st.session_state.user_secret_id = auth_res.user.id
                    # Retrieve the name from metadata
                    st.session_state.first_name = auth_res.user.user_metadata.get("first_name", "User")
                    st.session_state.authenticated = True
                    st.toast(f"Welcome back, {st.session_state.first_name}!")
                    time.sleep(1)
                    st.rerun()
            except:
                st.error("Invalid credentials.")
    
    with tab2:
        reg_name = st.text_input("First Name", placeholder="e.g. Faheem")
        reg_email = st.text_input("Email", key="reg_email")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Create Account", use_container_width=True):
            try:
                # We pass the name into 'options' so Supabase saves it in metadata
                supabase.auth.sign_up({
                    "email": reg_email, 
                    "password": reg_pass,
                    "options": {"data": {"first_name": reg_name}}
                })
                st.success(f"Account created for {reg_name}! Check your email to verify.")
            except Exception as e:
                st.error(f"Signup failed: {e}")

    with tab3:
        reset_email = st.text_input("Enter email for reset link")
        if st.button("Send Reset Link"):
            try:
                supabase.auth.reset_password_for_email(reset_email)
                st.success("Reset link sent!")
            except:
                st.error("Error sending link.")
    st.stop()

# 5. DATA SYNC
if "messages" not in st.session_state: st.session_state.messages = []
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None

# 6. SIDEBAR
with st.sidebar:
    st.markdown(f"<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.caption(f"👋 Hello, {st.session_state.first_name}")
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    # ... (Your History Loading Logic Here) ...

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.rerun()

# 7. MAIN CHAT AREA
st.markdown(f"<h3 style='text-align:center;'>How can I help you today, {st.session_state.first_name}?</h3>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. AI LOGIC (Personalized)
if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        # 🤖 SYSTEM PROMPT PERSONALIZATION
        sys_prompt = f"You are Feemo AI. You are talking to {st.session_state.first_name}, who is an ML & AI Engineer. Be helpful and professional."
        
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": sys_prompt}] + st.session_state.messages
        }
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # ... (Your Save to Supabase Logic Here) ...
            
    except:
        st.error("AI Connection Error.")
