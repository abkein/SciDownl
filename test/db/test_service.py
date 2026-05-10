import unittest

from scidownl.db.entities import ScihubUrl, get_storage_path
from scidownl.db.service import ScihubUrlService


class TestDBServices(unittest.TestCase):
    service: ScihubUrlService

    def setUp(self) -> None:
        storage_path = get_storage_path(test=True)
        if storage_path.exists():
            storage_path.unlink()
        self.service = ScihubUrlService(test=True)

    def tearDown(self) -> None:
        storage_path = get_storage_path(test=True)
        if storage_path.exists():
            storage_path.unlink()

    def test_scihub_url_service_add_urls(self) -> None:
        urls = [
            ScihubUrl(url="http://sci-hub.se"),
            ScihubUrl(url="https://sci-hub.sd"),
        ]

        self.service.add_urls(urls)

        self.assertEqual(urls, self.service.get_all_urls())

    def test_scihub_url_service_ignores_duplicate_urls(self) -> None:
        self.service.add_urls(
            [
                ScihubUrl(url="http://sci-hub.se"),
                ScihubUrl(url="http://sci-hub.se"),
            ]
        )

        all_urls = self.service.get_all_urls()

        self.assertEqual(1, len(all_urls))
        self.assertEqual("http://sci-hub.se", all_urls[0].url)

    def test_scihub_url_service_incr_success_times(self) -> None:
        self.service.add_urls([ScihubUrl(url="http://sci-hub.se")])

        self.service.increment_success_times("http://sci-hub.se")

        [saved_url] = self.service.get_all_urls()
        self.assertEqual(1, saved_url.success_times)
        self.assertEqual(0, saved_url.failed_times)

    def test_scihub_url_service_incr_failed_times(self) -> None:
        self.service.add_urls([ScihubUrl(url="http://sci-hub.se")])

        self.service.increment_failed_times("http://sci-hub.se")

        [saved_url] = self.service.get_all_urls()
        self.assertEqual(0, saved_url.success_times)
        self.assertEqual(1, saved_url.failed_times)

    def test_scihub_url_service_get_all_urls(self) -> None:
        self.assertEqual([], self.service.get_all_urls())


if __name__ == "__main__":
    unittest.main()
