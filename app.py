import streamlit as st
import requests

st.set_page_config(page_title="Feemo AI", page_icon="🤖")
st.title("🤖 Feemo AI")
st.caption("Powered by Groq AI — Your Smart AI Assistant")

api_key = st.sidebar.text_input("Feemo AI API Key", type="password", placeholder="gsk_...")
st.sidebar.markdown("---")
st.sidebar.markdown("### About Feemo AI")
st.sidebar.markdown("Feemo AI is your personal AI assistant. Ask anything and get instant answers.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask Feemo AI anything..."):
    if not api_key:
        st.error("Please enter your Groq API key in the left sidebar")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": st.session_state.messages,
                "max_tokens": 1000
            }

            with st.chat_message("assistant"):
                with st.spinner("Feemo AI is thinking..."):
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=data
                    )
                    result = response.json()

                    if "choices" in result:
                        reply = result["choices"][0]["message"]["content"]
                        st.markdown(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                    elif "error" in result:
                        st.error(f"Groq Error: {result['error']['message']}")
                        st.session_state.messages.pop()
                    else:
                        st.error(f"Unexpected response: {result}")
                        st.session_state.messages.pop()

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.messages.pop()
