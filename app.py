import streamlit as st
import requests
import time
import datetime
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
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. UI STYLING (CSS)
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    /* Hamburger Menu Style */
    button[kind="headerNoPadding"]::after { 
        content: '☰'; font-size: 26px; color: #c9a84c; visibility: visible !important; display: block;
    }
    button[kind="headerNoPadding"] {
        background-color: transparent !important; margin-left: 15px !important;
    }

    /* Branded Logo */
    .logo-container { display: flex; justify-content: center; align-items: center; padding: 40px 0; margin-top: -10px; }
    .logo-text {
        font-size: 60px; font-weight: 900; letter-spacing: -2px;
        background: linear-gradient(135deg, #c9a84c 0%, #ffffff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 5px 15px rgba(201, 168, 76, 0.3));
    }
    .logo-symbol { color: #c9a84c; font-size: 35px; margin-right: 12px; }

    /* Theme Layout */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #2d2d2d !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .block-container { max-width: 850px; padding-top: 1rem !important; }
    .stForm { border: 1px solid #2d2d2d !important; padding: 25px !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. SESSION STATE INITIALIZATION
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# 5. AUTHENTICATION GATE
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    # Message Slot for Login Feedback
    auth_msg = st.empty()
    
    tab1, tab2, tab3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@email.com")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN TO WORKSPACE", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.user_secret_id = res.user.id
                        st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
                        st.session_state.authenticated = True
                        auth_msg.success("Verified! Entering Workspace...")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        auth_msg.error("Invalid credentials.")
                except:
                    auth_msg.error("Invalid email or password.")
    
    with tab2:
        with st.form("signup_form"):
            n_name = st.text_input("Full Name", placeholder="Faheem Riaz")
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password", type="password")
            c_pass = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                if n_pass == c_pass and len(n_pass) >= 6:
                    try:
                        supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                        auth_msg.success("Registration Sent! Check your email to verify.")
                    except:
                        auth_msg.error("Account already exists or error occurred.")
                else:
                    st.warning("Password error (Min 6 chars / Match).")
    st.stop()

# --- APP START (Only reached if authenticated is True) ---

# 6. POST-LOGIN UI
if not st.session_state.welcome_shown:
    st.toast(f"🚀 Welcome back, {st.session_state.first_name}!", icon="✨")
    st.session_state.welcome_shown = True

# 7. SIDEBAR & KNOWLEDGE BASE
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.caption(f"👤 {st.session_state.first_name}")
    
    st.markdown("---")
    st.markdown("<div style='color:#c9a84c; font-size:12px; font-weight:bold; margin-bottom:10px;'>KNOWLEDGE BASE</div>", unsafe_allow_html=True)
    
    pdf_file = st.file_uploader("Upload PDF", type="pdf")
    pdf_text = ""
    if pdf_file:
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            for i in range(min(len(reader.pages), 10)): # Limit context
                pdf_text += reader.pages[i].extract_text() + "\n"
            st.success("Knowledge Synced!")
        except:
            st.error("PDF Parsing failed.")

    st.markdown("---")
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    # Load History
    try:
        hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(5).execute()
        for chat in hist.data:
            if st.sidebar.button(f"💬 {chat['chat_title'][:20]}...", key=f"h_{chat['id']}", use_container_width=True):
                m_data = supabase.table("chat_history").select("full_history").eq("id", chat['id']).execute()
                st.session_state.messages = m_data.data[0]['full_history']
                st.session_state.current_chat_id = chat['id']
                st.rerun()
    except: pass

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.welcome_shown = False
        st.rerun()

# 8. MAIN VIEW
st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 9. AI ENGINE
if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Build System Knowledge
        sys_msg = f"You are Feemo AI. Professional helper to {st.session_state.first_name}, an ML & AI Engineer."
        if pdf_text:
            sys_msg += f"\n\nContext from PDF:\n{pdf_text[:7000]}"
            sys_msg += "\n\nAnswer questions using this context first."

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
        
        # Persistence
        if st.session_state.current_chat_id is None:
            new_c = supabase.table("chat_history").insert({"chat_title": prompt[:30], "full_history": st.session_state.messages, "user_id": st.session_state.user_secret_id}).execute()
            st.session_state.current_chat_id = new_c.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.current_chat_id).execute()
    except:
        st.error("Sync Error with AI Engine.")
