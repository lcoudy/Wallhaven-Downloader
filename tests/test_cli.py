import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from wallhaven_downloader.cli import build_parser, main


class CliTest(unittest.TestCase):
    def test_parser_accepts_url_mode(self):
        args = build_parser().parse_args(["--url", "https://wallhaven.cc/hot", "-o", "downloads"])

        self.assertEqual(args.url, "https://wallhaven.cc/hot")
        self.assertEqual(args.output, Path("downloads"))

    def test_main_uses_search_mode_without_url(self):
        with (
            patch("wallhaven_downloader.cli.download_from_search", return_value=[]) as download_from_search,
            redirect_stdout(io.StringIO()),
        ):
            exit_code = main(["-o", "downloads", "--sorting", "toplist", "--top-range", "1M"])

        self.assertEqual(exit_code, 0)
        download_from_search.assert_called_once()
