import os
import requests
import streamlit as st

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_api_key(key_name: str) -> str:
    """
    Get API key from st.secrets.
    
    Args:
        key_name: The name of the API key to retrieve
        
    Returns:
        The API key value
        
    Raises:
        RuntimeError: If the key is not found in st.secrets
    """
    try:
        return st.secrets[key_name]
    except (KeyError, AttributeError):
        raise RuntimeError(f"Missing API key: {key_name} not found in st.secrets")

st.title(":material/chat: Chat with MCP")
st.write("Interact with an LLM with access to the DIP MCP server.")

# Configure React agent
@st.cache_resource
def setup_chatbot():
    """Setup the LangGraph React agent with memory"""
    # Initialise Gemini model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=get_api_key("GOOGLE_API_KEY")
    )
    
    # Tools list
    @tool
    def add(a: int, b: int) -> int:
        """Adds two integer numbers together."""
        return a + b
    

    @tool
    def subtract(a: int, b: int) -> int:
        """Subtracts two integer numbers together."""
        return a - b
    
    @tool
    def multiply(a: int, b: int) -> int:
        """Multiplies two integer numbers together."""
        return a * b
    
    @tool
    def divide(a: int, b: int) -> int:
        """Divides two integer numbers together."""
        return a / b

    @tool
    def get_person(name: str = None, wahlperiode: int = None, cursor: str = None) -> dict:
        """
        Search for German parliamentary members from the DIP (Dokumentations- und Informationssystem für
        Parlamentsmaterialien) API.
        
        This function fetches persons from the DIP API with optional name, wahlperiode, and cursor filtering.
        Returns the raw API response containing person data from the German Bundestag database.
        
        PARAMETERS:
        - name (optional): Name to search for. Searches both first and last names.
                        Can be a single word (e.g., "Merkel") or full name in "Nachname Vorname" format
                        (e.g., "Steinmeier Frank Walter" for Frank-Walter Steinmeier).
                        If not provided, returns all persons.
        - wahlperiode (optional): Electoral period number to filter by (e.g., 21 for current period).
                                Selects only persons assigned to the specified electoral period.
                                Current period is 21, historical periods available from 1.
                                Note: 21 is the last available period - numbers above 21 are not allowed.
                                If not provided, returns persons from all periods.
        - cursor (optional): Pagination cursor for requesting additional results. Use the cursor value
                            from a previous response to get the next page of results. When the number
                            of found entities exceeds the limit, use this to load more entities.
                            Continue until the cursor stops changing to get all results.
                            If not provided, returns the first page of results.
        
        RESPONSE FORMAT:
        Returns a dictionary with:
        - numFound: Total number of matching persons
        - cursor: Pagination cursor for next page (use this for subsequent requests)
        - documents: Array of person objects with basic information
        
        EXAMPLE USAGE:
        # Get all persons
        result = get_person()
        
        # Search by last name
        result = get_person("Merkel")
        
        # Search by full name
        result = get_person("Steinmeier Frank Walter")
        
        # Get all current Bundestag members (period 21)
        result = get_person(wahlperiode=21)
        
        # Search for specific person in current period
        result = get_person("Merkel", wahlperiode=21)
        
        # Pagination example - get next page of results
        first_page = get_person(wahlperiode=21)
        if first_page['cursor']:
            next_page = get_person(wahlperiode=21, cursor=first_page['cursor'])
        
        # Process results
        print(f"Found {result['numFound']} persons")
        for person in result['documents']:
            print(f"{person['vorname']} {person['nachname']}")
        """

        # API key from st.secrets
        DIP_API_KEY = get_api_key("DIP_API_KEY")
        
        # Base URL
        BASE_URL = "https://search.dip.bundestag.de/api/v1"

        # Simple parameters - format, API key, and optional filters
        params = {
            "format": "json", 
            "apikey": DIP_API_KEY
        }
        
        # Add name filter if provided
        if name:
            params["f.person"] = [name]
        
        # Add wahlperiode filter if provided
        if wahlperiode:
            params["f.wahlperiode"] = [wahlperiode]
        
        # Add cursor for pagination if provided
        if cursor:
            params["cursor"] = cursor

        url = f"https://search.dip.bundestag.de/api/v1/person"
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    @tool
    def get_party_distribution(wahlperiode: int) -> list:
        """
        Get party distribution for parliamentary members in a specific Wahlperiode.
        
        This function automatically:
        - Fetches ALL parliamentary members from the specified electoral period
        - Handles pagination to retrieve every single member across all pages
        - Calculates accurate party distribution percentages
        
        PARAMETERS:
        - wahlperiode: Electoral period number to analyze (e.g., 21 for current period).
                    Current period is 21, historical periods available from 1.
                    Note: 21 is the last available period - numbers above 21 are not allowed.
        
        RESPONSE FORMAT:
        Returns a list of party statistics sorted by count (descending):
        [
            {"fraktion": "AfD", "count": 148, "percentage": 30.83},
            {"fraktion": "BÜNDNIS 90/DIE GRÜNEN", "count": 78, "percentage": 16.25},
            {"fraktion": "SPD", "count": 65, "percentage": 13.54}
        ]
        
        EXAMPLE USAGE:
        # Get current party distribution
        result = get_party_distribution(21)
        
        # Get historical party distribution  
        result = get_party_distribution(20)
        
        # Process results
        for party in result:
            print(f"{party['fraktion']}: {party['count']} members ({party['percentage']}%)")
        """

        # API key from st.secrets
        DIP_API_KEY = get_api_key("DIP_API_KEY")

        all_members = []
        cursor = None
        pages_fetched = 0
        
        # Fetch all pages until no more data
        while True:
            params = {
                "format": "json", 
                "apikey": DIP_API_KEY,
                "f.wahlperiode": [wahlperiode]
            }
            if cursor:
                params["cursor"] = cursor
                
            url = f"https://search.dip.bundestag.de/api/v1/person"
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            # Add members from this page
            documents = data.get('documents', [])
            all_members.extend(documents)
            pages_fetched += 1
            
            # Check if we need to continue
            new_cursor = data.get('cursor')
            if not new_cursor or new_cursor == cursor:
                break
            cursor = new_cursor
            
            # Safety check to prevent infinite loops
            if pages_fetched > 100:  # Reasonable safety limit
                break
        
        # Calculate party distribution
        party_counts = {}
        total_members = len(all_members)
        
        for member in all_members:
            # Get party affiliation - handle both direct and role-based
            party = None
            
            # First check direct fraktion field
            fraktion = member.get('fraktion', [])
            if isinstance(fraktion, list) and fraktion:
                party = fraktion[0]  # Take first party if multiple
            elif isinstance(fraktion, str):
                party = fraktion
                
            # If no direct party, check person_roles for this Wahlperiode
            if not party:
                roles = member.get('person_roles', []) or []
                for role in roles:
                    role_periods = role.get('wahlperiode_nummer', []) or []
                    if wahlperiode in role_periods:
                        role_party = role.get('fraktion')
                        if role_party:
                            party = role_party
                            break
            
            # Default to "Unbekannt" if no party found
            if not party:
                party = "Unbekannt"
                
            party_counts[party] = party_counts.get(party, 0) + 1
        
        # Calculate percentages and sort by count (descending)
        party_distribution = []
        for party, count in sorted(party_counts.items(), key=lambda x: (-x[1], x[0])):
            percentage = round((count / total_members) * 100.0, 2) if total_members > 0 else 0.0
            party_distribution.append({
                "fraktion": party,
                "count": count,
                "percentage": percentage
            })
        
        return party_distribution

    tools = [add, subtract, multiply, divide, get_person, get_party_distribution]
    
    # System message
    system_message = """You are a helpful AI assistant. You can have natural conversations with users 
    and remember the context of your previous interactions. Be friendly, informative, and helpful.
    
    You have acess to the following tools:
    - add: Adds two integer numbers together.
    - subtract: Subtracts two integer numbers together.
    - get_person: Search for German parliamentary members from the DIP
    (Dokumentations- und Informationssystem für Parlamentsmaterialien) API.
    - get_party_distribution: Get party distribution for a specific electoral period.
    """
    
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