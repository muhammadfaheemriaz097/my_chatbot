import streamlit as st
import requests
import time

st.set_page_config(page_title="Feemo AI", page_icon="🤖", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #0a0a0a; color: #f5f5f5; }
.stChatInput input { background-color: #1a1a1a !important; color: #f5f5f5 !important; border: 1px solid #c9a84c !important; border-radius: 12px !important; }
.stChatMessage { background-color: #111111 !important; border-radius: 12px !important; padding: 10px !important; }
section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #c9a84c !important; }
h1 { color: #c9a84c !important; font-family: Georgia, serif !important; letter-spacing: 2px !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #c9a84c; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style='text-align:center;padding:20px 0;'>
<div style='width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,#c9a84c,#8b6914);margin:0 auto 12px auto;display:flex;align-items:center;justify-content:center;font-size:36px;'>🤖</div>
<h2 style='color:#c9a84c;margin:0;'>Feemo AI</h2>
<p style='color:#8b6914;font-size:12px;'>Your Smart AI Assistant</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>👤 Created by</p>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#f5f5f5;font-size:15px;font-weight:bold;'>Muhammad Faheem Riaz</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='color:#c9a84c;font-weight:bold;'>💡 You can ask me about</p>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#aaa;font-size:12px;'>✦ General knowledge<br>✦ Writing and emails<br>✦ Coding help<br>✦ Study and learning<br>✦ Business ideas<br>✦ Anything else!</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

st.markdown("""
<div style='text-align:center;padding:10px 0 20px 0;'>
<h1 style='color:#c9a84c;font-size:42px;letter-spacing:3px;'>✦ FEEMO AI ✦</h1>
<p style='color:#8b6914;font-size:14px;'>Powered by Groq AI — Fast and Intelligent</p>
<hr style='border-color:#c9a84c;opacity:0.3;'>
</div>
""", unsafe_allow_html=True)

API_KEY = st.secrets["GROQ_API_KEY"]

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    st.markdown("""
<div style='text-align:center;padding:40px 20px;'>
<p style='font-size:40px;'>✦</p>
<p style='color:#c9a84c;font-size:18px;font-weight:bold;'>Welcome to Feemo AI</p>
<p style='color:#666;font-size:14px;'>Ask me anything — I am here to help you 24/7</p>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("✦ Ask Feemo AI anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        headers = {
            "Authorization": "Bearer " + API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": st.session_state.messages,
            "max_tokens": 1000
        }

        with st.chat_message("assistant"):
            with st.spinner("✦ Feemo AI is thinking..."):
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                result = response.json()

                if "choices" in result:
                    reply = result["choices"][0]["message"]["content"]
                    placeholder = st.empty()
                    typed = ""
                    for char in reply:
                        typed += char
                        placeholder.markdown(
                           "<p style='color:#c9a84c;font-size:15px;line-height:1.7;'>" + typed + "▌</p>",
                             unsafe_allow_html=True
                      )
                      time.sleep(0.008)
                 placeholder.markdown(
                           "<p style='color:#f5f5f5;font-size:15px;line-height:1.7;'>" + reply + "</p>",
                           unsafe_allow_html=True
                  )
                        time.sleep(0.008)
                    placeholder.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                elif "error" in result:
                    st.error("Error: " + result["error"]["message"])
                    st.session_state.messages.pop()
                else:
                    st.error("Unexpected response from API")
                    st.session_state.messages.pop()

    except Exception as e:
        st.error("Error: " + str(e))
        st.session_state.messages.pop()
