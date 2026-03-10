import asyncio
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure the source path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from uniarticles.sources import scopus, arxiv
from uniarticles.config import Settings

# Sample OAI XML for testing
SAMPLE_OAI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
         http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>2023-10-27T10:00:00Z</responseDate>
  <request verb="ListRecords" metadataPrefix="oai_dc">https://example.org/oai</request>
  <ListRecords>
    <record>
      <header>
        <identifier>oai:example.org:12345</identifier>
        <datestamp>2023-10-26T00:00:00Z</datestamp>
        <setSpec>example</setSpec>
      </header>
      <metadata>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
                   http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
          <dc:title>Test Title</dc:title>
          <dc:creator>Author One</dc:creator>
        </oai_dc:dc>
      </metadata>
    </record>
  </ListRecords>
</OAI-PMH>
"""

class TestScopusFunctions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch settings to include API key
        self.settings_patcher = patch("uniarticles.sources.scopus.settings")
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.scopus_api_key = "dummy_key"

    def tearDown(self):
        self.settings_patcher.stop()

    async def test_get_abstract(self):
        with patch("uniarticles.sources.scopus.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "abstracts-retrieval-response": {"coredata": {"dc:title": "Abstract Title"}}
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await scopus._get_abstract("eid-123")
            
            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "scopus")
            self.assertEqual(result["query"], "eid-123")
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(
                result["items"][0]["abstracts-retrieval-response"]["coredata"]["dc:title"], 
                "Abstract Title"
            )

    async def test_get_author(self):
        with patch("uniarticles.sources.scopus.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "author-retrieval-response": [{"preferred-name": {"surname": "Doe"}}]
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await scopus._get_author("auth-123")
            
            self.assertTrue(result["ok"])
            self.assertEqual(result["query"], "auth-123")
            self.assertEqual(len(result["items"]), 1)

    async def test_get_quota(self):
        with patch("uniarticles.sources.scopus.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {
                "X-RateLimit-Limit": "1000",
                "X-RateLimit-Remaining": "999",
                "X-RateLimit-Reset": "1234567890"
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await scopus._get_quota()
            
            self.assertTrue(result["ok"])
            self.assertEqual(result["query"], "quota")
            self.assertEqual(result["items"][0]["limit"], "1000")
            self.assertEqual(result["items"][0]["remaining"], "999")


class TestArxivFunctions(unittest.IsolatedAsyncioTestCase):
    async def test_search_paper(self):
        with patch("uniarticles.sources.arxiv.arxiv.Client") as mock_client_cls, \
             patch("uniarticles.sources.arxiv.arxiv.Search") as mock_search_cls:
            
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            
            mock_paper = MagicMock()
            mock_paper.get_short_id.return_value = "1234.5678"
            mock_paper.title = "Test Arxiv Paper"
            mock_paper.authors = [MagicMock(name="Author One")]
            mock_paper.authors[0].name = "Author One"
            mock_paper.summary = "Test Abstract"
            mock_paper.published.isoformat.return_value = "2023-01-01"
            mock_paper.categories = ["cs.AI"]
            mock_paper.pdf_url = "http://arxiv.org/pdf/1234.5678"
            
            mock_client.results.return_value = [mock_paper]
            
            result = arxiv._run_arxiv_search("test", 10)
            
            self.assertTrue(result["ok"])
            self.assertEqual(result["source"], "arxiv")
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["title"], "Test Arxiv Paper")

    async def test_get_paper_details(self):
        with patch("uniarticles.sources.arxiv.arxiv.Client") as mock_client_cls, \
             patch("uniarticles.sources.arxiv.arxiv.Search") as mock_search_cls:
            
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            
            mock_paper = MagicMock()
            mock_paper.get_short_id.return_value = "1234.5678"
            mock_paper.title = "Specific Paper"
            mock_paper.authors = []
            mock_paper.summary = "Abstract"
            mock_paper.published.isoformat.return_value = "2023-01-01"
            mock_paper.categories = []
            mock_paper.pdf_url = "url"
            
            # mock iterator
            mock_client.results.return_value = iter([mock_paper])
            
            result = arxiv._get_paper_details("1234.5678")
            
            self.assertTrue(result["ok"])
            self.assertEqual(result["items"][0]["title"], "Specific Paper")

    async def test_download_paper(self):
        with patch("uniarticles.sources.arxiv.arxiv.Client") as mock_client_cls, \
             patch("uniarticles.sources.arxiv.arxiv.Search") as mock_search_cls, \
             patch("uniarticles.sources.arxiv.os.makedirs") as mock_makedirs:
            
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            
            mock_paper = MagicMock()
            mock_paper.get_short_id.return_value = "1234.5678"
            mock_paper.title = "Downloadable Paper"
            mock_paper.download_pdf.return_value = "/path/to/downloaded.pdf"
            
            mock_client.results.return_value = iter([mock_paper])
            
            result = arxiv._download_paper("1234.5678", output_dir="/tmp/test")
            
            self.assertTrue(result["ok"])
            self.assertEqual(result["items"][0]["status"], "downloaded")
            self.assertEqual(result["items"][0]["file_path"], "/path/to/downloaded.pdf")
            mock_makedirs.assert_called_with("/tmp/test", exist_ok=True)
            mock_paper.download_pdf.assert_called()

if __name__ == "__main__":
    unittest.main()
