from mcp.server.fastmcp import FastMCP

from .scopus import register as register_scopus_source
from .sciencedirect import register as register_sciencedirect_source
from .arxiv import register as register_arxiv_source
from .pubmed import register as register_pubmed_source
from .openalex import register as register_openalex_source
from .crossref import register as register_crossref_source
from .europepmc import register as register_europepmc_source
from .doaj import register as register_doaj_source
from .zenodo import register as register_zenodo_source
from .openaire import register as register_openaire_source
from .semantic_scholar import register as register_semantic_scholar_source
from .core import register as register_core_source
from .dblp import register as register_dblp_source
from .biorxiv import register as register_biorxiv_source


def register_all_sources(server: FastMCP) -> None:
    # v2.x 既有数据源（Elsevier 全家桶 + arXiv + PubMed）
    register_scopus_source(server)
    register_sciencedirect_source(server)
    register_arxiv_source(server)
    register_pubmed_source(server)  # v3.1.0: 直连 NCBI Entrez（原 paperscraper 第三方包）
    # v3.0.0 新增：通用检索型（标准 query 关键词检索模式）
    register_openalex_source(server)
    register_crossref_source(server)
    register_europepmc_source(server)
    register_doaj_source(server)
    register_zenodo_source(server)
    register_openaire_source(server)
    register_semantic_scholar_source(server)  # 无 SEMANTIC_SCHOLAR_API_KEY 时不注册任何工具
    register_core_source(server)
    register_dblp_source(server)
    # v3.0.0 新增：语义特殊型（非关键词检索）
    register_biorxiv_source(server)  # 浏览语义（server/start_date/end_date/cursor）
