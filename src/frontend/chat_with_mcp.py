import os
import streamlit as st

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.title(":material/chat: Chat with MCP")
st.write("Interact with an LLM with access to the DIP MCP server.")

# Configure React agent
@st.cache_resource
def setup_chatbot():
    """Setup the LangGraph React agent with memory"""
    # Initialise Gemini model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")  # Make sure to set this in your .env
    )
    
    # Tools list (empty for now, will add MCP tools later)
    tools = []
    
    # System message
    system_message = """You are a helpful AI assistant. You can have natural conversations with users 
    and remember the context of your previous interactions. Be friendly, informative, and helpful."""
    
    # Add memory
    memory = MemorySaver()
    
    # Create React agent with memory
    agent = create_react_agent(
        llm, 
        tools, 
        prompt=SystemMessage(content=system_message),
        checkpointer=memory
    )
    
    return agent

# Initialize the chatbot
try:
    chatbot = setup_chatbot()
except Exception as e:
    st.error(f"Failed to initialize chatbot: {str(e)}")
    st.stop()

# Initialise session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(
        message["role"], avatar=":material/face:" if message["role"] == "user" else ":material/robot:"
        ):
        st.markdown(message["content"])

# Chat input for user messages
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user", avatar=":material/face:"):
        st.markdown(prompt)
    
    # Generate response using LangGraph agent
    with st.chat_message("assistant", avatar=":material/robot:"):
        with st.spinner("Thinking..."):
            try:
                # Configure thread for memory (using fixed thread ID)
                config = {"configurable": {"thread_id": "conversation"}}
                
                # Create message for LangGraph
                messages = [HumanMessage(content=prompt)]
                
                # Invoke the chatbot
                response = chatbot.invoke({"messages": messages}, config)
                
                # Extract the assistant's response
                assistant_message = response["messages"][-1].content
                
                # Display and store the response
                st.markdown(assistant_message)
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})