import streamlit as st
import requests
import time
import datetime
import uuid
from supabase import create_client

# 1. INITIALIZE DATABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIG
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. PERSISTENT IDENTITY LOGIC (URL-based for Refresh Stability)
# To keep your ID across refreshes, we will use a URL parameter.
# If you want to keep your history, always use the URL with your ID.
query_params = st.query_params
if "id" not in query_params:
    # Create a new ID only if one doesn't exist in the URL
    new_id = str(uuid.uuid4())[:8]
    st.query_params["id"] = new_id
    user_id = new_id
else:
    user_id = query_params["id"]

# Store in session state for the code to use
st.session_state.user_secret_id = user_id

# 4. DATA SYNC (Filtered by User ID)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

try:
    # Fetch history ONLY for this specific user_id
    hist_res = supabase.table("chat_history")\
        .select("id, chat_title")\
        .eq("user_id", st.session_state.user_secret_id)\
        .order("created_at", desc=True)\
        .limit(10).execute()
    recent_activity = hist_res.data if hist_res.data else []
except Exception as e:
    recent_activity = []

# 5. CSS (ChatGPT Style)
st.markdown("""
    <style>
    #MainMenu, footer, .stAppToolbar {visibility: hidden;}
    button[kind="headerNoPadding"]::after { content: '☰'; font-size: 26px; color: #c9a84c; visibility: visible !important; display: block; }
    button[kind="headerNoPadding"] { background-color: transparent !important; border: 1px solid rgba(201,168,76,0.2) !important; border-radius: 8px !important; margin-left: 15px !important; width: 45px !important; height: 45px !important; }
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #2d2d2d !important; }
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 25px 0 10px 10px; }
    div[data-testid="stSidebar"] button { background-color: transparent !important; color: #d1d1d1 !important; border: none !important; text-align: left !important; display: block !important; width: 100% !important; padding: 10px 15px !important; }
    div[data-testid="stSidebar"] button:hover { background-color: #1a1a1a !important; color: #ffffff !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }
    .block-container { max-width: 850px; padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# 6. SIDEBAR
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c; margin-left:10px;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.markdown("<div class='history-label'>MY RECENT ACTIVITY</div>", unsafe_allow_html=True)
    
    for chat in recent_activity:
        if st.sidebar.button(f"💬 {chat['chat_title'][:25]}...", key=f"btn_{chat['id']}", use_container_width=True):
            msg_res = supabase.table("chat_history").select("full_history").eq("id", chat['id']).execute()
            if msg_res.data:
                st.session_state.messages = msg_res.data[0]['full_history']
                st.session_state.current_chat_id = chat['id']
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Your Secret Link ID: {st.session_state.user_secret_id}")
    st.sidebar.info("Bookmark this URL to keep your history private and persistent!")

# 7. MAIN CHAT AREA
st.markdown("<div style='text-align:center;'><h1>✦ FEEMO AI ✦</h1></div>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 8. AI LOGIC & SAVING
if prompt := st.chat_input("Message Feemo AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        now = datetime.datetime.now().strftime("%B %d, %Y")
        headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": "You are Feemo AI."}] + st.session_state.messages}
        
        with st.chat_message("assistant"):
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
            reply = res["choices"][0]["message"]["content"]
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # SAVE WITH THE PERSISTENT USER_ID
        if st.session_state.current_chat_id is None:
            new_chat = supabase.table("chat_history").insert({
                "chat_title": prompt[:30],
                "full_history": st.session_state.messages,
                "user_id": st.session_state.user_secret_id 
            }).execute()
            st.session_state.current_chat_id = new_chat.data[0]['id']
        else:
            supabase.table("chat_history").update({"full_history": st.session_state.messages}).eq("id", st.session_state.current_chat_id).execute()
            
    except:
        st.error("Error.")
