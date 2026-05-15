import streamlit as st
import requests
import time
from supabase import create_client

# 1. INITIALIZE DATABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. ADVANCED CSS
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    button[kind="headerNoPadding"]::after { content: '☰'; font-size: 26px; color: #c9a84c; visibility: visible !important; display: block; }
    button[kind="headerNoPadding"] { background-color: transparent !important; margin-left: 15px !important; }
    .logo-container { display: flex; justify-content: center; align-items: center; padding: 40px 0; }
    .logo-text { font-size: 60px; font-weight: 900; background: linear-gradient(135deg, #c9a84c 0%, #ffffff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0px 5px 15px rgba(201, 168, 76, 0.3)); }
    .logo-symbol { color: #c9a84c; font-size: 35px; margin-right: 12px; }
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

# 5. AUTHENTICATION BLOCK
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    msg_slot = st.empty() # Placeholder for messages
    
    tab1, tab2, tab3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@email.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("LOGIN TO WORKSPACE", use_container_width=True)
        
        if submit:
            try:
                # Direct Authentication
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                
                if res.user:
                    # SUCCESS: Update state and force rerun BEFORE any other code executes
                    st.session_state.user_secret_id = res.user.id
                    st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
                    st.session_state.authenticated = True
                    msg_slot.success("Access Granted. Synchronizing...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    msg_slot.error("Invalid email or password.")
            except Exception:
                # FAILURE: Only happens if user is NOT found
                msg_slot.error("Invalid email or password.")
    
    with tab2:
        with st.form("signup_form"):
            n_name = st.text_input("Full Name")
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password", type="password")
            c_pass = st.text_input("Confirm", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                if n_pass == c_pass and len(n_pass) >= 6:
                    try:
                        supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                        msg_slot.success("Check your email to verify!")
                    except:
                        msg_slot.error("Registration failed.")
                else:
                    msg_slot.warning("Check password matching or length.")
    st.stop()

# --- EVERYTHING BELOW ONLY RUNS IF AUTHENTICATED IS TRUE ---

# 6. POST-LOGIN UI
if not st.session_state.welcome_shown:
    st.toast(f"🚀 Welcome back, {st.session_state.first_name}!", icon="✨")
    st.session_state.welcome_shown = True

# 7. DATA SYNC
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None

try:
    hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(10).execute()
    recent = hist.data if hist.data else []
except:
    recent = []

# 8. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.caption(f"👤 {st.session_state.first_name}")
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_id = None
        st.rerun()
    
    for c in recent:
        if st.sidebar.button(f"💬 {c['chat_title'][:25]}...", key=f"c_{c['id']}", use_container_width=True):
            m = supabase.table("chat_history").select("full_history").eq("id", c['id']).execute()
            if m.data:
                st.session_state.messages = m.data[0]['full_history']
                st.session_state.chat_id = c['id']
                st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.welcome_shown = False
        st.rerun()

# 9. MAIN LOGO (Fixed Header)
st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

# 10. CHAT ENGINE
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": f"You are Feemo AI. Helper to {st.session_state.first_name}"}] + st.session_state.messages}
        with st.chat_message("assistant"):
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = r["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Save History
        if st.session_state.chat_id is None:
            new = supabase.table("chat_history").insert({"chat_title": prompt[:30], "full_history": st.session_state.messages, "user_id": st.session_state.user_secret_id}).execute()
            st.session_state.chat_id = new.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.chat_id).execute()
    except:
        st.error("AI service error.")
