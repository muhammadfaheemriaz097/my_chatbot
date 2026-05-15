import streamlit as st
import requests
import time
import PyPDF2
import io
from supabase import create_client

# 1. DATABASE INITIALIZATION
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Secrets missing. Check Streamlit Cloud configuration.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. GEMINI-INSPIRED CUSTOM CSS
st.markdown("""
    <style>
    /* 1. Global Reset & Typography */
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    .stApp { background-color: #0e0e10; color: #e3e3e3; font-family: 'Inter', sans-serif; }
    
    /* 2. Centered Layout Container */
    .block-container { 
        max-width: 850px; 
        padding-top: 2rem !important; 
        margin: auto;
    }

    /* 3. GEMINI LOGO CUSTOMIZATION (Gradient & Glow) */
    .logo-container { 
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
    }
    .logo-text {
        font-size: 56px;
        font-weight: 700;
        letter-spacing: -2px;
        /* Custom Gemini-style Gradient */
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 0px 10px rgba(155, 114, 203, 0.2));
    }
    .logo-symbol { font-size: 35px; color: #4285f4; margin-right: 10px; }

    /* 4. Chat Bubbles */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        margin-bottom: 15px !important;
    }
    [data-testid="stChatMessageContent"] { font-size: 16px; line-height: 1.6; color: #e3e3e3; }

    /* 5. Floating Tool Chip (Knowledge Base) */
    .stExpander {
        border: 1px solid #2d2d2d !important;
        background-color: #171717 !important;
        border-radius: 12px !important;
        margin-bottom: 20px !important;
    }

    /* 6. Sidebar Styling */
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* 7. Input Bar Padding */
    .stChatInputContainer { padding-bottom: 30px !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. SESSION STATE
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []
if "login_error" not in st.session_state: st.session_state.login_error = None
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None

# --- 5. THE LOGIN CALLBACK ---
def login_callback():
    try:
        res = supabase.auth.sign_in_with_password({"email": st.session_state.email_input, "password": st.session_state.pass_input})
        if res.user:
            st.session_state.user_secret_id = res.user.id
            st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
            st.session_state.authenticated = True
            st.session_state.login_error = None
        else: st.session_state.login_error = "Invalid credentials."
    except: st.session_state.login_error = "Connection error."

# --- 6. AUTHENTICATION GATE ---
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ Feemo AI</h1></div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["SIGN IN", "REGISTER", "FORGOT PASSWORD"])
    
    with tab1:
        if st.session_state.login_error: st.error(st.session_state.login_error)
        with st.form("l_form"):
            st.text_input("Email", key="email_input")
            st.text_input("Password", type="password", key="pass_input")
            st.form_submit_button("LOGIN", use_container_width=True, on_click=login_callback)
    
    with tab2:
        with st.form("r_form"):
            n_name = st.text_input("Full Name", placeholder="Faheem Riaz")
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password", type="password")
            if st.form_submit_button("CREATE ACCOUNT", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                    st.success("Verification link sent! Check your email.")
                except: st.error("Registration failed.")
    
    with tab3:
        with st.form("reset_form"):
            r_email = st.text_input("Recovery Email")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(r_email)
                    st.success("Check your email for the link!")
                except: st.error("Error sending link.")
    st.stop()

# --- 7. PROTECTED CONTENT (SIDEBAR) ---
with st.sidebar:
    st.markdown("<h3 style='color:#4285f4;'>History</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.markdown("---")
    try:
        hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(8).execute()
        for c in hist.data:
            if st.button(f"💬 {c['chat_title'][:20]}...", key=f"h_{c['id']}", use_container_width=True):
                m_data = supabase.table("chat_history").select("full_history").eq("id", c['id']).execute()
                st.session_state.messages = m_data.data[0]['full_history']
                st.session_state.current_chat_id = c['id']
                st.rerun()
    except: pass
    
    st.sidebar.markdown("---")
    if st.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 8. MAIN VIEW (CENTERED CONTENT) ---
st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ Feemo AI</h1></div>", unsafe_allow_html=True)

# GEMINI-STYLE FLOATING TOOLS
with st.expander("📁 Upload PDF Knowledge Base"):
    pdf_file = st.file_uploader("Feemo will read this document", type="pdf", label_visibility="collapsed")
    pdf_text = ""
    if pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for i in range(min(len(reader.pages), 10)):
            pdf_text += reader.pages[i].extract_text() + "\n"
        st.success("Document analyzed.")

# CHAT LOG
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# INPUT ENGINE
if prompt := st.chat_input("Ask Feemo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    try:
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        sys_msg = f"You are Feemo AI. Professional helper to {st.session_state.first_name}, an ML & AI Engineer."
        if pdf_text: sys_msg += f"\n\nContext from PDF: {pdf_text[:6000]}"

        payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages}
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # PERSISTENCE
        if st.session_state.current_chat_id is None:
            new_c = supabase.table("chat_history").insert({"chat_title": prompt[:25], "full_history": st.session_state.messages, "user_id": st.session_state.user_secret_id}).execute()
            st.session_state.current_chat_id = new_c.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.current_chat_id).execute()
    except: st.error("Engine Connection Error.")
