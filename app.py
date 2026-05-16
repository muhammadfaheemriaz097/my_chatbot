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
if "user_id" not in st.session_state: st.session_state.user_id = None
if "show_tray" not in st.session_state: st.session_state.show_tray = False

# 4. THE INTERCEPTOR & SESSION RECOVERY
def sync_identity():
    """Forces the app to exchange the Google code for a session immediately."""
    try:
        params = st.query_params
        if "code" in params:
            supabase.auth.get_session()
            st.query_params.clear()
            st.session_state.authenticated = True
            st.rerun()

        res = supabase.auth.get_user()
        if res and res.user:
            if not st.session_state.authenticated:
                st.session_state.authenticated = True
                st.session_state.user_id = res.user.id
                meta = res.user.user_metadata or {}
                st.session_state.first_name = meta.get("full_name") or meta.get("first_name") or res.user.email.split("@")[0]
                return True
    except Exception:
        pass
    return False

sync_identity()

# 5. DATABASE HISTORY UTILITIES
def load_chat_history():
    """Fetches past chat logs from the Supabase backend."""
    if not st.session_state.user_id:
        return []
    try:
        response = supabase.table("chat_history")\
            .select("*")\
            .eq("user_id", st.session_state.user_id)\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        return response.data if response else []
    except:
        return []

def save_chat_message(role, content):
    """Commits a single message node directly to the database layer."""
    if st.session_state.user_id:
        try:
            message_payload = {"role": role, "content": content}
            supabase.table("chat_history").insert({
                "user_id": st.session_state.user_id,
                "message": message_payload
            }).execute()
        except:
            pass

# 6. PREMIUM GEMINI-STYLE UI BRANDING & LAYOUT FIXES (CSS)
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
    
    /* SIDEBAR & CHAT CHIPS */
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    .stChatMessage p { color: #ffffff !important; font-size: 15px !important; line-height: 1.8 !important; }
    
    /* THE PREMIUM WRAPPED FLOATING INPUT BAR */
    div[data-testid="stForm"] {
        border: none !important;
        background-color: transparent !important;
        padding: 0 !important;
        margin-top: 1.5rem;
    }
    .premium-chat-bar {
        background-color: #1e1e22;
        border: 1px solid #2d2d34;
        border-radius: 32px !important;
        padding: 10px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    }
    
    /* BLEND INNER STREAMLIT TEXT INPUT INTO INVISIBLE BACKGROUND */
    .stTextInput > div > div > input {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 16px !important;
    }
    .stTextInput > div > div {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }
    
    /* FORCE THE TRAY TOGGLE BUTTON TO STAY BORDERLESS AND SLEEK */
    div[data-testid="column"] button {
        background-color: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        font-size: 20px !important;
        padding: 0 !important;
        line-height: 1 !important;
    }
    div[data-testid="column"] button:hover {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 7. SIDEBAR (WITH RECENT CHATS SUMMARY)
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if st.session_state.authenticated:
        st.markdown(f"<p style='color:#ffffff;'>👤 <b>{st.session_state.first_name}</b></p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("<p style='color:#888888; font-size:12px; font-weight:bold;'>RECENT CHATS</p>", unsafe_allow_html=True)
        recent_chats = load_chat_history()
        
        if recent_chats:
            for chat in recent_chats:
                msg_data = chat.get("message", {})
                preview = msg_data.get("content", "Empty conversation")[:25] + "..."
                if st.button(f"💬 {preview}", key=f"hist_{chat['id']}", use_container_width=True):
                    st.toast("Loading conversation history...")
                    if msg_data:
                        st.session_state.messages = [msg_data]
                        st.rerun()
        else:
            st.caption("No recent logs found.")
        
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
        st.info("Log in to activate workspace.")

# 8. LOGIC GATE: AUTHENTICATION INTERFACES
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])

    with t1:
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
    st.stop()

# 9. CHAT WORKSPACE (PREMIUM INTEGRATED INTERFACE DESIGN)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

    # Render ongoing stream elements
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Baseline text aggregation variables
    attached_context = ""

    # Render expandable context upload deck if state toggle is flagged open
    if st.session_state.show_tray:
        st.markdown("<p style='color:#6d6d75; font-size:13px; font-weight:600; margin-bottom:6px;'>📂 Staging Attachment Assets:</p>", unsafe_allow_html=True)
        with st.container(border=True):
            tray_tabs = st.tabs(["📄 Knowledge PDF", "📷 Analysis Photo", "⚙️ Raw Code/Data"])
            
            with tray_tabs[0]:
                pdf_file = st.file_uploader("Select Knowledge Base Source Document", type="pdf", label_visibility="collapsed")
                if pdf_file:
                    try:
                        reader = PyPDF2.PdfReader(pdf_file)
                        pdf_text = ""
                        for i in range(min(len(reader.pages), 10)):
                            page_text = reader.pages[i].extract_text()
                            if page_text: pdf_text += page_text + "\n"
                        attached_context += f"\n[Attached PDF Content]:\n{pdf_text[:5000]}"
                        st.success(f"Context integrated: {pdf_file.name}")
                    except Exception as e:
                        st.error(f"Could not read PDF bytes structural layer: {e}")

            with tray_tabs[1]:
                photo_file = st.file_uploader("Select Target Frame for Vision Diagnostics", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
                if photo_file:
                    st.image(photo_file, caption="Staged Image Asset", width=250)
                    attached_context += f"\n[User Attached an Image: {photo_file.name}]"
                    st.info("Vision asset staged. Pipeline will process on prompt execution.")

            with tray_tabs[2]:
                other_file = st.file_uploader("Select Supplemental Dataset", type=["txt", "csv", "json"], label_visibility="collapsed")
                if other_file:
                    try:
                        raw_bytes = other_file.read().decode("utf-8")
                        attached_context += f"\n[Attached File Context ({other_file.name})]:\n{raw_bytes[:3000]}"
                        st.success(f"Staged data payload: {other_file.name}")
                    except:
                        st.error("Failed parsing asset matrix to string layout tokens.")

    # HTML Form wrapper containing interactive inline row
    with st.form("premium_chat_wrapper", clear_on_submit=True):
        
        # Open layout panel structure
        st.markdown("<div class='premium-chat-bar'>", unsafe_allow_html=True)
        
        # Partition horizontal real estate across 3 core columns matching reference blueprint
        col_plus, col_field, col_meta = st.columns([1, 14, 2])
        
        with col_plus:
            # Inline interaction anchor symbol toggle
            btn_symbol = "✖" if st.session_state.show_tray else "＋"
            if st.form_submit_button(btn_symbol, help="Click to open or close attachment tray"):
                st.session_state.show_tray = not st.session_state.show_tray
                st.rerun()
                
        with col_field:
            # Borderless text data pipeline landing zone
            prompt = st.text_input("Ask Gemini...", placeholder="Ask Feemo AI anything...", label_visibility="collapsed")
            
        with col_meta:
            # Right aligned metrics tags tracking reference picture style configurations
            st.markdown(
                "<div style='display:flex; justify-content:flex-end; align-items:center; gap:14px; height:100%; margin-top:4px; font-family:sans-serif;'>"
                "<span style='color:#6d6d75; font-size:14px; font-weight:500; cursor:pointer;'>Fast ▾</span>"
                "<span style='color:#6d6d75; font-size:16px; cursor:pointer;'>🎙️</span>"
                "</div>", 
                unsafe_allow_html=True
            )
            
        # Close layout panel structure
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Transparent keyboard enter trigger tracker (Invisible element, catches returns)
        submit_chat = st.form_submit_button("SUBMIT", use_container_width=True)

    # Run inference sequence on positive submit trigger executions
    if submit_chat and prompt:
        full_prompt_payload = prompt
        if attached_context:
            full_prompt_payload = f"{prompt}\n\n{attached_context}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message("user", prompt)
            
        try:
            headers = {
                "Authorization": "Bearer " + st.secrets["GROQ_API_KEY"],
                "Content-Type": "application/json"
            }
            sys_msg = f"You are Feemo AI, a helpful assistant to {st.session_state.first_name}."

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages[:-1] + [{"role": "user", "content": full_prompt_payload}],
                "max_tokens": 1000
            }

            # Pre-rerun to draw the user message immediately
            st.rerun()
        except:
            pass

    # Async response rendering block fallback 
    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        try:
            headers = {
                "Authorization": "Bearer " + st.secrets["GROQ_API_KEY"],
                "Content-Type": "application/json"
            }
            sys_msg = f"You are Feemo AI, a helpful assistant to {st.session_state.first_name}."
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages,
                "max_tokens": 1000
            }
            
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            if "choices" in res:
                reply = res["choices"][0]["message"]["content"]
                st.session_state.messages.append({"role": "assistant", "content": reply})
                save_chat_message("assistant", reply)
                st.session_state.show_tray = False
                st.rerun()
        except:
            pass
