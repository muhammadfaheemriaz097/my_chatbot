import streamlit as st
import anthropic

st.set_page_config(page_title="Feemo AI", page_icon="🤖")
st.title("🤖 Feemo AI")

api_key = st.sidebar.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type a message..."):
    if not api_key:
        st.error("Please enter your Anthropic API key in the left sidebar")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            client = anthropic.Anthropic(api_key=api_key)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        messages=st.session_state.messages
                    )
                    reply = response.content[0].text
                    st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"Error: {str(e)}")
