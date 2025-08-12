import streamlit as st

st.title(":material/chat: Chat with MCP")
st.write("Interact with an LLM with access to the DIP MCP server.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input for user messages
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user", avatar=":material/face:"):
        st.markdown(prompt)
    
    # Generate echo response (simple bot that repeats the input)
    echo_response = f"Echo: {prompt}"
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": echo_response})
    
    # Display assistant response
    with st.chat_message("assistant", avatar=":material/robot:"):
        st.markdown(echo_response)