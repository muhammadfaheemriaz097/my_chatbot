import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Feemo AI", page_icon="🤖")
st.title("🤖 Feemo AI")
st.caption("Powered by Google Gemini — Your Smart AI Assistant")

api_key = st.sidebar.text_input("Feemo AI API Key", type="password", placeholder="AIza...")
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
        st.error("Please enter your Gemini API key in the left sidebar")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")

            history = []
            for msg in st.session_state.messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

            chat = model.start_chat(history=history)

            with st.chat_message("assistant"):
                with st.spinner("Feemo AI is thinking..."):
                    response = chat.send_message(prompt)
                    reply = response.text
                    st.markdown(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            st.error(f"Error: {str(e)}")
