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

# ── 8. GLOBAL CSS OVERRIDES ───────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;800&display=swap');

/* Hide GitHub elements and upper toolbar completely */
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

/* Logo Graphic Layout */
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

/* Clear native borders on custom inputs */
div[data-testid="stForm"] {{
    border: none !important;
    background-color: transparent !important;
    padding: 0 !important;
    box-shadow: none !important;
}}

/* UNIFIED SINGLE-ROW CAPSULE CHAT PILL BAR */
.chat-pill-outer {{
  display: flex;
  align-items: center;
  background: {T["pill_bg"]};
  border: 1px solid {T["pill_bd"]};
  border-radius: 32px;
  padding: 6px 18px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  width: 100%;
  margin-top: 20px;
}}

div[data-testid="stHorizontalBlock"] {{
    gap: 0px !important;
    align-items: center !important;
    width: 100% !important;
}}
div[data-testid="column"] {{
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
}}

/* Left Plus button styling inside capsule */
.plus-col-style button {{
    background: transparent !important;
    border: none !important;
    color: {T["ph_col"]} !important;
    font-size: 26px !important;
    font-weight: 300 !important;
    padding: 0 !important;
    margin-right: 12px !important;
    line-height: 1 !important;
    width: auto !important;
    box-shadow: none !important;
}}
.plus-col-style button:hover {{ color: #4285f4 !important; }}

/* Borderless center prompt input styling */
.text-col-style .stTextInput>div>div>input {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: {T["inp_col"]} !important;
  font-size: 16px !important;
  padding: 4px 0 !important;
  width: 100% !important;
}}
.text-col-style .stTextInput>div>div {{
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}}
.text-col-style .stTextInput>label {{ display: none !important; }}

/* Right hand send arrow button styling */
.send-col-style button {{
  background: #4285f4 !important;
  border: none !important;
  border-radius: 50% !important;
  width: 34px !important;
  height: 34px !important;
  color: #ffffff !important;
  font-size: 14px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0 !important;
  cursor: pointer !important;
  box-shadow: none !important;
}}
.send-col-style button:hover {{ background: #2a6dd9 !important; }}

/* Option menu overlay configuration sets */
.gemini-tray {{
  background: {T["pop_bg"]};
  border: 1px solid {T["pop_bd"]};
  border-radius: 20px;
  padding: 8px 0;
  width: 240px;
  box-shadow: 0 12px 36px rgba(0,0,0,0.5);
  margin-bottom: 12px;
}}
.gemini-tray-item {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 18px;
  color: {T["text"]};
  font-size: 14.5px;
  font-weight: 500;
}}
.gemini-tray-divider {{ height: 1px; background: {T["pop_bd"]}; margin: 6px 0; }}
.tray-item-btn button {{
  text-align: left !important;
  justify-content: flex-start !important;
  font-size: 15px !important;
  color: {T["text"]} !important;
  padding: 10px 16px !important;
  border-radius: 12px !important;
  width: 100% !important;
}}
.tray-item-btn button:hover {{ background: {T["hov"]} !important; }}

.new-chat-btn button {{
  background: linear-gradient(135deg,#4285f4,#9b72cb)!important;
  border: none !important;
  border-radius: 12px !important;
  color: #fff !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  padding: 10px 0 !important;
  width: 100% !important;
}}
.new-chat-btn button:hover {{ opacity: .9 !important; }}
.theme-btn button {{ background: transparent !important; border: 1px solid {T["pill_bd"]} !important; border-radius: 20px !important; color: {T["text"]} !important; font-size: 13px !important; padding: 4px 14px !important; width: auto !important; }}
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

# Render chat history nodes
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

staged_context_input = ""

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

# File uploader panel
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
                        staged_context_input += f"\n[PDF: {f.name}]:\n{txt[:5000]}"
                        st.success(f"Context Staged: {f.name}")
                    except: st.error("Could not parse PDF.")
            elif atype == "photo":
                f = st.file_uploader("Image", type=["png","jpg","jpeg"], key="fu_photo")
                if f:
                    st.image(f, width=200)
                    st.session_state.staged_context += f"\n[Image: {f.name}]"
                    st.success(f"Vision Asset Staged: {f.name}")
            elif atype == "code":
                f = st.file_uploader("Code / Data file",
                                     type=["txt","py","csv","json"], key="fu_code")
                if f:
                    try:
                        staged_context_input += (
                            f"\n[File: {f.name}]:\n{f.read().decode('utf-8')[:3000]}")
                        st.success(f"Source Code Staged: {f.name}")
                    except: st.error("Could not decode file.")

# ── 12. FLOATING CAPSULE BAR (COMPLETELY REPLACES BROKEN CHAT_INPUT) ──────────
st.markdown("<div class='chat-pill-outer'>", unsafe_allow_html=True)
with st.form("stable_chat_pill_form", clear_on_submit=True):
    c_plus, c_text, c_send = st.columns([0.4, 13.2, 0.4])
    
    with c_plus:
        st.markdown("<div class='plus-col-style'>", unsafe_allow_html=True)
        tray_label = "✖" if st.session_state.show_tray else "＋"
        plus_clicked = st.form_submit_button(tray_label)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with c_text:
        st.markdown("<div class='text-col-style'>", unsafe_allow_html=True)
        prompt_input = st.text_input("msg", placeholder="Ask Feemo AI anything...", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with c_send:
        st.markdown("<div class='send-col-style'>", unsafe_allow_html=True)
        send_clicked = st.form_submit_button("➤")
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── 13. INTERACTION EVALUATORS ────────────────────────────────────────────────
if plus_clicked:
    st.session_state.show_tray = not st.session_state.show_tray
    if not st.session_state.show_tray:
        st.session_state.active_upload_type = None
    st.rerun()

if send_clicked and prompt_input:
    full_payload = prompt_input
    if staged_context_input:
        full_payload = f"{prompt_input}\n\n{staged_context_input}"
        
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    save_chat_message("user", prompt_input)
    
    st.session_state["active_payload"] = full_payload
    st.session_state.show_tray = False
    st.session_state.active_upload_type = None
    st.session_state.staged_context = ""
    st.rerun()

# ── 14. AI RESPONSE INFERENCE ─────────────────────────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    ph = st.empty()
    ph.markdown(TYPING_HTML, unsafe_allow_html=True)
    
    current_prompt = st.session_state.get("active_payload", st.session_state.messages[-1]["content"])
    
    api_messages = []
    for m in st.session_state.messages[:-1]:
        api_messages.append({"role": m["role"], "content": m["content"]})
    api_messages.append({"role": "user", "content": current_prompt})
    
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": "Bearer " + st.secrets["GROQ_API_KEY"], "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"You are Feemo AI, a helpful assistant to {st.session_state.first_name}."}
                ] + api_messages,
                "max_tokens": 1000
            }
        ).json()
        
        if "choices" in res:
            reply = res["choices"][0]["message"]["content"]
            ph.empty()
            st.session_state.messages.append({"role": "assistant", "content": reply})
            save_chat_message("assistant", reply)
            if "active_payload" in st.session_state:
                del st.session_state["active_payload"]
            st.rerun()
        else:
            ph.empty()
            st.error("Inference structure failure.")
    except Exception as ex:
        ph.empty()
        st.error(f"API execution failure: {ex}")
