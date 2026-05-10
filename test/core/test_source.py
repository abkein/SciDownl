import unittest

from scidownl.core.source import DoiSource, PmidSource, TitleSource
from scidownl.exception import (
    EmptyDoiException,
    EmptyPmidException,
    EmptyTitleException,
)


class TestSource(unittest.TestCase):
    def test_create_doi_source(self) -> None:
        # Empty case: doi is None.
        with self.assertRaises(EmptyDoiException):
            DoiSource(None)

        # Empty case: doi is an empty string.
        with self.assertRaises(EmptyDoiException):
            DoiSource("")

        # Invalid type case: doi is not a string.
        with self.assertRaises(TypeError):
            DoiSource(2345783)

        # Correct case.
        cases = {
            "http_doi": "http://doi.org/10.1145/1327452.1327492",
            "https_doi": "https://doi.org/10.1145/1327452.1327492",
            "raw_doi": "doi.org/10.1145/1327452.1327492",
        }
        doi_source = DoiSource(cases["http_doi"])
        self.assertEqual("doi.org/10.1145/1327452.1327492", doi_source.get_doi())
        self.assertEqual("http", doi_source.get_protocol())

        doi_source = DoiSource(cases["https_doi"])
        self.assertEqual("doi.org/10.1145/1327452.1327492", doi_source.get_doi())
        self.assertEqual("https", doi_source.get_protocol())

        doi_source = DoiSource(cases["raw_doi"])
        self.assertEqual("doi.org/10.1145/1327452.1327492", doi_source.get_doi())
        self.assertEqual("https", doi_source.get_protocol())

    def test_create_pmid_source(self) -> None:
        # Empty case: PMID is None.
        with self.assertRaises(EmptyPmidException):
            PmidSource(None)

        # Empty case: doi is an empty string.
        with self.assertRaises(EmptyPmidException):
            PmidSource("")

        # Invalid type case: doi is not a string.
        with self.assertRaises(TypeError):
            PmidSource(True)
            PmidSource([])
            PmidSource({})

        # Correct case.
        cases = {
            "PMID_str": "31928726",
            "PMID_number": 31928726,
        }
        pmid_source = PmidSource(cases["PMID_str"])
        self.assertEqual(cases["PMID_str"], pmid_source.get_pmid())

        pmid_source = PmidSource(cases["PMID_number"])
        self.assertEqual(str(cases["PMID_number"]), pmid_source.get_pmid())

    def test_create_title_source(self) -> None:
        # Empty case: TITLE is None.
        with self.assertRaises(EmptyTitleException):
            TitleSource(None)

        # Empty case: doi is an empty string.
        with self.assertRaises(EmptyTitleException):
            TitleSource("")

        # Invalid type case: doi is not a string.
        with self.assertRaises(TypeError):
            TitleSource(True)
            TitleSource([])
            TitleSource({})

        # Correct case.
        cases = {
            "title1": "Visualizing Distributed System Executions",
            "title2": "    Measuring and improving customer retention at authorised automobile workshops after free services   ",
        }
        title_source = TitleSource(cases["title1"])
        self.assertEqual(cases["title1"], title_source.get_title())

        title_source = TitleSource(cases["title2"])
        self.assertEqual(str(cases["title2"]).strip(), title_source.get_title())


if __name__ == "__main__":
    unittest.main()
