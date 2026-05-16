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
if "active_upload_type" not in st.session_state: st.session_state.active_upload_type = None

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

# 6. FLOATING CONTEXT MENU ENGINE (CSS)
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .block-container { max-width: 850px; padding-top: 4rem !important; margin: auto; }
    
    /* LOGO BRANDING */
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 40px; }
    .logo-text {
        font-size: 55px; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .logo-symbol { font-size: 45px; margin-right: 15px; color: #4285f4; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #2d2d2d !important; }
    .stChatMessage p { color: #ffffff !important; font-size: 15px !important; line-height: 1.8 !important; }
    
    /* REMOVE ALL NATIVE STREAMLIT FORM STRIPES */
    div[data-testid="stForm"] {
        border: none !important;
        background-color: transparent !important;
        padding: 0 !important;
    }
    
    /* CAPSULE MAIN INPUT WRAPPER PANEL */
    .gemini-capsule-panel {
        background-color: #1e1e22;
        border: 1px solid #2d2d34;
        border-radius: 28px !important;
        padding: 16px 24px;
        box-shadow: 0 12px 42px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        gap: 12px;
        position: relative;
    }
    
    /* INVISIBLE TEXT INPUT */
    .stTextInput > div > div > input {
        background-color: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 17px !important;
        padding: 0 !important;
    }
    .stTextInput > div > div {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    
    /* REPLICATED FLOATING OVERLAY DIALOG */
    .floating-popup-menu {
        background-color: #1e1e22;
        border: 1px solid #2d2d34;
        border-radius: 20px;
        padding: 8px;
        width: 240px;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6);
        margin-bottom: -10px;
    }
    
    /* ACTIONS DECK CONTROL BAR */
    .bottom-action-row {
        display: flex;
        align-items: center;
        width: 100%;
        border-top: 1px solid rgba(255, 255, 255, 0.03);
        padding-top: 10px;
    }
    
    /* BORDERLESS TOGGLE ICON STYLING */
    div[data-testid="column"] button {
        background-color: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        font-size: 24px !important;
        padding: 0 !important;
        line-height: 1 !important;
        width: auto !important;
        text-align: left !important;
    }
    div[data-testid="column"] button:hover {
        color: #ffffff !important;
    }
    
    /* TRAY SELECTION ITEM SNIPPET ACTION BUTTONS */
    .tray-item-btn button {
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 15px !important;
        color: #ececf1 !important;
        padding: 10px 16px !important;
        border-radius: 12px !important;
        transition: background-color 0.2s;
    }
    .tray-item-btn button:hover {
        background-color: #2a2a30 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 7. SIDEBAR (WITH RECENT CHATS)
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

# 8. LOGIC GATE: AUTHENTICATION
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

# 9. CHAT WORKSPACE (EXACT FLOATING MENU MATCH)
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

    # Render History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    attached_context = ""

    # --- NEW: TRUE REPLICA FLOATING POPUP OVERLAY ---
    if st.session_state.show_tray and not st.session_state.active_upload_type:
        st.markdown("<div class='floating-popup-menu'>", unsafe_allow_html=True)
        
        # Action columns inside the menu to match the look
        st.markdown("<div class='tray-item-btn'>", unsafe_allow_html=True)
        if st.button("📎 &nbsp; Upload file", key="opt_pdf", use_container_width=True):
            st.session_state.active_upload_type = "pdf"
            st.rerun()
        if st.button("🖼️ &nbsp; Photos", key="opt_photo", use_container_width=True):
            st.session_state.active_upload_type = "photo"
            st.rerun()
        if st.button("📁 &nbsp; Import code", key="opt_code", use_container_width=True):
            st.session_state.active_upload_type = "code"
            st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Render the upload area once a menu option is picked
    if st.session_state.active_upload_type:
        with st.container(border=True):
            c_header, c_close = st.columns([12, 1])
            with c_close:
                if st.button("✖", key="close_uploader"):
                    st.session_state.active_upload_type = None
                    st.session_state.show_tray = False
                    st.rerun()
                    
            with c_header:
                if st.session_state.active_upload_type == "pdf":
                    pdf_file = st.file_uploader("Select Knowledge Document", type="pdf")
                    if pdf_file:
                        try:
                            reader = PyPDF2.PdfReader(pdf_file)
                            pdf_text = ""
                            for i in range(min(len(reader.pages), 10)):
                                page_text = reader.pages[i].extract_text()
                                if page_text: pdf_text += page_text + "\n"
                            attached_context += f"\n[Attached PDF Content]:\n{pdf_text[:5000]}"
                            st.success(f"Context loaded: {pdf_file.name}")
                        except:
                            st.error("Could not parse file structure.")

                elif st.session_state.active_upload_type == "photo":
                    photo_file = st.file_uploader("Select Target Frame", type=["png", "jpg", "jpeg"])
                    if photo_file:
                        st.image(photo_file, width=200)
                        attached_context += f"\n[User Attached an Image: {photo_file.name}]"
                        st.info("Vision asset staged.")

                elif st.session_state.active_upload_type == "code":
                    other_file = st.file_uploader("Select Code Script / Dataset", type=["txt", "py", "csv", "json"])
                    if other_file:
                        try:
                            raw_bytes = other_file.read().decode("utf-8")
                            attached_context += f"\n[Attached File Context ({other_file.name})]:\n{raw_bytes[:3000]}"
                            st.success(f"Code data staged: {other_file.name}")
                        except:
                            st.error("Failed to decode asset.")

    # --- GEMINI INPUT CAPSULE BAR ---
    with st.form("gemini_layout_form", clear_on_submit=True):
        st.markdown("<div class='gemini-capsule-panel'>", unsafe_allow_html=True)
        
        # Row 1: Chat Field
        st.markdown("<div class='top-input-row'>", unsafe_allow_html=True)
        prompt = st.text_input("Ask Gemini...", placeholder="Ask Gemini", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Row 2: Bottom Menu Icons
        st.markdown("<div class='bottom-action-row'>", unsafe_allow_html=True)
        col_plus, col_empty = st.columns([1, 14])
        
        with col_plus:
            # Replicated plain "+" icon button
            if st.form_submit_button("＋"):
                st.session_state.show_tray = not st.session_state.show_tray
                # Reset item states if the menu is closed
                if not st.session_state.show_tray:
                    st.session_state.active_upload_type = None
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Hidden submit logic
        st.markdown("<div style='display:none;'>", unsafe_allow_html=True)
        submit_chat = st.form_submit_button("SUBMIT")
        st.markdown("</div>", unsafe_allow_html=True)

    # Process submission
    if submit_chat and prompt:
        full_prompt_payload = prompt
        if attached_context:
            full_prompt_payload = f"{prompt}\n\n{attached_context}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message("user", prompt)
        st.session_state.show_tray = False
        st.session_state.active_upload_type = None
        st.rerun()

    # Async Response Parser
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
                st.rerun()
        except:
            pass
