import streamlit as st
import anthropic

st.set_page_config(page_title="Claude Chatbot", page_icon="🤖")
st.title("Claude Chatbot")

api_key = st.sidebar.text_input("Anthropic API Key", type="password")

if "messages" in st.session_state == False:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type a message..."):
    if not api_key:
        st.error("Please enter your API key in the sidebar")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

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
