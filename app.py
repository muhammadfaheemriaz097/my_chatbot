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
    st.error("Environment Error: Check Streamlit Secrets for SUPABASE_URL and SUPABASE_KEY.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. UI STYLING (Gemini Customization)
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    /* Global Theme */
    .stApp { background-color: #0e0e10; color: #ececf1; }
    
    /* Centered Layout (Gemini Style) */
    .block-container { max-width: 850px; padding-top: 1.5rem !important; margin: auto; }

    /* MULTI-COLOR GRADIENT LOGO */
    .logo-container { 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        padding: 20px 0; 
        margin-top: -10px; 
    }
    .logo-text {
        font-size: 60px; 
        font-weight: 900; 
        letter-spacing: -2px;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 5px 15px rgba(66, 133, 244, 0.2));
    }
    .logo-symbol { color: #4285f4; font-size: 35px; margin-right: 12px; }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #2d2d2d !important; }
    
    /* Chat Bubble Adjustments */
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1b !important; border-radius: 10px; }
    .stForm { border: 1px solid #2d2d2d !important; padding: 25px !important; border-radius: 15px !important; background-color: #111111; }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { color: #888; }
    </style>
    """, unsafe_allow_html=True)

# 4. SESSION STATE INITIALIZATION
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False
if "login_error" not in st.session_state:
    st.session_state.login_error = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --- 5. THE LOGIN CALLBACK ---
def login_callback():
    try:
        email = st.session_state.email_input
        password = st.session_state.pass_input
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.user_secret_id = res.user.id
            st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
            st.session_state.authenticated = True
            st.session_state.login_error = None
        else:
            st.session_state.login_error = "Invalid credentials."
    except Exception:
        st.session_state.login_error = "Invalid email or password."

# 6. AUTHENTICATION GATE
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with tab1:
        if st.session_state.login_error:
            st.error(st.session_state.login_error)
        with st.form("login_form"):
            st.text_input("Email Address", placeholder="name@email.com", key="email_input")
            st.text_input("Password", type="password", key="pass_input")
            st.form_submit_button("LOGIN TO WORKSPACE", use_container_width=True, on_click=login_callback)
        if st.session_state.authenticated:
            st.success("Access Granted! Loading...")
            time.sleep(0.5)
            st.rerun()
    
    with tab2:
        with st.form("signup_form"):
            n_name = st.text_input("Full Name", placeholder="Faheem Riaz")
            n_email = st.text_input("Email", placeholder="name@email.com")
            n_pass = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                    st.success("Check your email to verify!")
                except:
                    st.error("Registration failed.")

    with tab3:
        st.markdown("<div style='margin-bottom: 10px;'>Enter email for a recovery link.</div>", unsafe_allow_html=True)
        with st.form("reset_form"):
            reset_email = st.text_input("Email Address", placeholder="name@email.com")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("Recovery email sent!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    st.stop()

# --- 7. PROTECTED APPLICATION ---

if not st.session_state.welcome_shown:
    st.toast(f"🚀 Welcome back, {st.session_state.first_name}!", icon="✨")
    st.session_state.welcome_shown = True

# SIDEBAR (Preserved)
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.caption(f"👤 {st.session_state.first_name}")
    st.markdown("---")
    st.markdown("<div style='color:#4285f4; font-size:12px; font-weight:bold; margin-bottom:10px;'>KNOWLEDGE BASE</div>", unsafe_allow_html=True)
    
    pdf_file = st.file_uploader("Upload PDF", type="pdf")
    pdf_text = ""
    if pdf_file:
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            for i in range(min(len(reader.pages), 10)):
                extracted = reader.pages[i].extract_text()
                if extracted: pdf_text += extracted + "\n"
            st.success("Knowledge Synced!")
        except:
            st.error("PDF Parsing failed.")

    st.markdown("---")
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    # History Logic
    try:
        hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(5).execute()
        for chat in hist.data:
            if st.sidebar.button(f"💬 {chat['chat_title'][:20]}...", key=f"h_{chat['id']}", use_container_width=True):
                msg_data = supabase.table("chat_history").select("full_history").eq("id", chat['id']).execute()
                st.session_state.messages = msg_data.data[0]['full_history']
                st.session_state.current_chat_id = chat['id']
                st.rerun()
    except: pass

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# MAIN VIEW (Gemini Logo Customization Applied)
st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# AI ENGINE
if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        sys_msg = f"You are Feemo AI. Professional helper to {st.session_state.first_name}, an ML & AI Engineer."
        if pdf_text:
            sys_msg += f"\n\nContext from PDF:\n{pdf_text[:7000]}"
            sys_msg += "\n\nAnswer using the PDF context first."

        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages
        }
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        if st.session_state.current_chat_id is None:
            new_c = supabase.table("chat_history").insert({"chat_title": prompt[:30], "full_history": st.session_state.messages, "user_id": st.session_state.user_secret_id}).execute()
            st.session_state.current_chat_id = new_c.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.current_chat_id).execute()
    except:
        st.error("AI Engine Error.")
