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
    st.error("Missing Secrets: Check SUPABASE_URL and SUPABASE_KEY.")
    st.stop()

# 2. APP CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. CSS BRANDING (Gemini Aesthetic)
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }
    .logo-text {
        font-size: 55px; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .logo-symbol { font-size: 45px; margin-right: 15px; color: #4285f4; text-shadow: 0px 0px 15px rgba(66, 133, 244, 0.6); }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. FORCED AUTHENTICATION ENGINE
def force_session_sync():
    """Forces the app to acknowledge the login session after a redirect."""
    try:
        # Check standard user status
        res = supabase.auth.get_user()
        if res and res.user:
            return res.user
        
        # Backup: Check raw session
        sess = supabase.auth.get_session()
        if sess and sess.session:
            return sess.session.user
    except:
        pass
    return None

# Check for user immediately on load
active_user = force_session_sync()

# 5. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if active_user:
        u_name = active_user.user_metadata.get("full_name") or active_user.user_metadata.get("first_name", "User")
        st.write(f"Logged in: **{u_name}**")
        if st.button("Sign Out", use_container_width=True):
            supabase.auth.sign_out()
            st.rerun()

# 6. MAIN APPLICATION FLOW
if not active_user:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    st.info("The workspace is locked. Please sign in to activate the AI engine.")
    
    try:
        # Generate OAuth URL with the EXACT slash from your screenshot
        auth_data = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                "skip_browser_redirect": True 
            }
        })
        
        if auth_data and auth_data.url:
            st.link_button("Continue with Google 🌐", auth_data.url, use_container_width=True)
            
            # If the user is returning from a redirect but 'active_user' is still None
            # we show a "Connecting" spinner and force a rerun to catch the cookie.
            if "#access_token" in str(st.context.headers):
                with st.spinner("Synchronizing Identity..."):
                    time.sleep(2)
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Handshake configuration error: {e}")
    st.stop()

# 7. CHAT WORKSPACE (THE "SOLVED" STATE)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.success(f"Connection established for {active_user.email}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # UI for history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Input logic
    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
            payload = {
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role": "system", "content": "You are Feemo AI."}] + st.session_state.messages
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = resp["choices"][0]["message"]["content"]
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
        except:
            st.error("The AI engine is currently unreachable.")
