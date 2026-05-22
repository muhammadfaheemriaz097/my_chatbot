import streamlit as st
import PyPDF2
from supabase import create_client
from groq import Groq

# ── 1. DATABASE AND GROQ ENGINE INITIALIZATION ────────────────────────────────
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
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
<div class="ft"><span></span><span></span><span></span></div>
<style>
@keyframes fb{0%,80%,100%{transform:translateY(0);opacity:.4}40%{transform:translateY(-6px);opacity:1}}
.ft{display:flex;align-items:center;gap:5px;padding:12px 16px}
.ft span{width:8px;height:8px;border-radius:50%;background:#ff4b2b;display:inline-block;animation:fb 1.2s infinite ease-in-out}
.ft span:nth-child(2){animation-delay:.2s}.ft span:nth-child(3){animation-delay:.4s}
</style>
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

.gemini-tray {{ background:{T["pop_bg"]}; border:1px solid {T
