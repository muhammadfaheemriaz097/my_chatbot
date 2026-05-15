import streamlit as st
import requests
import time
import PyPDF2
from supabase import create_client

# 1. INITIALIZE BACKEND
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("Missing Secrets: Ensure SUPABASE_URL and SUPABASE_KEY are in Streamlit Cloud.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="✦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 3. GEMINI BRANDING (CSS)
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .block-container { max-width: 850px; padding-top: 2rem !important; margin: auto; }
    
    /* LOGO SECTION */
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

# 4. SERVER-SIDE AUTH CHECK (THE FIX)
def get_current_user():
    """Directly queries Supabase for an active session/user."""
    try:
        user_response = supabase.auth.get_user()
        if user_response and user_response.user:
            return user_response.user
    except:
        return None

# Immediately verify identity
active_user = get_current_user()

# 5. SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if active_user:
        # Extract name from Google or Email metadata
        user_name = active_user.user_metadata.get("full_name") or active_user.user_metadata.get("first_name", "Engineer")
        st.write(f"👤 **{user_name}**")
        st.markdown("---")
        
        # Logout logic
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.rerun()
    else:
        st.info("Log in to unlock features.")

# 6. LOGIC GATE: LOGIN VS WORKSPACE
if not active_user:
    # --- LOGIN INTERFACE ---
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with t1:
        # Email/Password Form
        with st.form("auth_login"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("SIGN IN", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    if res.user: st.rerun()
                except: st.error("Authentication failed.")
        
        st.markdown("<p style='text-align: center; color: #888; margin: 15px 0;'>OR</p>", unsafe_allow_html=True)
        
        # FAILSAFE GOOGLE LINK (Avoids browser redirect blocks)
        try:
            google_link = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                    "skip_browser_redirect": True 
                }
            })
            if google_link and google_link.url:
                st.link_button("Continue with Google 🌐", google_link.url, use_container_width=True)
        except Exception as e:
            st.error(f"Google setup incomplete: {e}")

    with t2:
        with st.form("auth_reg"):
            reg_name = st.text_input("Full Name")
            reg_email = st.text_input("Email")
            reg_pass = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": reg_email, "password": reg_pass, "options": {"data": {"first_name": reg_name}}})
                    st.success("Verification email sent!")
                except: st.error("Error during registration.")

    with t3:
        st.markdown("### Password Recovery")
        with st.form("auth_reset"):
            reset_email = st.text_input("Enter Email")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("Check your inbox for a reset link.")
                except: st.error("Could not process reset.")
    st.stop()

# 7. LOGGED-IN CHAT WORKSPACE
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    # Session State for Messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Knowledge Base Expander
    with st.expander("📁 PDF Context"):
        pdf = st.file_uploader("Upload technical docs", type="pdf", label_visibility="collapsed")
        pdf_content = ""
        if pdf:
            reader = PyPDF2.PdfReader(pdf)
            for i in range(min(len(reader.pages), 10)):
                chunk = reader.pages[i].extract_text()
                if chunk: pdf_content += chunk + "\n"
            st.success("Context loaded successfully.")

    # Render Chat
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Chat Interaction
    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
            name = active_user.user_metadata.get('full_name', 'Engineer')
            sys_prompt = f"You are Feemo AI, assisting {name}, an ML & AI Engineer."
            if pdf_content: sys_prompt += f"\n\nPDF Context:\n{pdf_content[:7000]}"

            payload = {
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role": "system", "content": sys_prompt}] + st.session_state.messages
            }
            
            with st.chat_message("assistant"):
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
                answer = resp["choices"][0]["message"]["content"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
        except:
            st.error("AI node is currently offline. Check API keys.")
