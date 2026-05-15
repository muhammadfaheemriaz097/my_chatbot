import streamlit as st
import requests
import time
import PyPDF2
import io
from supabase import create_client

# 1. DATABASE INITIALIZATION
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. GEMINI-INSPIRED CSS
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    /* Global Background */
    .stApp { background-color: #0e0e10; color: #e3e3e3; font-family: 'Inter', sans-serif; }
    
    /* Centered Chat Container */
    .block-container { 
        max-width: 800px; 
        padding-top: 5rem !important; 
        margin: auto;
    }

    /* Professional Logo (Centered like Gemini) */
    .logo-container { 
        text-align: center;
        margin-bottom: 40px;
    }
    .logo-text {
        font-size: 48px; font-weight: 600; letter-spacing: -1px;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        margin-bottom: 20px !important;
    }
    [data-testid="stChatMessageContent"] { font-size: 16px; line-height: 1.6; }

    /* The Bottom Input Area (Gemini Style) */
    .stChatInputContainer {
        padding-bottom: 20px !important;
        background-color: transparent !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #171717 !important; border-right: 1px solid #2d2d2d !important; }
    
    /* PDF Uploader Area (Main Area) */
    .pdf-tool {
        background-color: #1e1f20;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 10px 15px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. AUTHENTICATION (Callback Logic)
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "login_error" not in st.session_state: st.session_state.login_error = None

def login_callback():
    try:
        res = supabase.auth.sign_in_with_password({"email": st.session_state.email_input, "password": st.session_state.pass_input})
        if res.user:
            st.session_state.user_secret_id = res.user.id
            st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
            st.session_state.authenticated = True
        else: st.session_state.login_error = "Invalid credentials."
    except: st.session_state.login_error = "Login Error."

if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ Feemo AI</h1></div>", unsafe_allow_html=True)
    with st.container():
        tab1, tab2 = st.tabs(["SIGN IN", "REGISTER"])
        with tab1:
            if st.session_state.login_error: st.error(st.session_state.login_error)
            with st.form("l_form"):
                st.text_input("Email", key="email_input")
                st.text_input("Password", type="password", key="pass_input")
                st.form_submit_button("Sign In", use_container_width=True, on_click=login_callback)
        if st.session_state.authenticated: st.rerun()
    st.stop()

# --- MAIN APP ---

# 5. SIDEBAR (History Only)
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>History</h2>", unsafe_allow_html=True)
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    # (History loading code goes here)
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# 6. HEADER
st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ Feemo AI</h1></div>", unsafe_allow_html=True)

# 7. TOOL AREA (Gemini Style Chips)
col1, col2 = st.columns([1, 4])
with col1:
    pdf_file = st.file_uploader("📁 Add Knowledge", type="pdf", label_visibility="collapsed")
pdf_text = ""
if pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    for i in range(min(len(reader.pages), 10)):
        pdf_text += reader.pages[i].extract_text() + "\n"
    st.caption("✅ Document synced to brain")

# 8. MESSAGES
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 9. FLOATING INPUT bar
if prompt := st.chat_input("Ask Feemo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI Request
    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
    sys_msg = f"You are Feemo AI. Professional helper to {st.session_state.first_name}."
    if pdf_text: sys_msg += f"\n\nContext: {pdf_text[:5000]}"
    
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages}
    
    with st.chat_message("assistant"):
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
        reply = res["choices"][0]["message"]["content"]
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
