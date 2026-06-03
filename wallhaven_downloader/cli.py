from __future__ import annotations

import argparse
from pathlib import Path

from wallhaven_downloader.core import DEFAULT_MAX_WORKERS, download_from_search, download_wallpapers


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.url:
        results = download_wallpapers(
            args.url,
            args.pages,
            args.output,
            max_workers=args.workers,
            overwrite=args.overwrite,
        )
    else:
        results = download_from_search(
            output_dir=args.output,
            sorting=args.sorting,
            top_range=args.top_range,
            purity=args.purity,
            categories=args.categories,
            start_page=args.start_page,
            page_count=args.pages,
            max_workers=args.workers,
        )

    print_summary(results)
    return 1 if any(item.error for item in results) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download wallpapers from Wallhaven.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Download directory.")
    parser.add_argument("--url", help="Wallhaven listing URL. If omitted, search options are used.")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to download.")
    parser.add_argument("--workers", type=int, default=DEFAULT_MAX_WORKERS, help="Concurrent download workers.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--sorting", default="toplist", choices=["date_added", "toplist", "favorites", "views", "hot", "random"])
    parser.add_argument("--top-range", default="1M", choices=["1d", "1w", "1M", "3M", "6M", "1y"])
    parser.add_argument("--purity", default="110", help="Wallhaven purity bits, for example 110.")
    parser.add_argument("--categories", default="110", help="Wallhaven category bits, for example 110.")
    parser.add_argument("--start-page", type=int, default=1, help="Search start page.")
    return parser


def print_summary(results) -> None:
    downloaded = sum(1 for item in results if not item.skipped and item.error is None)
    skipped = sum(1 for item in results if item.skipped)
    failed = [item for item in results if item.error is not None]
    print(f"Downloaded: {downloaded}, skipped: {skipped}, failed: {len(failed)}")
    for item in failed:
        print(f"Failed {item.wallpaper_id}: {item.error}")


if __name__ == "__main__":
    raise SystemExit(main())
