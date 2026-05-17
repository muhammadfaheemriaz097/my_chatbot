import streamlit as st
import requests
import PyPDF2
from supabase import create_client

# ── 1. DATABASE INIT ──────────────────────────────────────────────────────────
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# ── 2. PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide",
                   initial_sidebar_state="expanded")

# ── 3. SESSION STATE ──────────────────────────────────────────────────────────
for k, v in {
    "authenticated": False, "messages": [], "first_name": "Engineer",
    "user_id": None, "show_tray": False, "active_upload_type": None,
    "theme": "dark", "staged_context": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── 4. AUTH RECOVERY ──────────────────────────────────────────────────────────
def sync_identity():
    try:
        if "code" in st.query_params:
            supabase.auth.get_session()
            st.query_params.clear()
            st.session_state.authenticated = True
            st.rerun()
        res = supabase.auth.get_user()
        if res and res.user and not st.session_state.authenticated:
            st.session_state.authenticated = True
            st.session_state.user_id = res.user.id
            meta = res.user.user_metadata or {}
            st.session_state.first_name = (
                meta.get("full_name") or meta.get("first_name")
                or res.user.email.split("@")[0]
            )
    except Exception:
        pass

sync_identity()

# ── 5. DB UTILITIES ───────────────────────────────────────────────────────────
def load_chat_history():
    if not st.session_state.user_id:
        return []
    try:
        rows = (supabase.table("chat_history").select("*")
                .eq("user_id", st.session_state.user_id)
                .order("created_at", desc=True).limit(40).execute()).data or []
        seen, result = set(), []
        for row in rows:
            msg = row.get("message", {})
            if msg.get("role") == "user":
                key = msg.get("content", "")[:40]
                if key not in seen:
                    seen.add(key)
                    result.append(row)
                    if len(result) == 6:
                        break
        return result
    except:
        return []

def load_full_conversation(up_to_id):
    if not st.session_state.user_id:
        return []
    try:
        rows = (supabase.table("chat_history").select("*")
                .eq("user_id", st.session_state.user_id)
                .lte("id", up_to_id)
                .order("created_at", desc=False).limit(100).execute()).data or []
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

# ── 6. THEME CONFIGURATION ────────────────────────────────────────────────────
IS_DARK = st.session_state.theme == "dark"
T = {
    "bg":      "#0e0e10" if IS_DARK else "#f4f4f6",
    "text":    "#ececf1" if IS_DARK else "#111111",
    "sb_bg":   "#111111" if IS_DARK else "#e8e8ed",
    "sb_bdr":  "#2d2d2d" if IS_DARK else "#cccccc",
    "pill_bg": "#1e1e22" if IS_DARK else "#ffffff",
    "pill_bd": "#3a3a44" if IS_DARK else "#d0d0d8",
    "inp_col": "#ffffff" if IS_DARK else "#111111",
    "ph_col":  "#6b7280" if IS_DARK else "#9ca3af",
    "pop_bg":  "#1e1e22" if IS_DARK else "#ffffff",
    "pop_bd":  "#3a3a44" if IS_DARK else "#cccccc",
    "hov":     "#2a2a30" if IS_DARK else "#ebebf0",
    "msg_t":   "#ffffff" if IS_DARK else "#111111",
}

# ── 7. TYPING INDICATOR ───────────────────────────────────────────────────────
TYPING_HTML = """
<style>
@keyframes fb{0%,80%,100%{transform:translateY(0);opacity:.4}40%{transform:translateY(-6px);opacity:1}}
.ft{display:flex;align-items:center;gap:5px;padding:12px 16px}
.ft span{width:8px;height:8px;border-radius:50%;background:#4285f4;display:inline-block;animation:fb 1.2s infinite ease-in-out}
.ft span:nth-child(2){animation-delay:.2s}.ft span:nth-child(3){animation-delay:.4s}
</style>
<div class="ft"><span></span><span></span><span></span></div>
"""

# ── 8. GLOBAL CSS OVERRIDES ───────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

/* Hide Dev Header Elements */
header[data-testid="stHeader"] {{ visibility: hidden !important; height: 0px !important; }}
div[data-testid="stStatusWidget"] {{ visibility: hidden !important; }}
.manage-app-button {{ display: none !important; }}

#MainMenu,footer{{visibility:hidden!important}}
.stApp{{background:{T["bg"]};color:{T["text"]};font-family:'Inter',sans-serif}}
.block-container{{max-width:860px;padding-top:2.5rem!important;margin:auto}}

/* Brand Logo Layout */
.logo-wrap{{display:flex;justify-content:center;align-items:center;margin-bottom:36px}}
.logo-txt{{font-size:52px;font-weight:800;letter-spacing:-2px;margin:0;
  background:linear-gradient(90deg,#4285f4,#9b72cb,#d96570,#f4af45);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.logo-sym{{font-size:42px;margin-right:14px;color:#4285f4}}

/* Navigation Sidebar */
section[data-testid="stSidebar"]{{background:{T["sb_bg"]}!important;border-right:1px solid {T["sb_bdr"]}!important}}
.stChatMessage p{{color:{T["msg_t"]}!important;font-size:15px!important;line-height:1.8!important}}

/* Base Layout Wrapper Panel */
.chat-pill-outer{{
  display:flex;align-items:center;background:{T["pill_bg"]};border:1px solid {T["pill_bd"]};
  border-radius:32px;padding:6px 14px;box-shadow:0 8px 32px rgba(0,0,0,.35);margin-top:10px;
}}

/* Structural Inline Configuration */
div[data-testid="stHorizontalBlock"]{{gap:12px!important;align-items:center!important;width:100%!important}}
div[data-testid="column"]{{padding:0!important;min-width:0!important}}

/* Borderless Utility Buttons */
div[data-testid="column"] button{{
  background:transparent!important;border:none!important;color:{T["ph_col"]}!important;
  font-size:22px!important;padding:0!important;line-height:1!important;width:auto!important;
}}
div[data-testid="column"] button:hover{{color:#4285f4!important}}

/* Text Area Style Neutralization */
.text-col .stTextInput>div>div>input{{
  background:transparent!important;border:none!important;box-shadow:none!important;
  color:{T["inp_col"]}!important;font-size:16px!important;padding:4px 0!important;
}}
.text-col .stTextInput>div>div{{border:none!important;background:transparent!important;box-shadow:none!important;padding:0!important}}
.text-col .stTextInput>label{{display:none!important}}

/* Gemini Menu Panel */
.gemini-tray{{
  background:{T["pop_bg"]};border:1px solid {T["pop_bd"]};border-radius:20px;
  padding:8px 0;width:240px;box-shadow:0 12px 36px rgba(0,0,0,.5);margin-bottom:8px;
}}
.gemini-tray-item{{
  display:flex;align-items:center;gap:12px;padding:10px 18px;color:{T["text"]};font-size:14.5px;font-weight:500;
  border:none;background:transparent;width:100%;text-align:left;cursor:pointer;
}}
.gemini-tray-divider{{height:1px;background:{T["pop_bd"]};margin:6px 0}}
.tray-item-btn button{{
  text-align:left!important;justify-content:flex-start!important;font-size:15px!important;color:{T["text"]}!important;
  padding:10px 16px!important;border-radius:12px!important;width:100%!important;
}}
.tray-item-btn button:hover{{background:{T["hov"]}!important}}

/* Control Button Custom Styles */
.new-chat-btn button{{
  background:linear-gradient(135deg,#4285f4,#9b72cb)!important;border:none!important;border-radius:12px!important;
  color:#fff!important;font-weight:600!important;font-size:14px!important;padding:10px 0!important;
}}
.new-chat-btn button:hover{{opacity:.9!important}}
.theme-btn button{{background:transparent!important;border:1px solid {T["pill_bd"]}!important;border-radius:20px!important;color:{T["text"]}!important;font-size:13px!important;padding:4px 14px!important;width:auto!important}}
</style>""", unsafe_allow_html=True)

# ── 9. SIDEBAR NAVIGATION ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;margin-bottom:12px'>✦ Feemo AI</h2>", unsafe_allow_html=True)

    st.markdown("<div class='theme-btn'>", unsafe_allow_html=True)
    if st.button("☀️ Light Mode" if IS_DARK else "🌙 Dark Mode", key="theme_toggle"):
        st.session_state.theme = "light" if IS_DARK else "dark"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.authenticated:
        st.markdown(f"<p style='color:{T['text']};margin:12px 0 4px'>👤 <b>{st.session_state.first_name}</b></p>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("<div class='new-chat-btn'>", unsafe_allow_html=True)
        if st.button("✦  New Chat", key="new_chat_btn", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_tray = False
            st.session_state.active_upload_type = None
            st.session_state.staged_context = ""
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<p style='color:#888;font-size:11px;font-weight:700;margin:14px 0 6px;letter-spacing:.8px'>RECENT CHATS</p>", unsafe_allow_html=True)

        recent = load_chat_history()
        if recent:
            for chat in recent:
                msg = chat.get("message", {})
                preview = msg.get("content", "Chat")[:30] + "…"
                if st.button(f"💬 {preview}", key=f"h_{chat['id']}", use_container_width=True):
                    thread = load_full_conversation(chat["id"])
                    st.session_state.messages = thread if thread else [msg]
                    st.rerun()
        else:
            st.caption("No recent chats yet.")

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            try: supabase.auth.sign_out()
            except: pass
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    else:
        st.info("Log in to start chatting.")

# ── 10. AUTH GATEWAY ──────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown("<div class='logo-wrap'><span class='logo-sym'>✦</span><h1 class='logo-txt'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])

    with t1:
        try:
            g = supabase.auth.sign_in_with_oauth({"provider": "google", "options": {
                "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/", "skip_browser_redirect": True}})
            if g and g.url:
                st.link_button("Continue with Google 🌐", g.url, use_container_width=True)
        except Exception as e:
            st.error(f"Google setup error: {e}")
        st.markdown("<p style='text-align:center;color:#888;margin:10px 0'>OR</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    r = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if r.user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = r.user.id
                        meta = r.user.user_metadata or {}
                        st.session_state.first_name = (meta.get("full_name") or email.split("@")[0])
                        st.rerun()
                except: st.error("Invalid email or password.")

    with t2:
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            reg_email = st.text_input("Email")
            reg_pass  = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": reg_email, "password": reg_pass, "options": {"data": {"full_name": full_name}}})
                    st.success("Check your email for the verification link.")
                except: st.error("Signup failed. Try again.")

    with t3:
        with st.form("reset_form"):
            reset_email = st.text_input("Enter your email")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(reset_email)
                    st.success("Reset link sent!")
                except: st.error("Reset failed. Try again.")
    st.stop()

# ── 11. CHAT WORKSPACE ────────────────────────────────────────────────────────
st.markdown("<div class='logo-wrap'><span class='logo-sym'>✦</span><h1 class='logo-txt'>FEEMO AI</h1></div>", unsafe_allow_html=True)

# Render Chat History Nodes
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Render Floating Context Selection Menu Overlay
if st.session_state.show_tray and not st.session_state.active_upload_type:
    st.markdown(f"""
    <div class="gemini-tray">
      <div class="gemini-tray-item">📎 &nbsp; Upload file</div>
      <div class="gemini-tray-divider"></div>
      <div class="gemini-tray-item">🖼️ &nbsp; Photos</div>
      <div class="gemini-tray-divider"></div>
      <div class="gemini-tray-item">📁 &nbsp; Import code</div>
    </div>""", unsafe_allow_html=True)
    
    ca, cb, cc = st.columns([1, 1, 1])
    with ca:
        if st.button("📎 Upload file", key="opt_pdf", use_container_width=True):
            st.session_state.active_upload_type = "pdf"; st.rerun()
    with cb:
        if st.button("🖼️ Photos", key="opt_photo", use_container_width=True):
            st.session_state.active_upload_type = "photo"; st.rerun()
    with cc:
        if st.button("📁 Import code", key="opt_code", use_container_width=True):
            st.session_state.active_upload_type = "code"; st.rerun()

# Render Explicit File Context Capture Drops
if st.session_state.active_upload_type:
    with st.container(border=True):
        ch, cc2 = st.columns([12, 1])
        with cc2:
            if st.button("✖", key="close_uploader"):
                st.session_state.active_upload_type = None
                st.session_state.show_tray = False
                st.rerun()
        with ch:
            atype = st.session_state.active_upload_type
            if atype == "pdf":
                f = st.file_uploader("PDF Document", type="pdf")
                if f:
                    try:
                        reader = PyPDF2.PdfReader(f)
                        txt = "".join(p.extract_text() or "" for p in reader.pages[:10])
                        st.session_state.staged_context += f"\n[PDF: {f.name}]:\n{txt[:5000]}"
                        st.success(f"Context Staged: {f.name}")
                    except: st.error("Could not parse PDF.")
            elif atype == "photo":
                f = st.file_uploader("Image", type=["png", "jpg", "jpeg"])
                if f:
                    st.image(f, width=200)
                    st.session_state.staged_context += f"\n[Image: {f.name}]"
                    st.success(f"Vision Asset Staged: {f.name}")
            elif atype == "code":
                f = st.file_uploader("Code / Data file", type=["txt", "py", "csv", "json"])
                if f:
                    try:
                        st.session_state.staged_context += f"\n[File: {f.name}]:\n{f.read().decode('utf-8')[:3000]}"
                        st.success(f"Source Code Staged: {f.name}")
                    except: st.error("Could not decode file.")

# ── CAPSULE CHAT PILL BAR INTERFACE ───────────────────────────────────────────
st.markdown("<div class='chat-pill-outer'>", unsafe_allow_html=True)
col_plus, col_text, col_send = st.columns([0.6, 14.8, 0.6])

with col_plus:
    # Explicit formless button handles overlay layout switches cleanly
    if st.button("＋", key="tray_toggle_trigger"):
        st.session_state.show_tray = not st.session_state.show_tray
        if not st.session_state.show_tray:
            st.session_state.active_upload_type = None
        st.rerun()

with col_text:
    st.markdown("<div class='text-col'>", unsafe_allow_html=True)
    prompt = st.text_input("msg", placeholder="Ask Feemo AI anything…", label_visibility="collapsed", key="user_prompt_input")
    st.markdown("</div>", unsafe_allow_html=True)

with col_send:
    # Clicking this or running native keyboard enters executes code evaluations perfectly
    send_triggered = st.button("➤", key="send_action_trigger")
st.markdown("</div>", unsafe_allow_html=True)

# Parse Message and Payload Deliveries 
if (send_triggered or (prompt and prompt != "")) and prompt:
    # Gather any context
