from mcp.server.fastmcp import FastMCP

from .arxiv import register as register_arxiv_source
from .paperscraper import register as register_paperscraper_source
from .scopus import register as register_scopus_source


def register_all_sources(server: FastMCP) -> None:
    register_arxiv_source(server)
    register_paperscraper_source(server)
    register_scopus_source(server)
