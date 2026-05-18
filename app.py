import streamlit as st
import requests
import PyPDF2
import base64
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
    "theme": "dark", "staged_context": "", "staged_image_b64": ""
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
            # Save standard conversational string to keep table schema clean
            txt_content = content if isinstance(content, str) else "[Image Shared Asset]"
            supabase.table("chat_history").insert({
                "user_id": st.session_state.user_id,
                "message": {"role": role, "content": txt_content}
            }).execute()
        except:
            pass

# ── 6. THEME ──────────────────────────────────────────────────────────────────
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

# ── 8. GLOBAL CSS ─────────────────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;800&display=swap');

/* Hide upper toolbar elements completely */
.stAppDeployDropdown,
div[data-testid="stHeaderDeveloperTools"],
div[data-testid="stStatusWidget"],
.manage-app-button,
#MainMenu,
footer {{ 
    display: none !important;
    visibility: hidden !important; 
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
}}

.stApp {{ background:{T["bg"]}; color:{T["text"]}; font-family:'Inter',sans-serif; }}
.block-container {{ max-width:860px; padding-top:2rem !important; margin:auto; }}

/* Logo Layout */
.logo-wrap {{ display:flex; justify-content:center; align-items:center; margin-bottom:36px; }}
.logo-txt {{
    font-size:52px; font-weight:800; letter-spacing:-2px; margin:0;
    background:linear-gradient(90deg,#4285f4,#9b72cb,#d96570,#f4af45);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}}
.logo-sym {{ font-size:42px; margin-right:14px; color:#4285f4; }}

/* Sidebar Frame */
section[data-testid="stSidebar"] {{
    background:{T["sb_bg"]} !important;
    border-right:1px solid {T["sb_bdr"]} !important;
}}
.stChatMessage p {{
    color:{T["msg_t"]} !important;
    font-size:15px !important;
    line-height:1.8 !important;
}}

/* Pill chat layouts */
div[data-testid="stBottom"] > div {{
    background: transparent !important;
    padding: 8px 0 16px 0 !important;
}}
div[data-testid="stChatInput"] {{
    background: {T["pill_bg"]} !important;
    border: 1px solid {T["pill_bd"]} !important;
    border-radius: 32px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35) !important;
    padding: 2px 8px !important;
    max-width: 860px !important;
    margin: 0 auto !important;
}}
div[data-testid="stChatInput"] textarea {{
    background: transparent !important;
    color: {T["inp_col"]} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}}
div[data-testid="stChatInput"] textarea::placeholder {{
    color: {T["ph_col"]} !important;
    opacity: 1 !important;
}}
div[data-testid="stChatInput"] button {{
    background: #4285f4 !important;
    border-radius: 50% !important;
    color: #fff !important;
    border: none !important;
}}
div[data-testid="stChatInput"] button:hover {{
    background: #2a6dd9 !important;
}}

/* Tray controller asset formatting */
div[data-testid="stHorizontalBlock"] .tray-col button {{
    background: {T["pill_bg"]} !important;
    border: 1px solid {T["pill_bd"]} !important;
    border-radius: 50% !important;
    color: {T["ph_col"]} !important;
    font-size: 20px !important;
    height: 42px !important;
    width: 42px !important;
    padding: 0 !important;
}}
div[data-testid="stHorizontalBlock"] .tray-col button:hover {{
    color: #4285f4 !important;
    border-color: #4285f4 !important;
}}

/* Floating drawer tray metrics */
.gemini-tray {{
    background:{T["pop_bg"]}; border:1px solid {T["pop_bd"]}; border-radius:20px;
    padding:8px 0; width:220px; box-shadow:0 12px 36px rgba(0,0,0,.5); margin-bottom:8px;
}}
.gemini-tray-item {{
    display:flex; align-items:center; gap:12px; padding:10px 18px;
    color:{T["text"]}; font-size:14px; font-weight:500;
}}
.gemini-tray-divider {{ height:1px; background:{T["pop_bd"]}; margin:4px 0; }}

/* Sidebar button configurations */
.new-chat-btn button {{
    background:linear-gradient(135deg,#4285f4,#9b72cb) !important;
    border:none !important; border-radius:12px !important;
    color:#fff !important; font-weight:600 !important; font-size:14px !important;
}}
.theme-btn button {{
    background:transparent !important;
    border:1px solid {T["pill_bd"]} !important;
    border-radius:20px !important;
    color:{T["text"]} !important;
    font-size:13px !important;
}}
</style>""", unsafe_allow_html=True)

# ── 9. SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;margin-bottom:12px'>✦ Feemo AI</h2>",
                unsafe_allow_html=True)

    st.markdown("<div class='theme-btn'>", unsafe_allow_html=True)
    if st.button("☀️ Light Mode" if IS_DARK else "🌙 Dark Mode", key="theme_toggle"):
        st.session_state.theme = "light" if IS_DARK else "dark"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.authenticated:
        st.markdown(
            f"<p style='color:{T['text']};margin:12px 0 4px'>👤 <b>{st.session_state.first_name}</b></p>",
            unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("<div class='new-chat-btn'>", unsafe_allow_html=True)
        if st.button("✦  New Chat", key="new_chat_btn", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_tray = False
            st.session_state.active_upload_type = None
            st.session_state.staged_context = ""
            st.session_state.staged_image_b64 = ""
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<p style='color:#888;font-size:11px;font-weight:700;"
            "margin:14px 0 6px;letter-spacing:.8px'>RECENT CHATS</p>",
            unsafe_allow_html=True)

        recent = load_chat_history()
        if recent:
            for chat in recent:
                msg     = chat.get("message", {})
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
    st.markdown(
        "<div class='logo-wrap'><span class='logo-sym'>✦</span>"
        "<h1 class='logo-txt'>FEEMO AI</h1></div>",
        unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])

    with t1:
        try:
            g = supabase.auth.sign_in_with_oauth({"provider": "google", "options": {
                "redirect_to": "https://chatbot-2k1njohomp7.streamlit.app/",
                "skip_browser_redirect": True}})
            if g and g.url:
                st.link_button("Continue with Google 🌐", g.url, use_container_width=True)
        except Exception as e:
            st.error(f"Google setup error: {e}")
        st.markdown("<p style='text-align:center;color:#888;margin:10px 0'>OR</p>",
                    unsafe_allow_html=True)
        with st.form("login_form"):
            email    = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    r = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password})
                    if r.user:
                        st.session_state.authenticated = True
                        st.session_state.user_id       = r.user.id
                        meta = r.user.user_metadata or {}
                        st.session_state.first_name    = (
                            meta.get("full_name") or email.split("@")[0])
                        st.rerun()
                except: st.error("Invalid email or password.")

    with t2:
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            reg_email = st.text_input("Email")
            reg_pass  = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({
                        "email": reg_email, "password": reg_pass,
                        "options": {"data": {"full_name": full_name}}})
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
st.markdown(
    "<div class='logo-wrap'><span class='logo-sym'>✦</span>"
    "<h1 class='logo-txt'>FEEMO AI</h1></div>",
    unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 12. TRAY ─────────────────────────────────────────────────────────────────
tray_label = "✖" if st.session_state.show_tray else "＋"
col_tray, col_spacer = st.columns([1, 11])
with col_tray:
    st.markdown("<div class='tray-col'>", unsafe_allow_html=True)
    if st.button(tray_label, key="tray_toggle"):
        st.session_state.show_tray = not st.session_state.show_tray
        if not st.session_state.show_tray:
            st.session_state.active_upload_type = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Tray panel
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

# File uploader panel with Base64 Conversion Pipeline
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
                f = st.file_uploader("PDF Document", type="pdf", key="fu_pdf")
                if f:
                    try:
                        reader = PyPDF2.PdfReader(f)
                        txt = "".join(p.extract_text() or "" for p in reader.pages[:10])
                        st.session_state.staged_context += f"\n[PDF: {f.name}]:\n{txt[:5000]}"
                        st.success(f"Context Staged: {f.name}")
                    except: st.error("Could not parse PDF.")
            elif atype == "photo":
                f = st.file_uploader("Image", type=["png","jpg","jpeg"], key="fu_photo")
                if f:
                    st.image(f, width=200)
                    # Pipeline binary data into an ASCII string for API delivery
                    bytes_data = f.getvalue()
                    st.session_state.staged_image_b64 = base64.b64encode(bytes_data).decode("utf-8")
                    st.success(f"Vision Asset Staged and Processed: {f.name}")
            elif atype == "code":
                f = st.file_uploader("Code / Data file",
                                     type=["txt","py","csv","json"], key="fu_code")
                if f:
                    try:
                        st.session_state.staged_context += (
                            f"\n[File: {f.name}]:\n{f.read().decode('utf-8')[:3000]}")
                        st.success(f"Source Code Staged: {f.name}")
                    except: st.error("Could not decode file.")

# ── 13. CHAT INPUT ────────────────────────────────────────────────────────────
prompt = st.chat_input("Ask Feemo AI anything...")

# ── 14. PROCESS PROMPT ───────────────────────────────────────────────────────
if prompt and prompt.strip():
    # If an image has been staged, we temporarily cache the base64 pointer to pass to vision
    st.session_state["active_image_payload"] = st.session_state.staged_image_b64
    
    full_payload = prompt.strip()
    if st.session_state.staged_context:
        full_payload = f"{full_payload}\n\n{st.session_state.staged_context}"

    st.session_state.messages.append({"role": "user", "content": prompt.strip()})
    save_chat_message("user", prompt.strip())
    
    st.session_state["active_payload"] = full_payload
    st.session_state.show_tray           = False
    st.session_state.active_upload_type = None
    st.session_state.staged_context    = ""
    st.session_state.staged_image_b64  = ""
    st.rerun()

# ── 15. MULTI-MODAL AI VISION RESPONSE INFERENCE ──────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    ph = st.empty()
    ph.markdown(TYPING_HTML, unsafe_allow_html=True)

    current_prompt = st.session_state.get("active_payload", st.session_state.messages[-1]["content"])
    image_b64_payload = st.session_state.get("active_image_payload", "")

    # Historical thread compiling
    api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    
    # ── VISION ROUTER CONDITION ──
    if image_b64_payload:
        # Dynamic execution branch matching multi-modal payload data blocks
        target_model = "llama-3.2-11b-vision-preview"
        api_messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": current_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64_payload}"
                    }
                }
            ]
        })
    else:
        # Default fallback to your standard text-only model pipeline
        target_model = "llama-3.3-70b-versatile"
        api_messages.append({"role": "user", "content": current_prompt})

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + st.secrets["GROQ_API_KEY"],
                "Content-Type": "application/json"
            },
            json={
                "model": target_model,
                "messages": [
                    {"role": "system", "content": f"You are Feemo AI, a highly capable multi-modal assistant to {st.session_state.first_name}."}
                ] + api_messages,
                "max_tokens": 1000
            }
        ).json()

        if "choices" in res:
            reply = res["choices"][0]["message"]["content"]
            ph.empty()
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_chat_message("assistant", reply)
            
            # Clear multi-modal execution memory slots
            if "active_payload" in st.session_state: del st.session_state["active_payload"]
            if "active_image_payload" in st.session_state: del st.session_state["active_image_payload"]
            st.rerun()
        else:
            ph.empty()
            st.error("Inference structure failure.")
    except Exception as ex:
        ph.empty()
        st.error(f"API execution failure: {ex}")
