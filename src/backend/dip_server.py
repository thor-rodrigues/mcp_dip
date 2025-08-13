import os
import requests
from typing import Optional, List, Literal, Union, Annotated

from fastmcp import FastMCP
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


mcp = FastMCP(
    name="DIP Parliamentary Data Server",
    instructions="""
    This server provides access to the German Bundestag's DIP (Dokumentations- und Informationssystem) API,
    which contains comprehensive data about parliamentary proceedings, members, and legislative documents.
    
    Current tools available:
    - add_numbers: Simple tool to add two integers together (for testing)
    - subtract_numbers: Simple tool to subtract two integers (for testing)
    - get_person: Retrieve parliament member information and biographical data
    - get_party_distribution: Get party distribution for a specific electoral period
    
    For analysing party distribution in the German parliament, use get_person with wahlperiode filters.
    The system supports the current electoral period (21) and historical periods.
    
    All data comes from the official Bundestag database and is updated regularly.
    """
)

# Base URL per official OpenAPI
BASE_URL = "https://search.dip.bundestag.de/api/v1"

# API key from environment
DIP_API_KEY = os.getenv("DIP_API_KEY")


@mcp.tool(
    name="add_numbers",
    description="Adds two integer numbers together.",
    tags={"math", "basic"},
)
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b


@mcp.tool(
    name="subtract_numbers", 
    description="Subtracts two integer numbers together.",
    tags={"math", "basic"},
)
def subtract(a: int, b: int) -> int:
    """Subtracts two integer numbers together."""
    return a - b


@mcp.tool(
    name="get_person",
    description="Call DIP GET /person with optional filters; returns raw API response.",
    tags={"DIP", "person"},
)
def get_person(
    # Filters (map to DIP parameters)
    person: Annotated[Optional[List[str]], Field(
        description="Name search terms for a person. Searches both first name and last name. "
                   "Can be repeated to search multiple names (OR search). "
                   "Single word search for complete name parts possible. "
                   "Multiple search terms are searched as phrase in order 'Nachname Vorname'. "
                   "Example: ['Steinmeier Frank Walter']"
    )] = None,
    
    id: Annotated[Optional[List[int]], Field(
        description="Entity IDs to select. Can be repeated to select multiple entities. "
                   "Use for direct lookup of specific persons by their DIP database ID."
    )] = None,
    
    wahlperiode: Annotated[Optional[List[int]], Field(
        description="Electoral period numbers (Wahlperioden). Selects all entities assigned to the specified "
                   "electoral period. Can be repeated to select multiple periods (OR search). "
                   "Current period is 21, historical periods available from 1. "
                   "Example: [20, 21] for periods 20 and 21"
    )] = None,
    
    aktualisiert_start: Annotated[Optional[str], Field(
        description="Earliest update date of the entity. Selects entities in a date range "
                   "based on the last update date. ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
                   "Examples: '2022-12-06T10:00:00' or '2022-12-06T10:00:00+02:00' with timezone"
    )] = None,
    
    aktualisiert_end: Annotated[Optional[str], Field(
        description="Latest update date of the entity. Selects entities in a date range "
                   "based on the last update date. ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
                   "Examples: '2022-12-06T20:00:00' or '2022-12-06T20:00:00+02:00' with timezone"
    )] = None,
    
    datum_start: Annotated[Optional[str], Field(
        description="Earliest document date. Selects entities in a date range based on document date. "
                   "For persons, the date range of all associated documents is used. "
                   "Format: YYYY-MM-DD. Example: '2021-01-11'"
    )] = None,
    
    datum_end: Annotated[Optional[str], Field(
        description="Latest document date. Selects entities in a date range based on document date. "
                   "For persons, the date range of all associated documents is used. "
                   "Format: YYYY-MM-DD. Example: '2021-01-15'"
    )] = None,

    # Institutional filtering
    zuordnung: Annotated[Optional[Literal["BT", "BR", "BV", "EK"]], Field(
        description="Institution assignment filter. BT=Bundestag, BR=Bundesrat, BV=Bundesversammlung, EK=Europakammer. "
                   "For party distribution analysis of the German Parliament, use 'BT' to get only Bundestag members."
    )] = None,

    # Pagination and format
    cursor: Annotated[Optional[str], Field(
        description="Cursor position for requesting additional entities. If the number of found entities "
                   "exceeds the limit, a follow-up request must be made to load more entities. "
                   "Use the cursor value from the previous response. Continue until cursor stops changing."
    )] = None,
    
    format: Annotated[Literal["json", "xml"], Field(
        description="Controls the data format of the response. JSON (default) or XML available."
    )] = "json",
) -> Union[dict, str]:
    """
    Retrieve German parliamentary member data from the DIP (Dokumentations- und Informationssystem) API.
    
    This tool accesses the official German Bundestag database containing information about 
    parliament members (MdB = Mitglied des Bundestages), including their names, party affiliations,
    electoral periods, and biographical data.
    
    USE CASES:
    - Find parliament members by name or party affiliation
    - Get member lists for specific electoral periods (Wahlperioden)
    - Analyse party composition and distribution
    - Research parliamentary member biographical information
    
    PARAMETERS:
    - person: List of name search terms (searches both first and last names)
    - id: List of specific person IDs for direct lookup
    - wahlperiode: List of electoral periods (e.g., [20, 21] for periods 20 and 21)
    - zuordnung: Institution filter ('BT'=Bundestag, 'BR'=Bundesrat, 'BV'=Bundesversammlung, 'EK'=Europakammer)
    - aktualisiert_start/end: Filter by last update date (ISO 8601 format)
    - datum_start/end: Filter by document dates (YYYY-MM-DD format)
    - cursor: For pagination - use the cursor from previous response to get next page
    - format: Response format ('json' recommended, 'xml' also available)
    
    RESPONSE FORMAT:
    Returns a dictionary with:
    - numFound: Total number of matching persons
    - cursor: Pagination cursor for next page
    - documents: Array of person objects with fields like:
      * id, nachname, vorname, titel (name information)
      * fraktion, funktion (party and role information) 
      * wahlperiode (electoral periods served)
      * person_roles (detailed role history)
    
    EXAMPLES:
    - Get all current Bundestag members: get_person(wahlperiode=[21], zuordnung="BT")
    - Get all current Bundesrat members: get_person(wahlperiode=[21], zuordnung="BR")
    - Search by name: get_person(person=["Merkel"])
    - Get specific person: get_person(id=[123])
    """
    if not DIP_API_KEY:
        raise RuntimeError("Missing API key: set DIP_API_KEY in the environment or .env file.")

    params: dict = {"format": format, "apikey": DIP_API_KEY}
    if person:
        params["f.person"] = person
    if id:
        params["f.id"] = id
    if wahlperiode:
        params["f.wahlperiode"] = wahlperiode
    if aktualisiert_start:
        params["f.aktualisiert.start"] = aktualisiert_start
    if aktualisiert_end:
        params["f.aktualisiert.end"] = aktualisiert_end
    if datum_start:
        params["f.datum.start"] = datum_start
    if datum_end:
        params["f.datum.end"] = datum_end
    if zuordnung:
        params["f.zuordnung"] = zuordnung
    if cursor:
        params["cursor"] = cursor

    url = f"{BASE_URL}/person"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json() if format == "json" else resp.text


@mcp.tool(
    name="get_party_distribution",
    description="Get party distribution for a Wahlperiode. Fetches ALL parliamentary members and calculates precise party percentages.",
    tags={"DIP", "analysis", "party"},
)
def get_party_distribution(
    wahlperiode: Annotated[int, Field(
        description="Electoral period number. Current period is 21, historical periods available from 1."
    )],
) -> list:
    """
    Get party distribution for Bundestag members in a specific Wahlperiode.
    
    This tool automatically:
    - Filters for BUNDESTAG-ONLY members (excludes Bundesrat, Bundesversammlung, Europakammer)
    - Handles pagination to retrieve every single Bundestag member 
    - Calculates accurate party distribution percentages
    
    Returns a list of party statistics in the format:
    [
        {"fraktion": "AfD", "count": 148, "percentage": 30.83},
        {"fraktion": "BÜNDNIS 90/DIE GRÜNEN", "count": 78, "percentage": 16.25}
    ]
    
    Important: Only includes Bundestag (BT) members, not Bundesrat (BR) or other institutions.
    """
    if not DIP_API_KEY:
        raise RuntimeError("Missing API key: set DIP_API_KEY in the environment or .env file.")

    all_members = []
    cursor = None
    pages_fetched = 0
    
    # Fetch all pages until no more data
    while True:
        params = {
            "format": "json", 
            "apikey": DIP_API_KEY,
            "f.wahlperiode": [wahlperiode],
            "f.zuordnung": "BT"  # Only Bundestag members, not Bundesrat/etc
        }
        if cursor:
            params["cursor"] = cursor
            
        url = f"{BASE_URL}/person"
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


@mcp.tool(
    name="new_get_person",
    description="Simplified version of get_person - basic search for German parliamentary members with optional name and wahlperiode filtering.",
    tags={"DIP", "person", "simple"},
)
def new_get_person(name: str = None, wahlperiode: int = None) -> dict:
    """
    Simplified version of get_person that performs a basic search for German parliamentary members.
    
    This function fetches persons from the DIP API with optional name and wahlperiode filtering.
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
    
    RESPONSE FORMAT:
    Returns a dictionary with:
    - numFound: Total number of matching persons
    - cursor: Pagination cursor for next page
    - documents: Array of person objects with basic information
    
    EXAMPLE USAGE:
    # Get all persons
    result = new_get_person()
    
    # Search by last name
    result = new_get_person("Merkel")
    
    # Search by full name
    result = new_get_person("Steinmeier Frank Walter")
    
    # Get all current Bundestag members (period 21)
    result = new_get_person(wahlperiode=21)
    
    # Search for specific person in current period
    result = new_get_person("Merkel", wahlperiode=21)
    
    # Process results
    print(f"Found {result['numFound']} persons")
    for person in result['documents']:
        print(f"{person['vorname']} {person['nachname']}")
    """
    if not DIP_API_KEY:
        raise RuntimeError("Missing API key: set DIP_API_KEY in the environment or .env file.")

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

    url = f"{BASE_URL}/person"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    mcp.run()