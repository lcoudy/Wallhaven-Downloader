import unittest

from wallhaven_downloader.core import (
    build_search_url,
    extract_wallpaper_links,
    image_url_for,
    iter_page_urls,
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


if __name__ == "__main__":
    unittest.main()
