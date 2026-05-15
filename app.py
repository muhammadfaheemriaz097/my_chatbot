import streamlit as st
import requests
import time
import PyPDF2
from supabase import create_client

# 1. DATABASE INITIALIZATION
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("Secrets missing (SUPABASE_URL/KEY). Check Streamlit Cloud Settings.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. GEMINI-STYLE CSS
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    .stApp { background-color: #0e0e10; color: #e3e3e3; }
    
    /* Centered Content Container */
    .block-container { 
        max-width: 850px; 
        padding-top: 2rem !important; 
        margin: auto;
    }

    /* Multi-Color Gradient Logo */
    .logo-container { text-align: center; margin-bottom: 20px; padding: 10px; }
    .logo-text {
        font-size: 52px; font-weight: 700; letter-spacing: -1.5px;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    /* Form & Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stForm { border: 1px solid #2d2d2d !important; background-color: #171717; border-radius: 15px !important; }

    /* Sidebar Styling - Locked to Dark Theme */
    section[data-testid="stSidebar"] { 
        background-color: #111111 !important; 
        border-right: 1px solid #2d2d2d !important; 
        width: 260px !important;
    }
    
    /* Chat Bubble Tweaks */
    [data-testid="stChatMessage"] { background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. SESSION STATE INITIALIZATION
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "login_error" not in st.session_state: st.session_state.login_error = None
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

# --- 5. THE SIDEBAR (ALWAYS VISIBLE) ---
with st.sidebar:
    st.markdown("<h3 style='color:#4285f4; margin-bottom:20px;'>✦ Feemo AI</h3>", unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        st.markdown(f"**Workspace:** {st.session_state.first_name}")
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_id = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("<div style='font-size: 12px; color: #666;'>RECENT CHATS</div>", unsafe_allow_html=True)
        try:
            hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(8).execute()
            for c in hist.data:
                if st.button(f"💬 {c['chat_title'][:20]}...", key=f"side_{c['id']}", use_container_width=True):
                    m_data = supabase.table("chat_history").select("full_history").eq("id", c['id']).execute()
                    st.session_state.messages = m_data.data[0]['full_history']
                    st.session_state.chat_id = c['id']
                    st.rerun()
        except: pass
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    else:
        st.info("Please sign in to access your chat history and knowledge base.")

# --- 6. THE LOGIN CALLBACK ---
def login_callback():
    try:
        res = supabase.auth.sign_in_with_password({"email": st.session_state.email_input, "password": st.session_state.pass_input})
        if res.user:
            st.session_state.user_secret_id = res.user.id
            st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
            st.session_state.authenticated = True
            st.session_state.login_error = None
        else: st.session_state.login_error = "Invalid email or password."
    except: st.session_state.login_error = "Connection Error."

# --- 7. MAIN AREA: AUTHENTICATION (Condition 1) ---
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ Feemo AI</h1></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with tab1:
        if st.session_state.login_error: st.error(st.session_state.login_error)
        with st.form("l_form"):
            st.text_input("Email", placeholder="name@email.com", key="email_input")
            st.text_input("Password", type="password", key="pass_input")
            st.form_submit_button("SIGN IN", use_container_width=True, on_click=login_callback)
    
    with tab2:
        with st.form("reg_form"):
            n_name = st.text_input("Full Name", placeholder="Faheem Riaz")
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                    st.success("Verification link sent! Check your inbox.")
                except: st.error("Signup failed or account exists.")

    with tab3:
        with st.form("res_form"):
            r_email = st.text_input("Recovery Email")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(r_email)
                    st.success("Recovery email sent! Check your inbox.")
                except: st.error("Error sending reset link.")
    
    if st.session_state.authenticated: st.rerun()
    st.stop() # Only stops main area if not logged in

# --- 8. MAIN AREA: LOGGED-IN CHAT (Condition 2) ---
else:
    st.markdown("<div class='logo-container'><h1 class='logo-text'>✦ Feemo AI</h1></div>", unsafe_allow_html=True)
    
    # KNOWLEDGE BASE TOOL
    with st.expander("📁 PDF Knowledge Base"):
        pdf_file = st.file_uploader("Upload PDF material", type="pdf", label_visibility="collapsed")
        pdf_text = ""
        if pdf_file:
            try:
                reader = PyPDF2.PdfReader(pdf_file)
                for i in range(min(len(reader.pages), 15)):
                    extracted = reader.pages[i].extract_text()
                    if extracted: pdf_text += extracted + "\n"
                st.success("Document Analyzed. Feemo is ready.")
            except: st.error("PDF Parsing failed.")

    # CHAT HISTORY DISPLAY
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # CHAT INPUT
    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
            sys_msg = f"You are Feemo AI. Professional assistant to {st.session_state.first_name}, an ML & AI Engineer."
            if pdf_text: sys_msg += f"\n\nContext from Uploaded PDF:\n{pdf_text[:7000]}"

            payload = {
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages
            }
            
            with st.chat_message("assistant"):
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
                reply = res["choices"][0]["message"]["content"]
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # SAVE TO DB
            if st.session_state.chat_id is None:
                new_c = supabase.table("chat_history").insert({"chat_title": prompt[:25], "full_history": st.session_state.messages, "user_id": st.session_state.user_secret_id}).execute()
                st.session_state.chat_id = new_c.data[0]['id']
            else:
                supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.chat_id).execute()
        except: st.error("Engine Connection Error.")
