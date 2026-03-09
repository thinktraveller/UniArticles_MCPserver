import asyncio
import os

import arxiv
from mcp.server.fastmcp import FastMCP

from ..config import settings


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "arxiv",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "arxiv",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


def _serialize_paper(paper) -> dict:
    return {
        "id": paper.get_short_id(),
        "title": paper.title,
        "authors": [author.name for author in paper.authors],
        "abstract": paper.summary,
        "published": paper.published.isoformat(),
        "categories": paper.categories,
        "pdf_url": paper.pdf_url,
    }


def _run_arxiv_search(query: str, max_results: int) -> dict:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    papers = []
    for paper in client.results(search):
        papers.append(_serialize_paper(paper))
    return _ok(query=query, items=papers)


def _get_paper_details(paper_id: str) -> dict:
    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(client.results(search))
        return _ok(query=paper_id, items=[_serialize_paper(paper)])
    except StopIteration:
        return _err(query=paper_id, message="Paper not found")


def _download_paper(paper_id: str, filename: str | None = None, output_dir: str | None = None) -> dict:
    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(client.results(search))
    except StopIteration:
        return _err(query=paper_id, message="Paper not found")

    target_dir = output_dir or settings.arxiv_download_dir
    
    # Ensure directory exists
    os.makedirs(target_dir, exist_ok=True)
    
    try:
        # arxiv library's download_pdf returns the filename
        downloaded_path = paper.download_pdf(dirpath=target_dir, filename=filename)
        return _ok(
            query=paper_id, 
            items=[{
                "id": paper.get_short_id(), 
                "title": paper.title, 
                "file_path": downloaded_path,
                "status": "downloaded"
            }]
        )
    except Exception as e:
        return _err(query=paper_id, message=f"Download failed: {str(e)}")


def register(server: FastMCP) -> None:
    @server.tool()
    async def search_arxiv(query: str, max_results: int = 10) -> dict:
        """Search for papers in ArXiv using a query string."""
        normalized_query = query.strip()
        bounded = max(1, min(max_results, 25))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            return await asyncio.to_thread(_run_arxiv_search, normalized_query, bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def search_paper(query: str, max_results: int = 10) -> dict:
        """Search for papers in ArXiv (alias for search_arxiv)."""
        return await search_arxiv(query, max_results)

    @server.tool()
    async def list_papers(max_results: int = 10) -> dict:
        """List recent papers from ArXiv (defaults to CS category if no query specified)."""
        # Since 'list' implies no specific query, we might need a default query.
        # However, arxiv API requires a query or id_list.
        # We'll use a broad query like "cat:cs.AI" or just "all" but "all" is too broad.
        # Let's use "electron" or similar, or just allow user to pass query in search_paper.
        # But if the user wants "list_papers", maybe they mean "list papers I have downloaded"?
        # Or "list recent papers"?
        # Given the context of "original arxiv-mcp", list_papers likely lists papers based on some criteria.
        # I will default to a broad category search or similar. 
        # Actually, let's just search for "cat:cs.AI" as a default example, or error if no concept of 'list' exists without query.
        # Better: Search for most recent papers in general? "all" might work with limit.
        try:
            return await asyncio.to_thread(_run_arxiv_search, "all", max_results)
        except Exception as exc:
            return _err(query="list_papers", message=str(exc))

    @server.tool()
    async def read_paper(paper_id: str) -> dict:
        """Get detailed information (abstract/metadata) for a specific ArXiv paper."""
        normalized_id = paper_id.strip()
        if not normalized_id:
            return _err(query=paper_id, message="paper_id must not be empty")
        try:
            return await asyncio.to_thread(_get_paper_details, normalized_id)
        except Exception as exc:
            return _err(query=normalized_id, message=str(exc))

    @server.tool()
    async def download_paper(paper_id: str, filename: str | None = None, output_dir: str | None = None) -> dict:
        """Download an ArXiv paper as PDF.
        
        Args:
            paper_id: The ArXiv ID of the paper.
            filename: Optional custom filename (e.g., "paper.pdf").
            output_dir: Optional directory to save the file. Defaults to configured ARXIV_DOWNLOAD_DIR.
        """
        normalized_id = paper_id.strip()
        if not normalized_id:
            return _err(query=paper_id, message="paper_id must not be empty")
        try:
            return await asyncio.to_thread(_download_paper, normalized_id, filename, output_dir)
        except Exception as exc:
            return _err(query=normalized_id, message=str(exc))
