import unittest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from curl_cffi.requests.exceptions import RequestException
    from curl_cffi import requests as requests

    HAS_CURL_CFFI = True
else:
    try:
        from curl_cffi import requests as requests
        from curl_cffi.requests.exceptions import RequestException

        HAS_CURL_CFFI = True
    except (ModuleNotFoundError, ImportError):
        import requests
        from requests.exceptions import RequestException

        HAS_CURL_CFFI = False  # pyright: ignore[reportConstantRedefinition]


from scidownl.core.source import PmidSource, DoiSource
from scidownl.core.crawler import ScihubCrawler
from scidownl.exception import CrawlException


class TestCrawler(unittest.TestCase):
    def test_scihub_crawl(self) -> None:
        scihub_url = "https://sci-hub.st"
        try:
            sess = requests.Session()
            sess.get(scihub_url)
        except RequestException:
            self.skipTest("Failed to establish connection")

        # Test crawling with PMID.
        pmid_source = PmidSource(31928726)
        ScihubCrawler(pmid_source, scihub_url).crawl()

        # Test crawling with DOI.
        doi_source = DoiSource("10.1016/bs.apcsb.2019.08.001")
        ScihubCrawler(doi_source, scihub_url).crawl()

        # Test crawling a non-existent PMID should raise an error.
        pmid_source = PmidSource(0)
        with self.assertRaises(CrawlException):
            ScihubCrawler(pmid_source, scihub_url).crawl()


if __name__ == "__main__":
    unittest.main()
