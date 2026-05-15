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
except:
    st.error("Secrets missing (SUPABASE_URL/KEY).")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(
    page_title="Feemo AI", 
    page_icon="✦", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 3. GEMINI-STYLE CSS (With ✦ Symbol Fix)
st.markdown("""
    <style>
    /* Clean UI */
    #MainMenu, footer {visibility: hidden !important;}
    .stApp { background-color: #0e0e10; color: #ececf1; }
    .block-container { max-width: 850px; padding-top: 2rem !important; margin: auto; }

    /* GEMINI MULTI-COLOR GRADIENT LOGO */
    .logo-container { 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        margin-bottom: 20px; 
        padding: 10px;
    }
    .logo-text {
        font-size: 55px; font-weight: 800; letter-spacing: -2px; margin: 0;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570, #f4af45);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .logo-symbol { 
        font-size: 45px; 
        margin-right: 15px; 
        color: #4285f4; 
        text-shadow: 0px 0px 15px rgba(66, 133, 244, 0.6); 
    }

    /* SIDEBAR THEME */
    section[data-testid="stSidebar"] { 
        background-color: #111111 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* TABS & FORMS */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stForm { border: 1px solid #2d2d2d !important; background-color: #171717; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. SESSION STATE
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_id" not in st.session_state: st.session_state.chat_id = None
if "login_error" not in st.session_state: st.session_state.login_error = None

# 5. SIDEBAR (Defined early for rendering)
with st.sidebar:
    st.markdown("<h2 style='color:#4285f4;'>✦ Feemo AI</h2>", unsafe_allow_html=True)
    if st.session_state.authenticated:
        st.write(f"👤 {st.session_state.get('first_name', 'Engineer')}")
        st.markdown("---")
        
        # History Logic
        try:
            hist = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(5).execute()
            for c in hist.data:
                if st.button(f"💬 {c['chat_title'][:20]}...", key=f"s_{c['id']}", use_container_width=True):
                    m_data = supabase.table("chat_history").select("full_history").eq("id", c['id']).execute()
                    st.session_state.messages = m_data.data[0]['full_history']
                    st.session_state.chat_id = c['id']
                    st.rerun()
        except: pass
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    else:
        st.info("Log in to unlock your workspace.")

# 6. LOGIN CALLBACK
def login_callback():
    try:
        res = supabase.auth.sign_in_with_password({"email": st.session_state.e_in, "password": st.session_state.p_in})
        if res.user:
            st.session_state.user_secret_id = res.user.id
            st.session_state.first_name = res.user.user_metadata.get("first_name", "User")
            st.session_state.authenticated = True
            st.session_state.login_error = None
        else: st.session_state.login_error = "Invalid credentials."
    except: st.session_state.login_error = "Auth connection error."

# 7. MAIN GATE
if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with t1:
        if st.session_state.login_error: st.error(st.session_state.login_error)
        with st.form("l_form"):
            st.text_input("Email", key="e_in")
            st.text_input("Password", type="password", key="p_in")
            st.form_submit_button("LOGIN", use_container_width=True, on_click=login_callback)
            
    with t2:
        with st.form("reg_form"):
            n_name = st.text_input("Name")
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pass, "options": {"data": {"first_name": n_name}}})
                    st.success("Check your email!")
                except: st.error("Signup failed.")

    with t3:
        with st.form("res_form"):
            r_email = st.text_input("Recovery Email")
            if st.form_submit_button("SEND RESET LINK", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(r_email)
                    st.success("Link sent!")
                except: st.error("Error.")
    st.stop()

# 8. LOGGED-IN WORKSPACE
else:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    with st.expander("📁 PDF Knowledge Base"):
        pdf_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
        pdf_text = ""
        if pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for i in range(min(len(reader.pages), 10)):
                extracted = reader.pages[i].extract_text()
                if extracted: pdf_text += extracted + "\n"
            st.success("Context Uploaded.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Ask Feemo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        try:
            headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
            sys_msg = f"You are Feemo AI. Professional helper to {st.session_state.first_name}, an ML & AI Engineer."
            if pdf_text: sys_msg += f"\n\nContext: {pdf_text[:7000]}"

            payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": sys_msg}] + st.session_state.messages}
            
            with st.chat_message("assistant"):
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
                reply = res["choices"][0]["message"]["content"]
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # Save History
            if st.session_state.chat_id is None:
                new_c = supabase.table("chat_history").insert({"chat_title": prompt[:25], "full_history": st.session_state.messages, "user_id": st.session_state.user_secret_id}).execute()
                st.session_state.chat_id = new_c.data[0]['id']
            else:
                supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.chat_id).execute()
        except: st.error("AI Engine Error.")
