import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    scopus_api_key: str | None = os.getenv("SCOPUS_API_KEY")
    arxiv_download_dir: str = os.getenv("ARXIV_DOWNLOAD_DIR", os.path.join(os.getcwd(), "arxiv_downloads"))


settings = Settings()
