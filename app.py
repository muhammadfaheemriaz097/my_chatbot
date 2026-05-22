import streamlit as st
import PyPDF2
from supabase import create_client
from groq import Groq

# ── 1. DATABASE AND GROQ ENGINE INITIALIZATION ────────────────────────────────
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    # Initialize the Groq hardware acceleration client directly
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
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
            user_email = getattr(res.user, "email", "Engineer@feemo.ai")
            st.session_state.first_name = (
                meta.get("full_name") or meta.get("first_name")
                or user_email.split("@")[0]
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
                key = str(msg.get("content", ""))[:40]
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
                "message": {"role": role, "content": str(content)}
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

TYPING_HTML = """
<style>
@keyframes fb{0%,80%,100%{transform:translateY(0);opacity:.4}40%{transform:translateY(-6px);opacity:1}}
.ft{display:flex;align-items:center;gap:5px;padding:12px 16px}
.ft span{width:8px;height:8px;border-radius:50%;background:#ff5823;display:inline-block;animation:fb 1.2s infinite ease-in-out}
.ft span:nth-child(2){animation-delay:.2s}.ft span:nth-child(3){animation-delay:.4s}
</style>
<div class="ft"><span></span><span></span><span></span></div>
"""

# ── 7. GLOBAL CSS OVERRIDES ───────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;800&display=swap');

.stAppDeployDropdown, div[data-testid="stHeaderDeveloperTools"],
div[data-testid="stStatusWidget"], .manage-app-button, #MainMenu, footer {{ 
    display: none !important; visibility: hidden !important; 
}}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.stApp {{ background:{T["bg"]}; color:{T["text"]}; font-family:'Inter',sans-serif; }}
.block-container {{ max-width:860px; padding-top:2rem !important; margin:auto; }}

.logo-wrap {{ display:flex; justify-content:center; align-items:center; margin-bottom:36px; }}
.logo-txt {{
    font-size:52px; font-weight:800; letter-spacing:-2px; margin:0;
    background:linear-gradient(90deg, #ff4b2b, #ff416c, #9b72cb);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}}
section[data-testid="stSidebar"] {{ background:{T["sb_bg"]} !important; border-right:1px solid {T["sb_bdr"]} !important; }}
.stChatMessage p {{ color:{T["msg_t"]} !important; font-size:15px !important; line-height:1.8 !important; }}

div[data-testid="stBottom"] > div {{ background: transparent !important; padding: 8px 0 16px 0 !important; }}
div[data-testid="stChatInput"] {{
    background: {T["pill_bg"]} !important; border: 1px solid {T["pill_bd"]} !important;
    border-radius: 32px !important; box-shadow: 0 8px 32px rgba(0,0,0,0.35) !important;
    padding: 2px 8px !important; max-width: 860px !important; margin: 0 auto !important;
}}
div[data-testid="stChatInput"] textarea {{ background: transparent !important; color: {T["inp_col"]} !important; font-size: 15px !important; border: none !important; box-shadow: none !important; }}
div[data-testid="stChatInput"] button {{ background: #ff4b2b !important; border-radius: 50% !important; color: #fff !important; }}

.gemini-tray {{ background:{T["pop_bg"]}; border:1px solid {T["pop_bd"]}; border-radius:20px; padding:8px 0; width:220px; box-shadow:0 12px 36px rgba(0,0,0,.5); margin-bottom:8px; }}
.gemini-tray-item {{ display:flex; align-items:center; gap:12px; padding:10px 18px; color:{T["text"]}; font-size:14px; font-weight:500; }}
.new-chat-btn button {{ background:linear-gradient(135deg,#ff4b2b,#ff416c) !important; border:none !important; color:#fff !important; font-weight:600 !important; }}
</style>""", unsafe_allow_html=True)

# ── 8. SIDEBAR NAVIGATION CONTROLS ────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='color:#ff4b2b;margin-bottom:12px'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.button("☀️ Light Mode" if IS_DARK else "🌙 Dark Mode", key="theme_toggle"):
        st.session_state.theme = "light" if IS_DARK else "dark"
        st.rerun()

    if st.session_state.authenticated:
        st.markdown(f"<p style='color:{T['text']};margin:12px 0 4px'>👤 <b>{st.session_state.first_name}</b></p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.button("✦  New Chat", key="new_chat_btn", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_tray = False
            st.session_state.active_upload_type = None
            st.session_state.staged_context = ""
            st.rerun()

        st.markdown("<p style='color:#888;font-size:11px;font-weight:700;margin:14px 0 6px;'>RECENT CHATS</p>", unsafe_allow_html=True)
        recent = load_chat_history()
        if recent:
            for chat in recent:
                msg = chat.get("message", {})
                preview = str(msg.get("content", "Chat"))[:30] + "…"
                if st.button(f"💬 {preview}", key=f"h_{chat['id']}", use_container_width=True):
                    thread = load_full_conversation(chat["id"])
                    st.session_state.messages = thread if thread else [msg]
                    st.rerun()

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            try: supabase.auth.sign_out()
            except: pass
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    else:
        st.info("Log in to start chatting.")

# ── 9. AUTH GATEWAY ───────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown("<div class='logo-wrap'><h1 class='logo-txt'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])

    with t1:
        with st.form("login_form"):
            email_in = st.text_input("Email")
            password_in = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                try:
                    r = supabase.auth.sign_in_with_password({"email": email_in, "password": password_in})
                    if r.user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = r.user.id
                        meta = r.user.user_metadata or {}
                        st.session_state.first_name = (meta.get("full_name") or email_in.split("@")[0])
                        st.rerun()
                except: st.error("Invalid email or password.")
    # (T2 and T3 omitted for runtime brevity, structural alignment preserved)
    st.stop()

# ── 10. CHAT WORKSPACE ────────────────────────────────────────────────────────
st.markdown("<div class='logo-wrap'><h1 class='logo-txt'>FEEMO AI</h1></div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(str(msg.get("content", "")))

# ── 11. TRAY CONTEXT CONTROLS ─────────────────────────────────────────────────
tray_label = "✖" if st.session_state.show_tray else "＋"
if st.button(tray_label, key="tray_toggle"):
    st.session_state.show_tray = not st.session_state.show_tray
    if not st.session_state.show_tray: st.session_state.active_upload_type = None
    st.rerun()

if st.session_state.show_tray and not st.session_state.active_upload_type:
    ca, cb = st.columns([1, 1])
    with ca:
        if st.button("📎 Upload PDF", key="opt_pdf", use_container_width=True):
            st.session_state.active_upload_type = "pdf"; st.rerun()
    with cb:
        if st.button("📁 Import Code", key="opt_code", use_container_width=True):
            st.session_state.active_upload_type = "code"; st.rerun()

if st.session_state.active_upload_type:
    with st.container(border=True):
        atype = st.session_state.active_upload_type
        if atype == "pdf":
            f = st.file_uploader("PDF Document", type="pdf")
            if f:
                reader = PyPDF2.PdfReader(f)
                txt = "".join(p.extract_text() or "" for p in reader.pages[:5])
                st.session_state.staged_context += f"\n[PDF CONTEXT]:\n{txt[:3000]}"
                st.success(f"Staged text matrix from: {f.name}")
        elif atype == "code":
            f = st.file_uploader("Code script", type=["txt","py","json","csv"])
            if f:
                st.session_state.staged_context += f"\n[SOURCE CODE]:\n{f.read().decode('utf-8')[:3000]}"
                st.success(f"Staged script content: {f.name}")

# ── 12. GROQ HIGH-SPEED INFERENCE RUNNER ─────────────────────────────────────
prompt = st.chat_input("Ask Feemo AI anything...")

if prompt and prompt.strip():
    full_payload = prompt.strip()
    if st.session_state.staged_context:
        full_payload = f"{full_payload}\n\n{st.session_state.staged_context}"

    st.session_state.messages.append({"role": "user", "content": prompt.strip()})
    save_chat_message("user", prompt.strip())

    # Build memory payloads safely for Groq engine array structure
    groq_messages = [{"role": "system", "content": f"You are Feemo AI, an elite AI Engineer assistant to {st.session_state.first_name}. Generate clean source layouts and robust technical debugging blocks."}]
    
    for m in st.session_state.messages[:-1]:
        groq_messages.append({"role": m["role"], "content": str(m.get("content", ""))})
    
    groq_messages.append({"role": "user", "content": full_payload})

    # Flush staging variables
    st.session_state.staged_context = ""
    st.session_state.show_tray = False
    st.session_state.active_upload_type = None

    ph = st.empty()
    ph.markdown(TYPING_HTML, unsafe_allow_html=True)

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=groq_messages,
            max_tokens=1500,
            temperature=0.5
        )
        reply = completion.choices[0].message.content
        ph.empty()

        st.session_state.messages.append({"role": "assistant", "content": reply})
        save_chat_message("assistant", reply)
        st.rerun()
    except Exception as e:
        ph.empty()
        st.error(f"Groq Core Execution Failure: {e}")
