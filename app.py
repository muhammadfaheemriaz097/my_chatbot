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
    st.error("Secrets missing. Please check Streamlit Cloud 'Settings > Secrets'.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="✦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 3. SESSION STATE & ADVANCED RECOVERY
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

def check_session():
    """Forces the app to capture the Supabase session after OAuth redirect."""
    try:
        res = supabase.auth.get_session()
        if res and res.session:
            user = res.session.user
            # Only update and rerun if we aren't already marked as authenticated
            if not st.session_state.authenticated:
                st.session_state.user_secret_id = user.id
                st.session_state.first_name = user.user_metadata.get("full_name") or user.user_metadata.get("first_name", "Engineer")
                st.session_state.authenticated = True
                time.sleep(0.5) # Buffer for state synchronization
                st.rerun()
    except Exception:
        pass

# Execute session check immediately on every script run
check_session()

# 4. GEMINI-STYLE CSS
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .block-container { max-width: 850px; padding-top: 2rem !important; margin: auto; }

    /* BRANDING */
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }
    .logo-text {
        font-size: 55px; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .logo-symbol { font-size: 45px; margin-right: 15px; color: #4285f4; text-shadow: 0px 0px 15px rgba(66, 133, 244, 0.6); }

    /* SIDEBAR & UI */
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
        
        # Load History
        try:
            hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(5).execute()
            for c in hist.data:
                if st.button(f"💬 {c['chat_title'][:20]}...", key=f"s_{c['id']}", use_container_width=True):
                    m_data = supabase.table("chat_history").select("full_history").eq("id", c['id']).execute()
                    st.session_state.messages = m_data.data[0]['full_history']
                    st.session_state.chat_id = c['id']
                    st.rerun()
        except: pass

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    else:
        st.info("Log in to access your AI workspace.")

# 6. AUTHENTICATION GATEWAY
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with t1:
        # Standard Login
        with st.form("login_form"):
            e_in = st.text_input("Email")
            p_in = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": e_in, "password": p_in})
                    if res.user:
                        st.session_state.authenticated = True
                        st.rerun()
                except: st.error("Invalid credentials.")
        
        st.markdown("<p style='text-align: center; color: #888;'>OR</p>", unsafe_allow_html=True)
        
        # FAILSAFE GOOGLE LOGIN (LINK BUTTON)
        try:
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
            st.error(f"OAuth setup error: {e}")
            
    with t2:
        with st.form("register_form"):
            n_name = st.text_input("Full Name")
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                    st.success("Check your email for the verification link!")
                except: st.error("Registration failed.")

    with t3:
        st.markdown("### Password Recovery")
        with st.form("reset_password_form"):
            r_email = st.text_input("Email Address")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(r_email)
                    st.success("Reset link sent! Please check your inbox.")
                except: st.error("Could not send reset link.")
    st.stop()

# 7. CHAT WORKSPACE (LOGGED IN)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    with st.expander("📁 PDF Knowledge Base"):
        pdf_file = st.file_uploader("Upload research PDF", type="pdf", label_visibility="collapsed")
        pdf_text = ""
        if pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for i in range(min(len(reader.pages), 15)): # Process up to 15 pages
                extracted = reader.pages[i].extract_text()
                if extracted: pdf_text += extracted + "\n"
            st.success("Knowledge Context Integrated.")

    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Chat Input Logic
    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
            sys_msg = f"You are Feemo AI, a specialized assistant for {st.session_state.first_name}, an ML & AI Engineer."
            if pdf_text: sys_msg += f"\n\nContext from PDF:\n{pdf_text[:7500]}"

            payload = {
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages
            }
            
            with st.chat_message("assistant"):
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
                reply = res["choices"][0]["message"]["content"]
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # Save to Supabase History
            if st.session_state.chat_id is None:
                new_c = supabase.table("chat_history").insert({
                    "chat_title": prompt[:30], 
                    "full_history": st.session_state.messages, 
                    "user_id": st.session_state.user_secret_id
                }).execute()
                st.session_state.chat_id = new_c.data[0]['id']
            else:
                supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.chat_id).execute()
        except Exception:
            st.error("AI connection failed. Check your API limit or key.")
