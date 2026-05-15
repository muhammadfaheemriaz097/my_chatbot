import streamlit as st
import requests
import PyPDF2
from supabase import create_client

# 1. DATABASE INITIALIZATION
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("Secrets missing. Please check your Streamlit Cloud Secrets.")
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
if "first_name" not in st.session_state: st.session_state.first_name = "User"
if "user_id" not in st.session_state: st.session_state.user_id = None

# 4. SESSION RECOVERY — runs on every page load including after Google redirect
def recover_session():
    try:
        res = supabase.auth.get_session()
        if res and res.session:
            user = res.session.user
            if user and not st.session_state.authenticated:
                st.session_state.authenticated = True
                st.session_state.user_id = user.id
                meta = user.user_metadata or {}
                st.session_state.first_name = (
                    meta.get("full_name") or
                    meta.get("name") or
                    meta.get("first_name") or
                    user.email.split("@")[0]
                )
                return True
    except Exception:
        pass
    return False

# Check URL params for OAuth tokens (Streamlit passes them as query params)
def check_url_token():
    try:
        params = st.query_params
        access_token = params.get("access_token", None)
        refresh_token = params.get("refresh_token", None)
        if access_token and refresh_token:
            res = supabase.auth.set_session(access_token, refresh_token)
            if res and res.session:
                user = res.session.user
                st.session_state.authenticated = True
                st.session_state.user_id = user.id
                meta = user.user_metadata or {}
                st.session_state.first_name = (
                    meta.get("full_name") or
                    meta.get("name") or
                    meta.get("first_name") or
                    user.email.split("@")[0]
                )
                st.query_params.clear()
                return True
    except Exception:
        pass
    return False

# Run both checks
if not st.session_state.authenticated:
    if check_url_token():
        st.rerun()
    elif recover_session():
        st.rerun()

# 5. CSS
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
.stForm { border: 1px solid #2d2d2d !important; background-color: #171717; border-radius: 15px !important; }
.stChatMessage p { color: #ffffff !important; font-size: 15px !important; line-height: 1.8 !important; }
</style>
""", unsafe_allow_html=True)

# 6. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if st.session_state.authenticated:
        st.markdown("<p style='color:#ffffff;'>👤 " + st.session_state.first_name + "</p>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except:
                pass
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    else:
        st.info("Log in to unlock your workspace.")

# 7. LOGIN PAGE
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])

    with t1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = res.user.id
                        meta = res.user.user_metadata or {}
                        st.session_state.first_name = (
                            meta.get("full_name") or
                            meta.get("first_name") or
                            email.split("@")[0]
                        )
                        st.rerun()
                except:
                    st.error("Invalid email or password.")

        st.markdown("<p style='text-align:center;color:#888;margin:10px 0;'>OR</p>", unsafe_allow_html=True)

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
            st.error("Google setup error: " + str(e))

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
    st.stop()

# 8. CHAT WORKSPACE
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

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

    if len(st.session_state.messages) == 0:
        st.markdown("""
<div style='text-align:center;padding:40px 20px;'>
<p style='font-size:40px;'>✦</p>
<p style='color:#4285f4;font-size:18px;font-weight:bold;'>Welcome back, """ + st.session_state.first_name + """!</p>
<p style='color:#666;font-size:14px;'>Ask me anything — I am here to help you 24/7</p>
</div>
""", unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask Feemo AI anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        try:
            headers = {
                "Authorization": "Bearer " + st.secrets["GROQ_API_KEY"],
                "Content-Type": "application/json"
            }
            sys_msg = "You are Feemo AI, a helpful assistant to " + st.session_state.first_name + "."
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
                        st.error("Error: " + str(res))
        except Exception as e:
            st.error("Error: " + str(e))
