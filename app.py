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
    st.error("Missing Secrets: Check SUPABASE_URL and SUPABASE_KEY in Streamlit.")
    st.stop()

# 2. APP CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. GEMINI BRANDING (CSS)
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
    .logo-symbol { font-size: 45px; margin-right: 15px; color: #4285f4; text-shadow: 0px 0px 15px rgba(66, 133, 244, 0.6); }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. ROBUST AUTH CHECK
def get_authenticated_user():
    """Forces a refresh to catch the session after the redirect."""
    try:
        # Check standard user
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            return user_res.user
        
        # Check for session in URL hash/storage
        session_res = supabase.auth.get_session()
        if session_res and session_res.session:
            return session_res.session.user
    except:
        pass
    return None

# Check identity
active_user = get_authenticated_user()

# 5. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if active_user:
        name = active_user.user_metadata.get("full_name") or active_user.user_metadata.get("first_name", "Engineer")
        st.write(f"👤 **{name}**")
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.rerun()

# 6. LOGIC GATE
if not active_user:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.warning("Authentication Required to open Chat.")
    
    try:
        # NOTICE: Added the slash '/' at the end to match your screenshot
        auth_info = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                "skip_browser_redirect": True 
            }
        })
        
        if auth_info and auth_info.url:
            st.link_button("🚀 Continue with Google", auth_info.url, use_container_width=True)
            st.caption("URL configured to match Supabase Site URL.")
            
    except Exception as e:
        st.error(f"Config Error: {e}")
    st.stop()

# 7. WORKSPACE (THE OPEN CHAT)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.success(f"Welcome, {active_user.user_metadata.get('full_name', 'Engineer')}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Simple UI Loop
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

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
            st.error("AI Error.")
