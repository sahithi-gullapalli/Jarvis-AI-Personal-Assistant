"""Optional Streamlit chat dashboard. Run: streamlit run dashboard.py"""
import streamlit as st
import jarvis_brain

st.set_page_config(page_title="Jarvis Assistant", page_icon="🤖", layout="centered")
st.title("Jarvis AI Personal Assistant")
st.caption("Local desktop assistant · Groq AI · Optional semantic memory")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Ask Jarvis something...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Jarvis is thinking..."):
            try:
                answer = jarvis_brain.think(query)
            except Exception:
                answer = "Jarvis hit an error. Check the terminal logs and configuration."
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

with st.sidebar:
    st.subheader("Local memory")
    st.write("Semantic memory is optional and stored on this computer.")
    if st.button("Clear Jarvis memory"):
        try:
            from jarvis_memory import clear_memory
            if clear_memory():
                st.success("Memory collection cleared.")
            else:
                st.error("Could not clear memory.")
        except Exception:
            st.error("Install the optional memory dependencies first.")
