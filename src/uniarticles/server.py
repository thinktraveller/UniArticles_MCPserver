from mcp.server.fastmcp import FastMCP

from .sources import register_all_sources


def create_server() -> FastMCP:
    server = FastMCP("uniarticles-mcp")
    register_all_sources(server)
    return server
