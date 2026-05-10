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


from pathlib import Path

from scidownl.core.information import PdfUrlTitleInformation
from scidownl.core.downloader import UrlDownloader
from scidownl.log import get_logger

logger = get_logger()


class TestDownloader(unittest.TestCase):
    def test_download_information(self) -> None:
        try:
            sess = requests.Session()
            sess.get("https://sci-hub.st")
        except RequestException:
            self.skipTest("Failed to establish connection")

        url = "https://sci-hub.st/downloads/2020-01-20/c1/nademi2019.pdf"
        title = "Protein misfolding in endoplasmic reticulum stress with applications to renal diseases. Advances in Protein Chemistry and Structural Biology, 217–247"
        info = PdfUrlTitleInformation(url, title)

        downloader = UrlDownloader(info)
        out = Path("test_paper.pdf")
        downloader.download(out)
        self.assertTrue(out.exists())
        out.unlink()
        logger.debug(f"Remove the test paper file: {out}")


if __name__ == "__main__":
    unittest.main()
