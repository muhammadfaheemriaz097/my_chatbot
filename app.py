import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE DATABASE
# Ensure these secrets are set in your Streamlit Cloud/local secrets.toml
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. ADVANCED CSS (Professional Dark Theme & UI Refinements)
st.markdown("""
    <style>
    /* Hide Default Streamlit Elements */
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    /* Custom Hamburger Menu Icon */
    button[kind="headerNoPadding"]::after { 
        content: '☰'; font-size: 26px; color: #c9a84c; visibility: visible !important; display: block;
    }
    button[kind="headerNoPadding"] {
        background-color: transparent !important; border-radius: 8px !important;
        margin-left: 15px !important; width: 45px !important; height: 45px !important;
    }

    /* Core Theme Colors */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* Sidebar Styling */
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 25px 0 10px 10px; }
    div[data-testid="stSidebar"] button {
        background-color: transparent !important; color: #d1d1d1 !important;
        text-align: left !important; display: block !important; width: 100% !important; padding: 10px 15px !important;
    }
    div[data-testid="stSidebar"] button:hover { background-color: #1a1a1a !important; color: #ffffff !important; }

    /* Chat Elements */
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .block-container { max-width: 850px; padding-top: 1rem !important; }
    
    /* Form Styling */
    .stForm { border: 1px solid #2d2d2d !important; padding: 20px !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. AUTHENTICATION LOGIC & CUSTOMIZED UI
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
        <div style='text-align:center; padding: 30px 0;'>
            <h1 style='font-size: 45px; letter-spacing: 2px; color: #c9a84c;'>✦ FEEMO AI ✦</h1>
            <p style='color: #888; font-size: 16px;'>Welcome! Please sign in to access your workspace.</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "RESET PASSWORD"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@email.com")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("LOGIN TO FEEMO", use_container_width=True)
            
            if submit_login:
                try:
                    auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if auth_res.user:
                        st.session_state.user_secret_id = auth_res.user.id
                        st.session_state.first_name = auth_res.user.user_metadata.get("first_name", "User")
                        st.session_state.authenticated = True
                        st.toast(f"Welcome back, {st.session_state.first_name}!")
                        time.sleep(1)
                        st.rerun()
                except Exception:
                    st.error("Invalid email or password.")
    
    with tab2:
        with st.form("signup_form"):
            new_name = st.text_input("Full Name", placeholder="e.g. Faheem Riaz")
            new_email = st.text_input("Email", placeholder="name@email.com")
            new_pass = st.text_input("Create Password", type="password", help="Minimum 6 characters")
            confirm_pass = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("REGISTER ACCOUNT", use_container_width=True)
            
            if submit_signup:
                if new_pass != confirm_pass:
                    st.warning("Passwords do not match.")
                elif len(new_pass) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif not new_name or not new_email:
                    st.warning("Please fill in all fields.")
                else:
                    try:
                        supabase.auth.sign_up({
                            "email": new_email, 
                            "password": new_pass,
                            "options": {"data": {"first_name": new_name}}
                        })
                        st.success("Account created! Check your email to verify your identity.")
                    except Exception as e:
                        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
                            st.error("An account with this email already exists. Please log in.")
                        else:
                            st.error(f"Signup failed: {str(e)}")

    with tab3:
        reset_email = st.text_input("Enter email for reset link", placeholder="your@email.com")
        if st.button("Send Reset Link", use_container_width=True):
            try:
                supabase.auth.reset_password_for_email(reset_email)
                st.success("A reset link has been sent to your email.")
            except:
                st.error("Could not send reset link. Verify the email address.")
                
    st.stop() # Halt execution until user logs in

# 5. DATA SYNC (Load history for logged-in user)
if "messages" not in st.session_state: st.session_state.messages = []
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None

try:
    hist_res = supabase.table("chat_history")\
        .select("id, chat_title")\
        .eq("user_id", st.session_state.user_secret_id)\
        .order("created_at", desc=True)\
        .limit(10).execute()
    recent_activity = hist_res.data if hist_res.data else []
except:
    recent_activity = []

# 6. SIDEBAR (User Profile & History)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.caption(f"👤 Connected as: {st.session_state.first_name}")
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.markdown("<div class='history-label'>MY RECENT ACTIVITY</div>", unsafe_allow_html=True)
    for chat in recent_activity:
        if st.sidebar.button(f"💬 {chat['chat_title'][:25]}...", key=f"btn_{chat['id']}", use_container_width=True):
            msg_res = supabase.table("chat_history").select("full_history").eq("id", chat['id']).execute()
            if msg_res.data:
                st.session_state.messages = msg_res.data[0]['full_history']
                st.session_state.current_chat_id = chat['id']
                st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.rerun()

# 7. MAIN CHAT AREA
st.markdown(f"<h3 style='text-align:center;'>How can I help you today, {st.session_state.first_name}?</h3>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. AI LOGIC & SAVING
if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        # Personalizing the AI with the user's name and profession
        sys_info = f"You are Feemo AI. The user's name is {st.session_state.first_name}, an ML & AI Engineer."
        
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": sys_info}] + st.session_state.messages
        }
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Save to Supabase
        if st.session_state.current_chat_id is None:
            new_chat = supabase.table("chat_history").insert({
                "chat_title": prompt[:30],
                "full_history": st.session_state.messages,
                "user_id": st.session_state.user_secret_id 
            }).execute()
            st.session_state.current_chat_id = new_chat.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.current_chat_id).execute()
            
    except:
        st.error("AI service is busy. Please try again in a moment.")
