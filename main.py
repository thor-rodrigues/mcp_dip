from fastmcp import FastMCP

mcp = FastMCP("Dokumentations- und Informationssystems für Parlamentsmaterialien (DIP) - MCP Server")

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()