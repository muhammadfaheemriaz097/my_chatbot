import streamlit as st
import PyPDF2
from supabase import create_client
from google import genai
from google.genai import types

# ── 1. FIXED HARDCODED EMERGENY STACK ─────────────────────────────────────────
try:
    SUPABASE_URL = "https://iqdhubrimiiodvliuhns.supabase.co"
    SUPABASE_KEY = "sb_secret_dV1Uxnc3kf5wfIqiNfvFMA_kFuaHDCW"
    GEMINI_API_KEY = "AIzaSyAhrK12HsRFLyKQ5fbr7_TgpAqeTVgwbMs"
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Initialization Error: {e}")
    st.stop()

# ── 2. PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Feemo AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

# ── 3. SESSION STATE ──────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "first_name" not in st.session_state:
    st.session_state.first_name = "Engineer"
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "show_tray" not in st.session_state:
    st.session_state.show_tray = False
if "active_upload_type" not in st.session_state:
    st.session_state.active_upload_type = None
if "staged_context" not in st.session_state:
    st.session_state.staged_context = ""
if "staged_image_bytes" not in st.session_state:
    st.session_state.staged_image_bytes = None
if "staged_image_mime" not in st.session_state:
    st.session_state.staged_image_mime = ""

# ── 4. GLOBAL CSS OVERRIDES ───────────────────────────────────────────────────
st.markdown("""<style>
.stAppDeployDropdown, div[data-testid="stHeaderDeveloperTools"], 
div[data-testid="stStatusWidget"], .manage-app-button, #MainMenu, footer { 
    display: none !important; visibility: hidden !important; 
}
.stApp { background: #0e0e10; color: #ececf1; font-family: 'Inter', sans-serif; }
.logo-wrap { display:flex; justify-content:center; align-items:center; margin-bottom:36px; }
.logo-txt {
    font-size:52px; font-weight:800; letter-spacing:-2px;
    background:linear-gradient(90deg,#4285f4,#9b72cb,#d96570,#f4af45);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
</style>""", unsafe_allow_html=True)

# ── 5. AUTH GATEWAY ──────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown("<div class='logo-wrap'><h1 class='logo-txt'>✦ FEEMO AI</h1></div>", unsafe_allow_html=True)
    with st.form("login_form"):
        email_in = st.text_input("Email")
        password_in = st.text_input("Password", type="password")
        if st.form_submit_button("LOGIN", use_container_width=True):
            try:
                r = supabase.auth.sign_in_with_password({"email": email_in, "password": password_in})
                if r.user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = r.user.id
                    st.session_state.first_name = email_in.split("@")[0]
                    st.rerun()
            except:
                st.error("Invalid email or password.")
    st.stop()

# ── 6. WORKSPACE MAIN PANEL ───────────────────────────────────────────────────
st.markdown("<div class='logo-wrap'><h1 class='logo-txt'>✦ FEEMO AI</h1></div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(str(msg.get("content", "")))

# ── 7. ATTACHMENT HANDLING FRAME ──────────────────────────────────────────────
if st.button("＋ Attach Media Context"):
    st.session_state.show_tray = not st.session_state.show_tray

if st.session_state.show_tray:
    f = st.file_uploader("Upload Image or document asset", type=["png","jpg","jpeg","pdf"])
    if f:
        if f.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            st.session_state.staged_image_bytes = f.getvalue()
            st.session_state.staged_image_mime = f.type
            st.success(f"Visual target context locked: {f.name}")
        elif f.name.lower().endswith('.pdf'):
            try:
                reader = PyPDF2.PdfReader(f)
                txt = "".join(p.extract_text() or "" for p in reader.pages[:5])
                st.session_state.staged_context += f"\n[DOCUMENT EXTRACT]:\n{txt[:2000]}"
                st.success(f"PDF structure parsed: {f.name}")
            except:
                st.error("Error reading PDF.")

# ── 8. INFERENCE ROUTER ───────────────────────────────────────────────────────
prompt = st.chat_input("Ask Feemo AI anything...")

if prompt and prompt.strip():
    st.session_state.messages.append({"role": "user", "content": prompt.strip()})
    
    current_parts = []
    if st.session_state.staged_image_bytes:
        current_parts.append(types.Part.from_bytes(data=st.session_state.staged_image_bytes, mime_type=st.session_state.staged_image_mime))
    
    payload_text = prompt.strip()
    if st.session_state.staged_context:
        payload_text = f"{payload_text}\n\n{st.session_state.staged_context}"
        
    current_parts.append(types.Part.from_text(text=payload_text))
    
    # Flush temporal variables instantly
    st.session_state.staged_image_bytes = None
    st.session_state.staged_context = ""
    st.session_state.show_tray = False
    
    with st.spinner("Analyzing context engine..."):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[types.Content(role="user", parts=current_parts)],
                config=types.GenerateContentConfig(
                    system_instruction=f"You are Feemo AI, a brilliant multi-modal assistant to {st.session_state.first_name}. Process visual and structural data layouts completely.",
                    max_output_tokens=1000
                )
            )
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Inference error: {e}")
    st.rerun()
