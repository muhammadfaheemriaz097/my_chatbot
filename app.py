import streamlit as st
import requests
import time
from supabase import create_client

# 1. INITIALIZE BACKEND
try:
    # Fetches your credentials from Streamlit Secrets [cite: 3, 5]
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

# 3. GEMINI-STYLE UI BRANDING [cite: 4, 30]
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
    .stButton > button { border-radius: 10px; border: 1px solid #2d2d2d; background-color: #171717; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 4. FORCED SESSION SYNC (THE ABSOLUTE FIX FOR YOUR VIDEO ISSUE)
def get_user():
    """Intercepts the OAuth code from Google and forces a login session."""
    try:
        # Check for the '?code=' parameter in the URL from your video [cite: 52]
        params = st.query_params
        if "code" in params:
            # Exchange the code for a session token immediately
            supabase.auth.get_session()
            # Clear the URL to prevent refresh loops
            st.query_params.clear()
            st.rerun()

        # Final check for an active user
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            return user_res.user
    except:
        pass
    return None

# Verify identity before rendering anything
active_user = get_user()

# 5. SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if active_user:
        u_name = active_user.user_metadata.get("full_name") or active_user.user_metadata.get("first_name", "Engineer")
        st.write(f"Logged in: **{u_name}**")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.rerun()
    else:
        st.info("Log in to activate workspace.")

# 6. AUTHENTICATION GATEWAY
if not active_user:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.warning("Workspace Locked: Identity verification required.")
    
    try:
        # OAuth Redirect Configuration
        auth_res = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                # Matches your Supabase 'Site URL' setting exactly [cite: 55]
                "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                "skip_browser_redirect": True 
            }
        })
        
        if auth_res and auth_res.url:
            st.link_button("Continue with Google 🌐", auth_res.url, use_container_width=True)
            st.caption("Clicking opens secure Google sign-in.")
            
    except Exception as e:
        st.error(f"OAuth configuration error: {e}")
    st.stop()

# 7. LOGGED-IN CHAT WORKSPACE
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    st.success(f"Connection Secure. Welcome back, {active_user.user_metadata.get('full_name', 'User')}.")

    # Initialize chat state [cite: 5]
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Chat Interaction
    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            # AI Inference via Groq [cite: 4, 30]
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
            st.error("AI node offline. Verify GROQ_API_KEY in Secrets.")
