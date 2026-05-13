import streamlit as st
import requests
import time
import datetime
from supabase import create_client

# 1. INITIALIZE DATABASE
# Ensure SUPABASE_URL, SUPABASE_KEY, and GROQ_API_KEY are in Streamlit Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. APP CONFIGURATION
st.set_page_config(page_title="Feemo AI", page_icon="✨", layout="wide")

# 3. SILENT DATA SYNC (Load Memory & Recent Activity)
if "bot_memory" not in st.session_state:
    try:
        # Load long-term context from user_memory table
        mem_res = supabase.table("user_memory").select("memory_context").eq("id", 1).execute()
        st.session_state.bot_memory = mem_res.data[0]['memory_context'] if mem_res.data else ""
        
        # Load existing history from chat_history table
        hist_res = supabase.table("chat_history").select("chat_title").order("created_at", desc=True).limit(10).execute()
        st.session_state.recent_activity = [row['chat_title'] for row in hist_res.data] if hist_res.data else []
    except Exception:
        st.session_state.bot_memory = ""
        st.session_state.recent_activity = []

# 4. CHATGPT-STYLE CSS (Hamburger Menu & Clean UI)
st.markdown("""
    <style>
    /* UI Clean-up */
    #MainMenu, footer, .stAppToolbar {visibility: hidden;}
    
    /* REPLACE ARROW WITH THREE LINES (HAMBURGER MENU) */
    button[kind="headerNoPadding"] svg { display: none; }
    button[kind="headerNoPadding"]::after { 
        content: '☰'; 
        font-size: 26px; 
        color: #c9a84c; 
        visibility: visible !important; 
        display: block;
    }
    button[kind="headerNoPadding"] {
        background-color: transparent !important;
        border: 1px solid rgba(201, 168, 76, 0.2) !important;
        border-radius: 8px !important;
        margin-left: 15px !important;
        width: 45px !important;
        height: 45px !important;
    }

    /* DARK THEME & CHATGPT-STYLE LAYOUT */
    .stApp { background-color: #0d0d0d; color: #ececf1; }
    section[data-testid="stSidebar"] { 
        background-color: #000000 !important; 
        border-right: 1px solid #2d2d2d !important; 
    }
    
    /* RECENT ACTIVITY STYLE */
    .history-label { color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin: 25px 10px 10px 10px; }
    .history-item {
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-size: 14px;
        color: #d1d1d1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: 0.2s;
    }
    .history-item:hover { background-color: #1a1a1a; cursor: default; }

    /* MESSAGE BUBBLES */
    [data-testid="stChatMessage"] { border: none !important; padding: 2rem 1rem !important; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #1a1a1a !important; }

    /* CENTERED CHAT BOX */
    .block-container { max-width: 850px; padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# 5. SIDEBAR (History List)
with st.sidebar:
    st.markdown("<h2 style='color:#c9a84c; margin-left:10px;'>Feemo AI</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<div class='history-label'>RECENT ACTIVITY</div>", unsafe_allow_html=True)
    
    # Display the History
    if st.session_state.recent_activity:
        for activity in st.session_state.recent_activity:
            st.markdown(f"<div class='history-item'>💬 {activity}</div>", unsafe_allow_html=True)
    else:
        st.sidebar.caption("No recent activity.")

    # Developer Signature
    st.sidebar.markdown(f"""
        <div style='position: fixed; bottom: 20px; width: 220px; font-size:11px;
