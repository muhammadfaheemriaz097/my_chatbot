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
if "authenticated"        not in st.session_state: st.session_state.authenticated        = False
if "messages"             not in st.session_state: st.session_state.messages             = []
if "first_name"           not in st.session_state: st.session_state.first_name           = "Engineer"
if "user_id"              not in st.session_state: st.session_state.user_id              = None
if "show_tray"            not in st.session_state: st.session_state.show_tray            = False
if "active_upload_type"   not in st.session_state: st.session_state.active_upload_type   = None
if "theme"                not in st.session_state: st.session_state.theme                = "dark"   # NEW

# 4. THE INTERCEPTOR & SESSION RECOVERY
def sync_identity():
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
                st.session_state.first_name = (
                    meta.get("full_name") or meta.get("first_name") or res.user.email.split("@")[0]
                )
                return True
    except Exception:
        pass
    return False

sync_identity()

# 5. DATABASE HISTORY UTILITIES
def load_chat_history():
    """Fetches the last 5 unique user messages as sidebar conversation starters."""
    if not st.session_state.user_id:
        return []
    try:
        response = (
            supabase.table("chat_history")
            .select("*")
            .eq("user_id", st.session_state.user_id)
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        rows = response.data if response else []
        seen, result = set(), []
        for row in rows:
            msg = row.get("message", {})
            if msg.get("role") == "user":
                preview = msg.get("content", "")[:30]
                if preview not in seen:
                    seen.add(preview)
                    result.append(row)
                    if len(result) == 5:
                        break
        return result
    except:
        return []

def load_full_conversation(up_to_id):
    """Loads all messages in chronological order up to and including the given row id."""
    if not st.session_state.user_id:
        return []
    try:
        response = (
            supabase.table("chat_history")
            .select("*")
            .eq("user_id", st.session_state.user_id)
            .lte("id", up_to_id)
            .order("created_at", desc=False)
            .limit(100)
            .execute()
        )
        rows = response.data if response else []
        return [r["message"] for r in rows if r.get("message")]
    except:
        return []

def save_chat_message(role, content):
    if st.session_state.user_id:
        try:
            supabase.table("chat_history").insert({
                "user_id": st.session_state.user_id,
                "message": {"role": role, "content": content}
            }).execute()
        except:
            pass

# ─────────────────────────────────────────────
# 6. THEME VARIABLES  (NEW)
# ─────────────────────────────────────────────
IS_DARK = st.session_state.theme == "dark"

THEME = {
    "app_bg":        "#0e0e10"  if IS_DARK else "#f4f4f6",
    "text":          "#ececf1"  if IS_DARK else "#111111",
    "sidebar_bg":    "#111111"  if IS_DARK else "#e8e8ed",
    "sidebar_border":"#2d2d2d"  if IS_DARK else "#cccccc",
    "capsule_bg":    "#1e1e22"  if IS_DARK else "#ffffff",
    "capsule_border":"#2d2d34"  if IS_DARK else "#d0d0d8",
    "input_color":   "#ffffff"  if IS_DARK else "#111111",
    "popup_bg":      "#1e1e22"  if IS_DARK else "#ffffff",
    "popup_border":  "#2d2d34"  if IS_DARK else "#cccccc",
    "tray_hover":    "#2a2a30"  if IS_DARK else "#ebebf0",
    "icon_color":    "#9ca3af"  if IS_DARK else "#555555",
    "icon_hover":    "#ffffff"  if IS_DARK else "#000000",
    "msg_text":      "#ffffff"  if IS_DARK else "#111111",
    "divider":       "rgba(255,255,255,0.03)" if IS_DARK else "rgba(0,0,0,0.08)",
}

# ─────────────────────────────────────────────
# 7. TYPING INDICATOR KEYFRAMES  (NEW)
# ─────────────────────────────────────────────
TYPING_INDICATOR_HTML = """
<style>
@keyframes feemo-bounce {
    0%, 80%, 100% { transform: translateY(0);   opacity: 0.4; }
    40%            { transform: translateY(-6px); opacity: 1;   }
}
.feemo-typing {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 10px 14px;
}
.feemo-typing span {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #4285f4;
    display: inline-block;
    animation: feemo-bounce 1.2s infinite ease-in-out;
}
.feemo-typing span:nth-child(1) { animation-delay: 0s;    }
.feemo-typing span:nth-child(2) { animation-delay: 0.2s;  }
.feemo-typing span:nth-child(3) { animation-delay: 0.4s;  }
</style>
<div class="feemo-typing">
    <span></span><span></span><span></span>
</div>
"""

# 8. GLOBAL CSS (theme-aware)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    #MainMenu, footer {{visibility: hidden !important;}}

    .stApp {{
        background-color: {THEME["app_bg"]};
        color: {THEME["text"]};
        font-family: 'Inter', sans-serif;
    }}
    .block-container {{
        max-width: 850px;
        padding-top: 4rem !important;
        margin: auto;
    }}

    /* LOGO */
    .logo-container {{
        display: flex; justify-content: center; align-items: center; margin-bottom: 40px;
    }}
    .logo-text {{
        font-size: 55px; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .logo-symbol {{ font-size: 45px; margin-right: 15px; color: #4285f4; }}

    /* SIDEBAR */
    section[data-testid="stSidebar"] {{
        background-color: {THEME["sidebar_bg"]} !important;
        border-right: 1px solid {THEME["sidebar_border"]} !important;
    }}

    /* CHAT MESSAGES */
    .stChatMessage p {{
        color: {THEME["msg_text"]} !important;
        font-size: 15px !important;
        line-height: 1.8 !important;
    }}

    /* FORM */
    div[data-testid="stForm"] {{
        border: none !important;
        background-color: transparent !important;
        padding: 0 !important;
    }}

    /* ── HIDE THE HIDDEN TRAY TRIGGER BUTTON ── */
    .stButton:has(button[data-testid="tray_toggle_btn"]),
    button[data-testid="tray_toggle_btn"] {{
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }}

    /* ── CHAT INPUT WRAPPER — give it relative positioning ── */
    div[data-testid="stChatInput"] {{
        background-color: {THEME["capsule_bg"]} !important;
        border: 1px solid {THEME["capsule_border"]} !important;
        border-radius: 999px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
        position: relative !important;
    }}

    /* Textarea — push text right so + button has room */
    div[data-testid="stChatInput"] textarea {{
        background: transparent !important;
        color: {THEME["input_color"]} !important;
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
        border: none !important;
        box-shadow: none !important;
        resize: none !important;
        min-height: 44px !important;
        padding-left: 54px !important;
    }}
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: {THEME["icon_color"]} !important;
        opacity: 1 !important;
    }}

    /* Send arrow — blue circle (right side, already there) */
    div[data-testid="stChatInput"] button {{
        background-color: #4285f4 !important;
        border: none !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        color: white !important;
        transition: background 0.2s !important;
    }}
    div[data-testid="stChatInput"] button:hover {{
        background-color: #2a6dd9 !important;
    }}

    /* ── + BUTTON: injected via JS, styled here ── */
    #feemo-plus-btn {{
        position: absolute !important;
        left: 12px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 9999 !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
        border: 1.5px solid {THEME["capsule_border"]} !important;
        background: transparent !important;
        color: {THEME["icon_color"]} !important;
        font-size: 20px !important;
        font-weight: 300 !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
        transition: border-color 0.2s, color 0.2s !important;
        padding: 0 !important;
    }}
    #feemo-plus-btn:hover {{
        border-color: #4285f4 !important;
        color: #4285f4 !important;
    }}

    /* TEXT INPUT */
    .stTextInput > div > div > input {{
        background-color: transparent !important;
        border: none !important;
        color: {THEME["input_color"]} !important;
        font-size: 17px !important;
        padding: 0 !important;
    }}
    .stTextInput > div > div {{
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}

    /* ── GEMINI-STYLE POPUP MENU ── */
    .gemini-tray-wrapper {{
        position: relative;
        width: 260px;
        margin-bottom: 6px;
    }}
    .gemini-tray {{
        background-color: {THEME["popup_bg"]};
        border: 1px solid {THEME["popup_border"]};
        border-radius: 16px;
        padding: 6px 0;
        width: 260px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.35);
        overflow: hidden;
    }}
    .gemini-tray-item {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 11px 18px;
        cursor: pointer;
        transition: background 0.15s;
        color: {THEME["text"]};
        font-size: 14.5px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        border: none;
        background: transparent;
        width: 100%;
        text-align: left;
        text-decoration: none;
    }}
    .gemini-tray-item:hover {{
        background-color: {THEME["tray_hover"]};
    }}
    .gemini-tray-item svg {{
        flex-shrink: 0;
        opacity: 0.75;
    }}
    .gemini-tray-divider {{
        height: 1px;
        background: {THEME["popup_border"]};
        margin: 4px 0;
    }}

    /* kept for tray item hover */
    .tray-item-btn button {{
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 15px !important;
        color: {THEME["text"]} !important;
        padding: 10px 16px !important;
        border-radius: 12px !important;
        transition: background-color 0.2s;
    }}
    .tray-item-btn button:hover {{
        background-color: {THEME["tray_hover"]} !important;
    }}

    /* THEME TOGGLE BUTTON */
    .theme-toggle-btn button {{
        background: transparent !important;
        border: 1px solid {THEME["capsule_border"]} !important;
        border-radius: 20px !important;
        color: {THEME["text"]} !important;
        font-size: 13px !important;
        padding: 4px 14px !important;
        cursor: pointer !important;
        width: auto !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 9. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)

    # ── THEME TOGGLE (NEW) ──────────────────────────────
    toggle_label = "☀️ Light Mode" if IS_DARK else "🌙 Dark Mode"
    st.markdown("<div class='theme-toggle-btn'>", unsafe_allow_html=True)
    if st.button(toggle_label, key="theme_toggle", use_container_width=False):
        st.session_state.theme = "light" if IS_DARK else "dark"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    # ────────────────────────────────────────────────────

    if st.session_state.authenticated:
        st.markdown(f"<p style='color:{THEME['text']};'>👤 <b>{st.session_state.first_name}</b></p>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("<p style='color:#888888; font-size:12px; font-weight:bold;'>RECENT CHATS</p>", unsafe_allow_html=True)
        recent_chats = load_chat_history()

        if recent_chats:
            for chat in recent_chats:
                msg_data = chat.get("message", {})
                preview = msg_data.get("content", "Empty")[:28] + "..."
                if st.button(f"💬 {preview}", key=f"hist_{chat['id']}", use_container_width=True):
                    full_thread = load_full_conversation(chat["id"])
                    if full_thread:
                        st.session_state.messages = full_thread
                        st.rerun()
        else:
            st.caption("No recent chats yet.")

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

# 10. AUTHENTICATION GATE
if not st.session_state.authenticated:
    st.markdown(
        "<div class='logo-container'><span class='logo-symbol'>✦</span>"
        "<h1 class='logo-text'>FEEMO AI</h1></div>",
        unsafe_allow_html=True
    )

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
            email    = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.authenticated = True
                        st.session_state.user_id       = res.user.id
                        meta = res.user.user_metadata or {}
                        st.session_state.first_name    = meta.get("full_name") or email.split("@")[0]
                        st.rerun()
                except:
                    st.error("Invalid email or password.")

    with t2:
        with st.form("register_form"):
            full_name  = st.text_input("Full Name")
            reg_email  = st.text_input("Email")
            reg_pass   = st.text_input("Password", type="password")
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

# 11. CHAT WORKSPACE
else:
    st.markdown(
        "<div class='logo-container'><span class='logo-symbol'>✦</span>"
        "<h1 class='logo-text'>FEEMO AI</h1></div>",
        unsafe_allow_html=True
    )

    # Render message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    attached_context = ""

    # ── GEMINI-STYLE FLOATING TRAY POPUP ──
    if st.session_state.show_tray and not st.session_state.active_upload_type:
        st.markdown(f"""
        <div class="gemini-tray-wrapper">
          <div class="gemini-tray">
            <!-- Upload file -->
            <div class="gemini-tray-item" id="tray_pdf_hint">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{THEME['text']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66L9.41 17.41a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
              </svg>
              Upload file
            </div>
            <!-- Divider -->
            <div class="gemini-tray-divider"></div>
            <!-- Photos -->
            <div class="gemini-tray-item" id="tray_photo_hint">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{THEME['text']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
              Photos
            </div>
            <!-- Import code -->
            <div class="gemini-tray-item" id="tray_code_hint">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{THEME['text']}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
              </svg>
              Import code
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Hidden Streamlit buttons that are triggered by the HTML items via JS click bridge
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("<div class='tray-item-btn'>", unsafe_allow_html=True)
            if st.button("📎 Upload file", key="opt_pdf", use_container_width=True):
                st.session_state.active_upload_type = "pdf"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with col_b:
            st.markdown("<div class='tray-item-btn'>", unsafe_allow_html=True)
            if st.button("🖼️ Photos", key="opt_photo", use_container_width=True):
                st.session_state.active_upload_type = "photo"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with col_c:
            st.markdown("<div class='tray-item-btn'>", unsafe_allow_html=True)
            if st.button("📁 Import code", key="opt_code", use_container_width=True):
                st.session_state.active_upload_type = "code"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # Upload area
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
                            reader   = PyPDF2.PdfReader(pdf_file)
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

    # ── CHAT INPUT: native pill + JS-injected + button ──
    # JS injects the + button directly inside the chat bar DOM after render
    tray_state = "open" if st.session_state.show_tray else "closed"
    st.markdown(f"""
        <script>
        (function() {{
            function inject() {{
                var bar = document.querySelector('div[data-testid="stChatInput"]');
                if (!bar) {{ setTimeout(inject, 80); return; }}
                if (document.getElementById('feemo-plus-btn')) return;
                var btn = document.createElement('button');
                btn.id = 'feemo-plus-btn';
                btn.type = 'button';
                btn.innerText = '+';
                btn.title = 'Attach file';
                btn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    // Toggle tray via URL param — Streamlit picks it up on next interaction
                    var hidden = document.querySelector('[data-testid="tray_toggle_btn"]');
                    if (hidden) {{ hidden.click(); }}
                }});
                bar.appendChild(btn);
            }}
            inject();
        }})();
        </script>
    """, unsafe_allow_html=True)

    # Hidden trigger — zero-size, invisible
    if st.button("＋", key="tray_toggle_btn"):
        st.session_state.show_tray = not st.session_state.show_tray
        if not st.session_state.show_tray:
            st.session_state.active_upload_type = None
        st.rerun()

    prompt = st.chat_input("Ask Feemo AI anything...")

    if prompt:
        full_prompt_payload = prompt
        if attached_context:
            full_prompt_payload = f"{prompt}\n\n{attached_context}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message("user", prompt)
        st.session_state.show_tray        = False
        st.session_state.active_upload_type = None
        st.rerun()

    # ── ASYNC RESPONSE WITH TYPING INDICATOR ──
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":

        # Show typing indicator while fetching
        typing_placeholder = st.empty()
        typing_placeholder.markdown(TYPING_INDICATOR_HTML, unsafe_allow_html=True)

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

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            ).json()

            if "choices" in res:
                reply = res["choices"][0]["message"]["content"]

                # Clear indicator, then display reply
                typing_placeholder.empty()
                st.session_state.messages.append({"role": "assistant", "content": reply})
                save_chat_message("assistant", reply)
                st.rerun()
            else:
                typing_placeholder.empty()

        except Exception as ex:
            typing_placeholder.empty()
            st.error(f"API error: {ex}")
