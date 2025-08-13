import os
import requests
import streamlit as st

from fastmcp import FastMCP


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


mcp = FastMCP(
    name="DIP Parliamentary Data Server",
    instructions="""
    This server provides access to the German Bundestag's DIP (Dokumentations- und
    Informationssystem für Parlamentsmaterialien) API, which contains comprehensive
    data about parliamentary proceedings, members, and legislative documents.

    This MCP server also includes tools for basic arithmetic operations
    
    Current tools available:
    - add_numbers: Simple tool to add two integers together
    - subtract_numbers: Simple tool to subtract two integers
    - multiply_numbers: Simple tool to multiply two integers
    - divide_numbers: Simple tool to divide two integers
    - get_person: Retrieve parliament member information and biographical data
    - get_party_distribution: Get party distribution for a specific electoral period
    
    The system supports the current electoral period (21) and historical periods.
    """
)

# API key from st.secrets
DIP_API_KEY = get_api_key("DIP_API_KEY")


@mcp.tool(name="add_numbers", description="Adds two integer numbers together.")
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b


@mcp.tool(name="subtract_numbers", description="Subtracts two integer numbers together.")
def subtract(a: int, b: int) -> int:
    """Subtracts two integer numbers together."""
    return a - b


@mcp.tool(name="multiply_numbers", description="Multiplies two integer numbers together.")
def multiply(a: int, b: int) -> int:
    """Multiplies two integer numbers together."""
    return a * b


@mcp.tool(name="divide_numbers", description="Divides two integer numbers together.")
def divide(a: int, b: int) -> int:
    """Divides two integer numbers together."""
    return a / b


@mcp.tool(
    name="get_person",
    description="""
    Search for German parliamentary members with optional name, wahlperiode, and cursor parameters.
    """,
)
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
    if not DIP_API_KEY:
        raise RuntimeError("Missing API key: set DIP_API_KEY in st.secrets.")

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


@mcp.tool(
    name="get_party_distribution",
    description="""
    Get party distribution for a Wahlperiode. Fetches ALL parliamentary members and
    calculates precise party percentages.
    """,
)
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
        {
            "fraktion": "AfD", 
            "count": 148, 
            "percentage": 30.83,
            "members": ["Alice Weidel", "Alexander Gauland", ...]
        },
        {
            "fraktion": "BÜNDNIS 90/DIE GRÜNEN", 
            "count": 78, 
            "percentage": 16.25,
            "members": ["Annalena Baerbock", "Robert Habeck", ...]
        },
        {
            "fraktion": "SPD", 
            "count": 65, 
            "percentage": 13.54,
            "members": ["Olaf Scholz", "Lars Klingbeil", ...]
        }
    ]
    
    EXAMPLE USAGE:
    # Get current party distribution
    result = get_party_distribution(21)
    
    # Get historical party distribution  
    result = get_party_distribution(20)
    
    # Process results
    for party in result:
        print(f"{party['fraktion']}: {party['count']} members ({party['percentage']}%)")
        print(f"Members: {', '.join(party['members'][:5])}{'...' if len(party['members']) > 5 else ''}")
    """
    if not DIP_API_KEY:
        raise RuntimeError("Missing API key: set DIP_API_KEY in st.secrets.")

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
    
    # Calculate party distribution and collect member names
    party_data = {}
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
        
        # Initialize party data if not exists
        if party not in party_data:
            party_data[party] = {
                "count": 0,
                "members": []
            }
        
        # Increment count and add member name
        party_data[party]["count"] += 1
        
        # Get member name (handle both vorname/nachname and name fields)
        vorname = member.get('vorname', '').strip()
        nachname = member.get('nachname', '').strip()
        
        if vorname and nachname:
            member_name = f"{vorname} {nachname}"
        elif nachname:
            member_name = nachname
        elif vorname:
            member_name = vorname
        else:
            # Fallback to other name fields if available
            member_name = member.get('name', 'Unknown Name')
        
        party_data[party]["members"].append(member_name)
    
    # Calculate percentages and sort by count (descending)
    party_distribution = []
    for party, data in sorted(party_data.items(), key=lambda x: (-x[1]["count"], x[0])):
        percentage = round((data["count"] / total_members) * 100.0, 2) if total_members > 0 else 0.0
        party_distribution.append({
            "fraktion": party,
            "count": data["count"],
            "percentage": percentage,
            "members": sorted(data["members"])  # Sort member names alphabetically
        })
    
    return party_distribution


if __name__ == "__main__":
    mcp.run()