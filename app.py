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
except:
    st.error("Secrets missing.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. GEMINI-INSPIRED CSS
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    .stApp { background-color: #0e0e10; color: #e3e3e3; }
    
    /* Centered Content Container */
    .block-container { 
        max-width: 850px; 
        padding-top: 3rem !important; 
        margin: auto;
    }

    /* Multi-Color Gradient Logo */
    .logo-container { text-align: center; margin-bottom: 30px; padding: 20px; }
    .logo-text {
        font-size: 52px; font-weight: 700; letter-spacing: -1.5px;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
    }

    /* Chat Styling */
    [data-testid="stChatMessage"] { background-color: transparent !important; border: none !important; }
    [data-testid="stChatMessageContent"] { font-size: 16px; color: #e3e3e3; }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0e0e10; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #171717 !important; border-right: 1px solid #2d2d2d !important; }
    div[data-testid="stSidebar"] button { background-color: transparent !important; text-align: left !important; border: none !important; color: #aaa !important; }
    div[data-testid="stSidebar"] button:hover { background-color: #2d2d2d !important; color: white !important; }
    
    /* PDF Uploader Chip */
    .stFileUploader { margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 4. AUTHENTICATION & CALLBACK
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
    tab1, tab2 = st.tabs(["SIGN IN", "REGISTER"])
    with tab1:
        if st.session_state.login_error: st.error(st.session_state.login_error)
        with st.form("l_form"):
            st.text_input("Email", key="email_input")
            st.text_input("Password", type="password", key="pass_input")
            st.form_submit_button("Sign In", use_container_width=True, on_click=login_callback)
    st.stop()

# --- MAIN APP LOGIC ---

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

# 5. SIDEBAR (History & Logout)
with st.sidebar:
    st.markdown("<h3 style='color:#4285f4; margin-left:10px;'>History</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_id = None
        st.rerun()
    
    try:
        hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(8).execute()
        for c in hist.data:
            if st.button(f"💬 {c['chat_title'][:20]}...", key=f"c_{c['id']}", use_container_width=True):
                m_data = supabase.table("chat_history").select("full_history").eq("id", c['id']).execute()
                st.session_state.messages = m_data.data[0]['full_history']
                st.session_state.chat_id = c['id']
                st.rerun()
    except: pass

    st.sidebar.markdown("---")
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# 6. MAIN HEADER & TOOLS
st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ Feemo AI</h1></div>", unsafe_allow_html=True)

# Document Knowledge Base (Centered Tool)
with st.expander("📁 Add PDF Context (Knowledge Base)"):
    pdf_file = st.file_uploader("Upload study material", type="pdf", label_visibility="collapsed")
    pdf_text = ""
    if pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for i in range(min(len(reader.pages), 10)):
            pdf_text += reader.pages[i].extract_text() + "\n"
        st.success("Context Uploaded.")

# 7. CHAT DISPLAY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. INPUT & AI ENGINE
if prompt := st.chat_input("Ask Feemo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        sys_msg = f"You are Feemo AI. Assistant to {st.session_state.first_name}, an ML & AI Engineer."
        if pdf_text: sys_msg += f"\n\nPDF Knowledge: {pdf_text[:6000]}"

        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages
        }
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.openai.com/v1/chat/completions" if "OPENAI" in st.secrets else "https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Save History
        if st.session_state.chat_id is None:
            new_c = supabase.table("chat_history").insert({"chat_title": prompt[:25], "full_history": st.session_state.messages, "user_id": st.session_state.user_secret_id}).execute()
            st.session_state.chat_id = new_c.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.chat_id).execute()
    except:
        st.error("Engine connection error.")
