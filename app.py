import streamlit as st

# This page is the entry point for the app.
# Set page config
st.set_page_config(
    page_title="DIP MCP Server",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Define pages
pages = {
    "Apps": [
        st.Page(
            page="src/frontend/parliment_analysis.py", 
            title="Parliamentary Data", 
            default=True, 
            icon=":material/how_to_vote:"
        ),
        st.Page(
            page="src/frontend/chat_with_mcp.py", 
            title="Chat with MCP", icon=":material/chat:"),
    ],
}

# Run the app
pg = st.navigation(pages)
pg.run()