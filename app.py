import streamlit as st
import requests
import time
import datetime
import PyPDF2
import io
from supabase import create_client

# 1. DATABASE & SECRETS CHECK
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Missing Secrets: Please check your Streamlit Cloud secrets configuration.")
    st.stop()

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. ADVANCED CSS (Professional Branding)
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    
    button[kind="headerNoPadding"]::after { 
        content: '☰'; font-size: 26px; color: #c9a84c; visibility: visible !important; display: block;
    }
    button[kind="headerNoPadding"] {
        background-color: transparent !important; border-radius: 8px !important;
        margin-left: 15px !important; width: 45px !important; height: 45px !important;
    }
    .logo-container {
        display: flex; justify-content: center; align-items: center;
        padding: 40px 0; margin-top: -10px;
    }
    .logo-text {
        font-size: 60px; font-weight: 900; letter-spacing: -2px;
        background: linear-gradient(135deg, #c9a84c 0%, #ffffff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 5px 15px rgba(201, 168, 76, 0.3));
    }
    .logo-symbol { color: #c9a84c; font-size: 35px; margin-right: 12px; }
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #2d2d2d !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .block-container { max-width: 850px; padding-top: 1rem !important; }
    .stForm { border: 1px solid #2d2d2d !important; padding: 25px !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. AUTHENTICATION SYSTEM (State-Lock Logic)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

if not st.session_state.authenticated:
    st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)
    
    msg_zone = st.empty() 
    tab1, tab2, tab3 = st.tabs(["SIGN IN", "CREATE ACCOUNT", "FORGOT PASSWORD"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="name@email.com")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN TO WORKSPACE", use_container_width=True):
                try:
                    auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if auth_res.user:
                        st.session_state.user_secret_id = auth_res.user.id
                        st.session_state.first_name = auth_res.user.user_metadata.get("first_name", "User")
                        st.session_state.authenticated = True
                        msg_zone.success("Access Granted. Synchronizing...")
                        time.sleep(0.7)
                        st.rerun()
                        st.stop()
                    else:
                        msg_zone.error("Invalid email or password.")
                except:
                    msg_zone.error("Invalid email or password.")
    
    with tab2:
        with st.form("signup_form"):
            new_name = st.text_input("Full Name", placeholder="Faheem Riaz")
            new_email = st.text_input("Email", placeholder="name@email.com")
            new_pass = st.text_input("Create Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("REGISTER", use_container_width=True):
                if new_pass == confirm_pass and len(new_pass) >= 6:
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_pass, "options": {"data": {"first_name": new_name}}})
                        msg_zone.success("Verification link sent! Check your email inbox.")
                    except Exception as e:
                        if "already" in str(e).lower(): msg_zone.error("Email already exists.")
                        else: msg_zone.error(f"Error: {e}")
                else:
                    msg_zone.warning("Check password matching or length (min 6).")
    st.stop()

# 5. POST-LOGIN UI (Welcome Toast)
if not st.session_state.welcome_shown:
    st.toast(f"🚀 Welcome back, {st.session_state.first_name}!", icon="✨")
    st.session_state.welcome_shown = True

# 6. SIDEBAR & PDF KNOWLEDGE BASE
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c;'>Feemo AI</h2>", unsafe_allow_html=True)
    st.caption(f"👤 {st.session_state.first_name}")
    
    st.markdown("---")
    st.markdown("<div style='color:#c9a84c; font-size:12px; font-weight:bold; margin-bottom:10px;'>KNOWLEDGE BASE</div>", unsafe_allow_html=True)
    
    pdf_file = st.file_uploader("Upload PDF Study Material", type="pdf")
    pdf_text = ""
    
    if pdf_file:
        with st.spinner("Processing Knowledge..."):
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                # Extract first 15 pages to stay within Groq context window
                for i in range(min(len(pdf_reader.pages), 15)):
                    extracted = pdf_reader.pages[i].extract_text()
                    if extracted:
                        pdf_text += extracted + "\n"
                st.success("Knowledge Loaded!")
            except Exception as e:
                st.error(f"PDF Error: {str(e)}")

    st.markdown("---")
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    # Recent Chats History
    try:
        hist_res = supabase.table("chat_history").select("id, chat_title").eq("user_id", st.session_state.user_secret_id).order("created_at", desc=True).limit(10).execute()
        if hist_res.data:
            st.markdown("<div style='color:#666; font-size:11px; margin-top:20px;'>RECENT CHATS</div>", unsafe_allow_html=True)
            for chat in hist_res.data:
                if st.sidebar.button(f"💬 {chat['chat_title'][:25]}...", key=f"h_{chat['id']}", use_container_width=True):
                    msg_data = supabase.table("chat_history").select("full_history").eq("id", chat['id']).execute()
                    if msg_data.data:
                        st.session_state.messages = msg_data.data[0]['full_history']
                        st.session_state.current_chat_id = chat['id']
                        st.rerun()
    except:
        pass

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.welcome_shown = False
        st.rerun()

# 7. MAIN INTERFACE (Logo Only)
st.markdown("<div class='logo-container'><span class='logo-symbol'>✦</span><h1 class='logo-text'>FEEMO AI</h1></div>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. AI ENGINE (RAG Integration)
if prompt := st.chat_input("Ask about your PDF or type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Build System Prompt
        sys_prompt = f"You are Feemo AI, a highly intelligent professional assistant. The user's name is {st.session_state.first_name}, an ML & AI Engineer."
        if pdf_text:
            sys_prompt += f"\n\n[IMPORTANT] USE THE FOLLOWING PDF CONTENT AS YOUR PRIMARY KNOWLEDGE BASE:\n{pdf_text[:8000]}"
            sys_prompt += "\n\nAnswer based on this context. If not found, use general knowledge but prioritize the PDF."

        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": sys_prompt}] + st.session_state.messages
        }
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Persistence Logic
        if st.session_state.current_chat_id is None:
            new_c = supabase.table("chat_history").insert({
                "chat_title": prompt[:30], 
                "full_history": st.session_state.messages, 
                "user_id": st.session_state.user_secret_id
            }).execute()
            if new_c.data:
                st.session_state.current_chat_id = new_c.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.current_chat_id).execute()
    except Exception as e:
        st.error(f"AI Service Error: {str(e)}")
