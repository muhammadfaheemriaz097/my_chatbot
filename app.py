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

# 4. THE INTERCEPTOR & SESSION RECOVERY
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
                st.session_state.first_name = meta.get("full_name") or meta.get("first_name") or res.user.email.split("@")[0]
                return True
    except Exception:
        pass
    return False

# Run the identity check immediately on every script run
sync_identity()

# 5. GEMINI-STYLE UI BRANDING (CSS)
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
    .logo-symbol { font-size: 45px; margin-right: 15px; color: #4285f4; }
    
    /* UI COMPONENTS */
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    .stForm { border: 1px solid #2d2d2d !important; background-color: #171717; border-radius: 15px !important; }
    .stChatMessage p { color: #ffffff !important; font-size: 15px !important; line-height: 1.8 !important; }
    </style>
    """, unsafe_allow_html=True)

# 6. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if st.session_state.authenticated:
        st.markdown(f"<p style='color:#ffffff;'>👤 <b>{st.session_state.first_name}</b></p>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except:
                pass
            # Wipe everything to force login tabs to reappear
            for k in list(st.session_state.keys()): 
                del st.session_state[k]
            st.rerun()
    else:
        st.info("Log in to activate workspace.")

# 7. LOGIC GATE: LOGIN PAGE (SHOWS TABS IF NOT LOGGED IN)
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    # Restored Tabs
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])

    with t1:
        # High-Priority Google OAuth Button
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
            st.error(f"Google setup error: {e}")

        st.markdown("<p style='text-align:center;color:#888;margin:10px 0;'>OR</p>", unsafe_allow_html=True)

        # Standard Email/Password Form
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.authenticated = True
                        meta = res.user.user_metadata or {}
                        st.session_state.first_name = meta.get("full_name") or email.split("@")[0]
                        st.rerun()
                except:
                    st.error("Invalid email or password.")

    with t2:
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            reg_email = st.text_input("Email")
            reg_pass = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({
                        "email": reg_email,
                        "password": reg_pass,
                        "options": {"data": {"full_name": full_name}}
                    })
                    st.success("Verification link sent! Check your email.")
                except:
                    st.error("Signup failed. Try again.")

    with t3:
        st.markdown("### Reset Password")
        with st.form("reset_form"):
            reset_email = st.text_input("Enter Email")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("Link sent! Check your inbox.")
                except:
                    st.error("Reset failed. Try again.")
    
    st.stop() # Prevents the chat interface from loading underneath the login screen

# 8. CHAT WORKSPACE (RUNS ONLY IF AUTHENTICATED)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

    # Knowledge Base Expandable Section
    with st.expander("📁 PDF Knowledge Base"):
        pdf_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
        pdf_text = ""
        if pdf_file:
            try:
                reader = PyPDF2.PdfReader(pdf_file)
                for i in range(min(len(reader.pages), 10)):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        pdf_text += page_text + "\n"
                st.success("PDF Knowledge Integrated.")
            except:
                st.error("Could not read PDF.")

    # Welcome message for empty rooms
    if len(st.session_state.messages) == 0:
        st.markdown(f"""
        <div style='text-align:center;padding:40px 20px;'>
            <p style='font-size:40px;'>✦</p>
            <p style='color:#4285f4;font-size:18px;font-weight:bold;'>Welcome back, {st.session_state.first_name}!</p>
            <p style='color:#666;font-size:14px;'>Ask me anything — I am here to help you 24/7</p>
        </div>
        """, unsafe_allow_html=True)

    # Render History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Interaction Block
    if prompt := st.chat_input("Ask Feemo AI anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        try:
            headers = {
                "Authorization": "Bearer " + st.secrets["GROQ_API_KEY"],
                "Content-Type": "application/json"
            }
            sys_msg = f"You are Feemo AI, a helpful assistant to {st.session_state.first_name}."
            if pdf_text:
                sys_msg += "\n\nContext from PDF:\n" + pdf_text[:7000]

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages,
                "max_tokens": 1000
            }

            with st.chat_message("assistant"):
                with st.spinner("✦ Feemo AI is thinking..."):
                    res = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload
                    ).json()
                    
                    if "choices" in res:
                        reply = res["choices"][0]["message"]["content"]
                        st.markdown(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                    else:
                        st.error(f"Inference error structural issue: {res}")
        except Exception as e:
            st.error(f"Node execution failure: {e}")
