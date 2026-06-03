import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from wallhaven_downloader.core import (
    DownloadResult,
    build_search_url,
    download_wallpapers,
    extract_wallpaper_links,
    image_url_for,
    iter_page_urls,
    request_with_retries,
    wallpaper_id_from_url,
)


class CoreTest(unittest.TestCase):
    def test_iter_page_urls_adds_page_query_when_missing(self):
        urls = iter_page_urls("https://wallhaven.cc/hot", 3)

        self.assertEqual(
            urls,
            [
                "https://wallhaven.cc/hot",
                "https://wallhaven.cc/hot?page=2",
                "https://wallhaven.cc/hot?page=3",
            ],
        )

    def test_iter_page_urls_increments_existing_page_query(self):
        urls = iter_page_urls("https://wallhaven.cc/search?q=cat&page=9", 2)

        self.assertEqual(
            urls,
            [
                "https://wallhaven.cc/search?q=cat&page=9",
                "https://wallhaven.cc/search?q=cat&page=10",
            ],
        )

    def test_extract_wallpaper_links(self):
        html = """
        <section class="thumb-listing-page">
          <ul>
            <li><a href="https://wallhaven.cc/w/abc123">one</a></li>
            <li><a href="https://wallhaven.cc/w/def456">two</a></li>
          </ul>
        </section>
        """

        self.assertEqual(
            extract_wallpaper_links(html),
            ["https://wallhaven.cc/w/abc123", "https://wallhaven.cc/w/def456"],
        )

    def test_build_search_url(self):
        self.assertEqual(
            build_search_url("toplist", "1M", "110", "101", 4),
            "https://wallhaven.cc/search?categories=101&purity=110&topRange=1M&sorting=toplist&order=desc&page=4",
        )

    def test_image_url_for(self):
        self.assertEqual(
            image_url_for("abc123", "png"),
            "https://w.wallhaven.cc/full/ab/wallhaven-abc123.png",
        )

    def test_wallpaper_id_from_url(self):
        self.assertEqual(wallpaper_id_from_url("https://wallhaven.cc/w/abc123/"), "abc123")

    def test_request_with_retries_retries_retryable_status(self):
        first = Mock(status_code=500)
        second = Mock(status_code=200)
        client = Mock()
        client.request.side_effect = [first, second]

        with patch("wallhaven_downloader.core.time.sleep"):
            response = request_with_retries(client, "GET", "https://example.test", retries=1)

        self.assertIs(response, second)
        self.assertEqual(client.request.call_count, 2)

    def test_download_wallpapers_reports_progress(self):
        progress = []

        with (
            patch("wallhaven_downloader.core.fetch_wallpaper_links", return_value=["https://wallhaven.cc/w/abc123"]),
            patch("wallhaven_downloader.core.resolve_image_url", return_value="https://w.wallhaven.cc/full/ab/wallhaven-abc123.jpg"),
            patch(
                "wallhaven_downloader.core.download_image",
                return_value=DownloadResult(
                    wallpaper_id="abc123",
                    url="https://w.wallhaven.cc/full/ab/wallhaven-abc123.jpg",
                    path=Path("abc123.jpg"),
                ),
            ),
        ):
            results = download_wallpapers(
                "https://wallhaven.cc/hot",
                1,
                ".",
                max_workers=1,
                progress_callback=progress.append,
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(len(progress), 1)


if __name__ == "__main__":
    unittest.main()
