import shutil
import unittest
from pathlib import Path

from scidownl.core.task import ScihubTask
from scidownl.log import get_logger
from scidownl.config import get_config

logger = get_logger()
configs = get_config()


class TestTask(unittest.TestCase):

    def test_run_tasks(self) -> None:
        self.skipTest("Just")
        tmp_paper_dir = Path("./.tmp_paper/")
        cases = [
            ("10.1016/bs.apcsb.2019.08.001", "doi", tmp_paper_dir),  # ./<title>.pdf
            ("10.3343/alm.2013.33.1.8", "doi", tmp_paper_dir),
            ("31256946", "pmid", tmp_paper_dir),
            ("18691502", "pmid", tmp_paper_dir),
            ("33253586", "pmid", tmp_paper_dir),
            ("10.1093/oxfordjournals.jmicro.a023417", "doi", tmp_paper_dir),
            ("10.1002/chin.197335038", "doi", tmp_paper_dir),
            (
                "Measuring and improving customer retention at authorised automobile workshops after free services    ",
                "title",
                tmp_paper_dir,
            ),
            ("Synthetic Biology Goes Cell-Free", "title", tmp_paper_dir),
        ]
        for case in cases:
            task = ScihubTask(source_keyword=case[0], source_type=case[1], out=case[2])
            try:
                task.run()
            except Exception:
                logger.error(f"final status: {task.context['status']}, error: {task.context['error']}")

        if tmp_paper_dir.exists():
            shutil.rmtree(tmp_paper_dir)

    def test_run_one_task(self) -> None:
        self.skipTest("Just")
        tmp_paper_dir = Path("./.tmp_paper/")
        ScihubTask(
            source_keyword="10.1016/bs.apcsb.2019.08.001",
            source_type="doi",
            out=tmp_paper_dir,
        ).run()

        if tmp_paper_dir.exists():
            shutil.rmtree(tmp_paper_dir)

    def test_run_one_task_with_proxies(self) -> None:
        self.skipTest("Just")
        tmp_paper_dir = Path("./.tmp_paper/")
        ScihubTask(
            source_keyword="10.1016/bs.apcsb.2019.08.001",
            source_type="doi",
            out=tmp_paper_dir,
            proxies={
                # 'http': 'http://127.0.0.1:7890'
                "https": "socks5://127.0.0.1:1080"
            },
        ).run()

        if tmp_paper_dir.exists():
            shutil.rmtree(tmp_paper_dir)


if __name__ == "__main__":
    unittest.main()
