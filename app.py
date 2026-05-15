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

# 3. ADVANCED CSS (Logo Styling + UI Refinement)
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    /* Logo Container Styling */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px 0;
        margin-bottom: 20px;
    }
    .logo-text {
        font-size: 55px;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(45deg, #c9a84c, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 10px 20px rgba(201, 168, 76, 0.2);
    }
    
    /* Sidebar & Theme Styling */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #2d2d2d !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .block-container { max-width: 850px; padding-top: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. AUTHENTICATION LOGIC
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["SIGN IN", "CREATE ACCOUNT"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if auth_res.user:
                        st.session_state.user_secret_id = auth_res.user.id
                        st.session_state.first_name = auth_res.user.user_metadata.get("first_name", "User")
                        st.session_state.authenticated = True
                        st.rerun()
                except:
                    st.error("Login failed.")
    
    with tab2:
        with st.form("signup_form"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_pass = st.text_input("Create Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                if new_pass == confirm_pass:
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_pass, "options": {"data": {"first_name": new_name}}})
                        st.success("Verification email sent!")
                    except:
                        st.error("Error during registration.")
                else:
                    st.warning("Passwords mismatch.")
    st.stop()

# --- 5. THE 2-SEC POPUP LOGIC ---
if not st.session_state.welcome_shown:
    welcome_placeholder = st.empty()
    with welcome_placeholder.container():
        st.markdown(f"""
            <div style="background-color: #c9a84c; padding: 20px; border-radius: 10px; text-align: center; color: black; font-weight: bold; margin-bottom: 20px;">
                🚀 Welcome back, {st.session_state.first_name}! Syncing your workspace...
            </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
    welcome_placeholder.empty() # Removes the popup after 2 seconds
    st.session_state.welcome_shown = True

# 6. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.caption(f"👤 {st.session_state.first_name}")
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.welcome_shown = False
        st.rerun()

# --- 7. MAIN LOGO (Appears after welcome popup disappears) ---
st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

# 8. CHAT LOGIC
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI Logic (Simplified for code length)
    try:
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": f"You are Feemo AI. Helper to {st.session_state.first_name}"}] + st.session_state.messages}
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
    except:
        st.error("Error connecting to AI.")
