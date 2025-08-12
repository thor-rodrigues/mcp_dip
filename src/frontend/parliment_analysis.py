import streamlit as st
import asyncio
from fastmcp import Client
import os
import json
from datetime import datetime

st.title(":material/how_to_vote: DIP Parliamentary Data MCP Server")
st.markdown("""
            This page displays information about the German parliament,
            fetched via MCP from the DIP (Dokumentations- und Informationssystem
            für Parlamentsmaterialien) API.
            """)

# Check if MCP server exists
mcp_server_path = "src/backend/dip_server.py"
if not os.path.exists(mcp_server_path):
    st.error(f":material/error: MCP server file '{mcp_server_path}' not found. Please ensure it exists.")
    st.stop()

# UI Components
st.subheader("Parliamentary Data Query")

# Enhanced Wahlperiode selection with context
wahlperiode_options = {
    21: "21 (2025-2029)",
    20: "20 (2021-2025)",
    19: "19 (2017-2021)", 
    18: "18 (2013-2017)",
    17: "17 (2009-2013)",
}

wahlperiode = st.selectbox(
    ":material/how_to_vote: Electoral Period (Wahlperiode)",
    options=list(wahlperiode_options.keys()),
    format_func=lambda x: wahlperiode_options[x],
    index=0,  # Default to period 20 (complete term)
    help=":material/warning: Party distributions can change mid-term due to switching, defections, or new party formations!"
)



# Fetch data button
if st.button(":material/search: Fetch Party Distribution", type="primary", use_container_width=True):
    # Show toast notification when starting
    toast_msg = st.toast("Starting MCP server connection...")
    
    with st.spinner("Connecting to MCP server and fetching data..."):
        
        async def fetch_data():
            """Fetch data using MCP client"""
            try:
                # Connect to your MCP server (on-demand)
                client = Client(mcp_server_path)
                
                async with client:
                    # Use the party distribution tool for challenge requirements
                    result = await client.call_tool("get_party_distribution", {
                        "wahlperiode": wahlperiode
                    })
                    return result.data
                    
            except Exception as e:
                return {"error": str(e)}
        
        # Run the async function
        try:
            # Update toast for data fetching
            toast_msg.toast("Fetching parliamentary data...")
            results = asyncio.run(fetch_data())
            
            if "error" in results:
                toast_msg.toast("Error occurred while fetching data!")
                st.error(f":material/error: Error: {results['error']}")
            else:
                # results is now a list of party distribution data
                party_dist = results if isinstance(results, list) else []
                total_members = sum(party['count'] for party in party_dist) if party_dist else 0
                
                # Success toast with analysis info
                toast_msg.toast(f"Party analysis: {total_members} members, {len(party_dist)} parties!")
                
                # First row: Total Members and Number of Parties
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Members", total_members)
                with col2:
                    st.metric("Number of Parties", len(party_dist))
                
                # Second row: Largest Party (full width)
                if party_dist:
                    st.metric("Largest Party", f"{party_dist[0]['fraktion']} ({party_dist[0]['percentage']}%)")
                
                st.divider()

                # Show party distribution
                if party_dist:
                    st.subheader("Party Distribution")
                    for party_info in party_dist:
                        st.write(f"**{party_info['fraktion']}**: {party_info['count']} members ({party_info['percentage']}%)")
                
                # Raw data in expander
                with st.expander("View Party Distribution JSON"):
                    st.json(results)

                # Prepare download data with metadata
                download_data = {
                    "metadata": {
                        "wahlperiode": wahlperiode,
                        "wahlperiode_description": wahlperiode_options[wahlperiode],
                        "total_members": total_members,
                        "number_of_parties": len(party_dist),
                        "generated_at": datetime.now().isoformat(),
                        "source": "DIP (Dokumentations- und Informationssystem für Parlamentsmaterialien)"
                    },
                    "party_distribution": results
                }
                
                # Generate filename with wahlperiode
                filename = f"party_distribution_wahlperiode_{wahlperiode}.json"
                
                st.download_button(
                    label=":material/file_download: Download Party Analysis as JSON",
                    data=json.dumps(download_data, indent=2, ensure_ascii=False),
                    file_name=filename,
                    mime="application/json",
                    type="primary",
                    width="stretch",
                    key="download_party_distribution_button"
                )
                    
        except Exception as e:
            toast_msg.toast("MCP server connection failed!")
            st.error(f"Failed to connect to MCP server: {str(e)}")
            st.info("Make sure your .env file contains the DIP_API_KEY")