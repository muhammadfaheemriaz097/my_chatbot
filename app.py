import streamlit as st
import requests
import time
import PyPDF2
from supabase import create_client

# 1. DATABASE
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("Missing secrets.")
    st.stop()

# 2. APP CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

# 3. CSS (ONLY THE NECESSARY STUFF)
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .block-container { max-width: 800px; margin: auto; padding-top: 2rem !important; }

    /* GEMINI GRADIENT LOGO */
    .logo-container { text-align: center; padding: 20px 0; }
    .logo-text {
        font-size: 55px; font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    /* SIDEBAR THEME */
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. STATE
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

# 5. SIDEBAR (Defined early to force rendering)
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if st.session_state.authenticated:
        st.write(f"Logged in: {st.session_state.get('first_name', 'User')}")
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    else:
        st.info("Sidebar will show history once you log in.")

# 6. AUTH CALLBACK
def login_callback():
    try:
        res = supabase.auth.sign_in_with_password({"email": st.session_state.e_in, "password": st.session_state.p_in})
        if res.user:
            st.session_state.user_secret_id = res.user.id
            st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
            st.session_state.authenticated = True
    except: st.error("Login Error")

# 7. MAIN BODY
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><h1 class='logo-text'>Feemo AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    with t1:
        with st.form("l_form"):
            st.text_input("Email", key="e_in")
            st.text_input("Password", type="password", key="p_in")
            st.form_submit_button("SIGN IN", use_container_width=True, on_click=login_callback)
    with t2:
        st.write("Registration Form Placeholder") # Add your registration form here
    with t3:
        st.write("Reset Form Placeholder") # Add your reset form here
    
    if st.session_state.authenticated: st.rerun()
    st.stop()

# 8. CHAT INTERFACE
else:
    st.markdown("<div class='logo-container'><h1 class='logo-text'>Feemo AI</h1></div>", unsafe_allow_html=True)
    
    # PDF Tool
    with st.expander("📁 Add PDF Context"):
        uploaded = st.file_uploader("Upload", type="pdf", label_visibility="collapsed")
        # Logic for PDF parsing...

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Ask Feemo..."):
        # Logic for Groq API call...
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
