import streamlit as st
from groq import Groq

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
            client = Groq(api_key=api_key)

            with st.chat_message("assistant"):
                with st.spinner("Feemo AI is thinking..."):
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=st.session_state.messages,
                        max_tokens=1000
                    )
                    reply = response.choices[0].message.content
                    st.markdown(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"Error: {str(e)}")
