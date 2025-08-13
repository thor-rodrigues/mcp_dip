# MCP DIP Parliamentary Data Server

A comprehensive Model Context Protocol (MCP) server and Streamlit frontend for accessing German Parliamentary data from the DIP (Dokumentations- und Informationssystem für Parlamentsmaterialien) API.

## Overview

This project provides a complete solution for querying and analysing German Parliamentary data through a FastMCP server backend and two interactive Streamlit frontend applications. The system allows users to search for parliamentary members, analyse party distributions, and interact with the data through both a conversational AI interface and a dedicated data analysis interface.

## Features

### MCP Server (`src/backend/dip_server.py`)
- **Parliamentary Member Search**: Query members by name, electoral period (Wahlperiode), with pagination support
- **Party Distribution Analysis**: Comprehensive analysis of party representation across electoral periods
- **Mathematical Operations**: Basic arithmetic tools (add, subtract, multiply, divide)
- **DIP API Integration**: Direct access to the official German Bundestag database
- **FastMCP Framework**: Built on the modern FastMCP framework for efficient tool execution

### Frontend Applications

#### 1. Chat Interface (`src/frontend/chat_with_mcp.py`)
- **Conversational AI**: Natural language interaction with parliamentary data
- **LangGraph Integration**: Powered by LangGraph React agent with memory
- **Google Gemini**: Uses Gemini 2.5 Flash for intelligent responses
- **Multi-tool Access**: All MCP server tools available through natural conversation
- **Persistent Memory**: Conversation context maintained across interactions

#### 2. Parliamentary Analysis Interface (`src/frontend/parliment_analysis.py`)
- **Visual Data Analysis**: Dedicated interface for parliamentary data exploration
- **Party Distribution Visualisation**: Metrics and breakdowns of party representation
- **Electoral Period Selection**: Choose from historical or current parliamentary periods (1-21)
- **Data Export**: Download comprehensive party analysis as JSON with metadata
- **Real-time Notifications**: Toast notifications and progress indicators

## Installation

### Prerequisites
- Python 3.11 or higher
- [uv package manager](https://docs.astral.sh/uv/) (recommended)

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/thor-rodrigues/mcp_dip
   cd mcp_dip
   ```

2. **Install dependencies using uv** (recommended):
   ```bash
   uv install
   ```

   Or alternatively with pip:
   ```bash
   pip install -e .
   ```

3. **Environment Configuration**:
   Create a `.env` file in the project root with your API keys:
   ```env
   DIP_API_KEY=your_dip_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   ```

   **For Streamlit deployment**, create `.streamlit/secrets.toml`:
   ```toml
   DIP_API_KEY = "your_dip_api_key_here"
   GOOGLE_API_KEY = "your_google_api_key_here"
   ```

4. **API Key Setup**:
   - **DIP API Key**: Register at [DIP Bundestag Portal](https://dip.bundestag.de/) for access to parliamentary data
   - **Google API Key**: Obtain from [Google AI Studio](https://aistudio.google.com/) for Gemini access

## Usage

### Running the MCP Server (Optional)

**Note**: You do **not** need to start the MCP server separately to use the Streamlit application. The Streamlit app includes all MCP tools internally and will connect to the MCP server automatically when needed.

Only run the MCP server directly if you want to use it as a standalone service for other MCP clients:

```bash
# Start the MCP server directly (for standalone use only)
python src/backend/dip_server.py

# Or run with uv
uv run python src/backend/dip_server.py
```

### Running the Frontend Application

```bash
# Start the Streamlit multi-page application (includes MCP integration)
streamlit run app.py

# Or with uv
uv run streamlit run app.py
```

The application provides a unified interface with navigation between two main features:

#### 1. Parliamentary Data Analysis (Default Page)
- Select electoral periods from dropdown (periods 1-21 available)
- View comprehensive party statistics and member counts
- Download detailed analysis with member lists as JSON
- Real-time data fetching with progress indicators

#### 2. Chat with MCP Interface
Features available through natural language:
- "Find members named Merkel in period 21"
- "What's the party distribution for the current parliament?"
- "Calculate 15 + 27"
- "Show me all AfD members from 2017-2021"

## Technical Architecture

### Dependencies
- **FastMCP**: Modern MCP server framework for tool integration
- **Streamlit**: Web application framework for interactive frontends
- **LangGraph**: Agent framework for conversational AI workflows
- **Google Generative AI**: Gemini 2.5 Flash for natural language processing
- **Requests**: HTTP client for DIP API communication
- **Pydantic**: Data validation and serialisation

### Data Sources
- **DIP API**: Official German Bundestag parliamentary database
- **Electoral Periods**: Supports periods 1-21 (1949-2029)
- **Real-time Data**: Direct API access ensures up-to-date information

### API Capabilities
- **Member Search**: Search by name with fuzzy matching
- **Electoral Period Filtering**: Historical and current period support
- **Pagination**: Handle large datasets efficiently
- **Party Analysis**: Comprehensive party distribution calculations
- **Error Handling**: Robust error handling and user feedback

## Project Structure
```
mcp_dip/
├── app.py                         # Streamlit multi-page application entry point
├── src/
│   ├── backend/
│   │   └── dip_server.py          # FastMCP server with DIP API tools
│   └── frontend/
│       ├── chat_with_mcp.py       # Conversational AI interface
│       └── parliment_analysis.py  # Data analysis interface
├── pyproject.toml                 # Project configuration and dependencies
├── LICENSE                        # Project licence
└── README.md                     # This file
```



## Licence

This project is licensed under the MIT License. See the LICENSE file for details.
