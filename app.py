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
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="✦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 3. SESSION STATE DEFAULTS
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []
if "first_name" not in st.session_state: st.session_state.first_name = "Engineer"

# 4. THE INTERCEPTOR (THE FIX) 
def sync_identity():
    """Forces the app to exchange the Google code for a session immediately."""
    try:
        # Check for the '?code=' parameter from the OAuth redirect 
        params = st.query_params
        if "code" in params:
            # Exchange code for a real session token 
            supabase.auth.get_session()
            # Clear the URL to prevent loops 
            st.query_params.clear()
            st.session_state.authenticated = True
            st.rerun()

        # Standard recovery for page refreshes using server-side check 
        res = supabase.auth.get_user()
        if res and res.user:
            if not st.session_state.authenticated:
                st.session_state.authenticated = True
                meta = res.user.user_metadata or {}
                st.session_state.first_name = meta.get("full_name") or res.user.email.split("@")[0]
                return True
    except Exception:
        pass
    return False

# Run the identity check immediately 
if not st.session_state.authenticated:
    sync_identity()

# 5. GEMINI-STYLE UI BRANDING
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .block-container { max-width: 850px; padding-top: 2rem !important; margin: auto; }
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }
    .logo-text {
        font-size: 55px; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .logo-symbol { font-size: 45px; margin-right: 15px; color: #4285f4; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    </style>
    """, unsafe_allow_html=True)

# 6. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if st.session_state.authenticated:
        st.write(f"👤 **{st.session_state.first_name}**")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    else:
        st.info("Log in to activate workspace.")

# 7. LOGIC GATE: LOGIN VS CHAT
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    try:
        # NOTICE: Redirect includes trailing slash to match your Supabase config 
        auth_res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                "skip_browser_redirect": True 
            }
        })
        
        if auth_res and auth_res.url:
            st.link_button("Continue with Google 🌐", auth_res.url, use_container_width=True)
                
    except Exception as e:
        st.error(f"Login setup failed: {e}")
    st.stop()

# 8. WORKSPACE (LOGGED-IN STATE)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.success(f"Access Granted. Hello, {st.session_state.first_name}.")

    with st.expander("📁 PDF Knowledge Base"):
        pdf_file = st.file_uploader("Upload technical docs", type="pdf", label_visibility="collapsed")
        pdf_text = ""
        if pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for i in range(min(len(reader.pages), 10)):
                chunk = reader.pages[i].extract_text()
                if chunk: pdf_text += chunk + "\n"
            st.success("Context Integrated.")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            sys_msg = f"You are Feemo AI, a helpful assistant to {st.session_state.first_name}."
            if pdf_text: sys_msg += f"\n\nContext from PDF:\n{pdf_text[:7000]}"

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
            st.error("AI node is offline. Check API key.")
