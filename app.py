import streamlit as st
import requests
import time
from supabase import create_client

# 1. INITIALIZE BACKEND
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"Config Error: {e}")
    st.stop()

# 2. APP CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide")

# 3. CSS BRANDING (Gemini Gradient)
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

# 4. THE SESSION RECOVERY (THE FIX)
def get_user():
    """Forces the app to acknowledge the login immediately."""
    try:
        # Check standard user session
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            return user_res.user
        
        # Check for 'code' in query params (OAuth return)
        if "code" in st.query_params:
            # Exchange code for session automatically
            supabase.auth.get_session()
            time.sleep(1) # Give Supabase time to sync
            st.rerun()
    except:
        pass
    return None

active_user = get_user()

# 5. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if active_user:
        u_name = active_user.user_metadata.get("full_name") or active_user.user_metadata.get("first_name", "Engineer")
        st.write(f"Logged in: **{u_name}**")
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.rerun()

# 6. AUTHENTICATION LOGIC
if not active_user:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.info("The AI engine is locked. Sign in with Google to continue.")
    
    try:
        # OAuth Setup - MUST match your Supabase config exactly
        auth_res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                "skip_browser_redirect": True 
            }
        })
        
        if auth_res and auth_res.url:
            # We use link_button as it's more reliable for redirects
            st.link_button("Continue with Google 🌐", auth_res.url, use_container_width=True)
                
    except Exception as e:
        st.error(f"Login setup failed: {e}")
    st.stop()

# 7. CHAT WORKSPACE (THE "OPENED" STATE)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.success(f"Access Granted. Hello, {active_user.user_metadata.get('full_name', 'User')}.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Chat Input
    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            # Call Groq AI using your secret key
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
            st.error("AI connection failed. Check your API key.")
            
