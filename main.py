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
    - get_person: Retrieve parliament member information and biographical data
    
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
    - Get all current members: get_person(wahlperiode=[21])
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
    if cursor:
        params["cursor"] = cursor

    url = f"{BASE_URL}/person"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json() if format == "json" else resp.text


if __name__ == "__main__":
    mcp.run()