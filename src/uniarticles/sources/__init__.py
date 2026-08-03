from mcp.server.fastmcp import FastMCP

from .scopus import register as register_scopus_source
from .sciencedirect import register as register_sciencedirect_source
from .arxiv import register as register_arxiv_source
from .paperscraper import register as register_paperscraper_source


def register_all_sources(server: FastMCP) -> None:
    register_scopus_source(server)
    register_sciencedirect_source(server)
    register_arxiv_source(server)
    register_paperscraper_source(server)
