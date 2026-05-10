import json
import unittest

from scidownl.db.entities import ScihubUrl, create_storage, get_storage_path


class TestEntities(unittest.TestCase):
    def setUp(self) -> None:
        storage_path = get_storage_path(test=True)
        if storage_path.exists():
            storage_path.unlink()

    def tearDown(self) -> None:
        storage_path = get_storage_path(test=True)
        if storage_path.exists():
            storage_path.unlink()

    def test_create_storage(self) -> None:
        create_storage(test=True)

        storage_path = get_storage_path(test=True)
        self.assertTrue(storage_path.is_file())
        self.assertEqual({"scihub_urls": []}, json.loads(storage_path.read_text(encoding="utf-8")))

    def test_scihub_url_json_round_trip(self) -> None:
        item = ScihubUrl(url="http://sci-hub.se", success_times=2, failed_times=1)

        restored_item = ScihubUrl.from_dict(item.to_dict())

        self.assertEqual(item, restored_item)


if __name__ == "__main__":
    unittest.main()
