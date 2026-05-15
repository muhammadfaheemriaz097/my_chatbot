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
    st.error("Secrets missing. Please check your Streamlit Cloud Secrets.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="✦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 3. SESSION & OAUTH RECOVERY LOGIC
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

def check_active_session():
    """Detects and captures the session after Google/Social redirect."""
    try:
        res = supabase.auth.get_session()
        if res and res.session and not st.session_state.authenticated:
            user = res.session.user
            st.session_state.user_secret_id = user.id
            # Google typically provides 'full_name' in metadata
            st.session_state.first_name = user.user_metadata.get("full_name") or user.user_metadata.get("first_name", "User")
            st.session_state.authenticated = True
            st.rerun()
    except Exception:
        pass

# Always run the session check at the start
check_active_session()

# 4. GEMINI-STYLE CSS
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .block-container { max-width: 850px; padding-top: 2rem !important; margin: auto; }

    /* LOGO BRANDING */
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }
    .logo-text {
        font-size: 55px; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .logo-symbol { font-size: 45px; margin-right: 15px; color: #4285f4; text-shadow: 0px 0px 15px rgba(66, 133, 244, 0.6); }

    /* UI COMPONENTS */
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stForm { border: 1px solid #2d2d2d !important; background-color: #171717; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if st.session_state.authenticated:
        st.write(f"👤 {st.session_state.first_name}")
        st.markdown("---")
        
        # Logout Logic
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    else:
        st.info("Log in to unlock your workspace.")

# 6. AUTHENTICATION PAGES
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with t1:
        # Standard Email/Pass Login
        with st.form("l_form"):
            e_in = st.text_input("Email")
            p_in = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e_in, "password": p_in})
                    if res.user:
                        st.session_state.authenticated = True
                        st.rerun()
                except: st.error("Invalid email or password.")
        
        st.markdown("<p style='text-align: center; color: #888; margin: 10px 0;'>OR</p>", unsafe_allow_html=True)
        
        # THE GOOGLE FAILSAFE BUTTON
        try:
            # Generate the Google OAuth URL
            google_auth = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                    "skip_browser_redirect": True 
                }
            })
            if google_auth and google_auth.url:
                st.link_button("Continue with Google 🌐", google_auth.url, use_container_width=True)
        except Exception as e:
            st.error(f"Google setup error: {e}")
            
    with t2:
        with st.form("reg_form"):
            n_name = st.text_input("Full Name")
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                    st.success("Verification link sent! Check your email.")
                except: st.error("Signup failed.")

    with t3:
        st.markdown("### Reset Password")
        with st.form("reset_form"):
            r_email = st.text_input("Enter Email")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(r_email)
                    st.success("Link sent! Check your inbox.")
                except: st.error("Reset failed.")
    st.stop()

# 7. LOGGED-IN CHAT WORKSPACE
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    with st.expander("📁 PDF Knowledge Base"):
        pdf_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
        pdf_text = ""
        if pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for i in range(min(len(reader.pages), 10)):
                page_text = reader.pages[i].extract_text()
                if page_text: pdf_text += page_text + "\n"
            st.success("PDF Knowledge Integrated.")

    # Render History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
            sys_msg = f"You are Feemo AI, a helpful assistant to {st.session_state.first_name}, an ML & AI Engineer."
            if pdf_text: sys_msg += f"\n\nContext from PDF:\n{pdf_text[:7000]}"

            payload = {
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages
            }
            
            with st.chat_message("assistant"):
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
                reply = res["choices"][0]["message"]["content"]
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        except: 
            st.error("AI connection lost. Please check your API key.")
