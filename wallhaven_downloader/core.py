from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    ),
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/81.0.4389.90 Safari/531.36"
    ),
}

DEFAULT_PAGE_TIMEOUT = 20
DEFAULT_DOWNLOAD_TIMEOUT = 30
DEFAULT_RETRIES = 6
DEFAULT_RETRY_DELAY = 2.0
DEFAULT_MAX_WORKERS = 2
DEFAULT_FAILED_RETRY_ROUNDS = 1
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class DownloadResult:
    wallpaper_id: str
    url: str
    path: Path
    skipped: bool = False
    error: str | None = None


ProgressCallback = Callable[[DownloadResult], None]


def build_headers() -> dict[str, str]:
    headers = dict(DEFAULT_HEADERS)
    wallhaven_cookie = os.getenv("WALLHAVEN_COOKIE")
    if wallhaven_cookie:
        headers["Cookie"] = wallhaven_cookie
    return headers


def build_search_url(
    sorting: str,
    top_range: str,
    purity: str = "110",
    categories: str = "110",
    start_page: int = 1,
) -> str:
    query = {
        "categories": categories,
        "purity": purity,
        "topRange": top_range,
        "sorting": sorting,
        "order": "desc",
        "page": str(start_page),
    }
    return "https://wallhaven.cc/search?" + urlencode(query)


def iter_page_urls(url: str, page_count: int) -> list[str]:
    if page_count < 1:
        return []

    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    page_index = next((idx for idx, item in enumerate(query) if item[0] == "page"), None)
    if page_index is None:
        start_page = 1
    else:
        try:
            start_page = int(query[page_index][1])
        except ValueError:
            start_page = 1

    urls = []
    for offset in range(page_count):
        page = start_page + offset
        if page_index is None and page == 1:
            urls.append(url)
            continue

        next_query = list(query)
        if page_index is None:
            next_query.append(("page", str(page)))
        else:
            next_query[page_index] = ("page", str(page))
        urls.append(urlunsplit(parts._replace(query=urlencode(next_query))))
    return urls


def extract_wallpaper_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    listing = soup.find("section", class_="thumb-listing-page")
    if listing is None:
        return []

    links = []
    for item in listing.find_all("li"):
        anchor = item.find("a", href=True)
        if anchor is not None:
            links.append(str(anchor["href"]))
    return links


def wallpaper_id_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def image_url_for(wallpaper_id: str, extension: str = "jpg") -> str:
    extension = extension.lstrip(".")
    return f"https://w.wallhaven.cc/full/{wallpaper_id[:2]}/wallhaven-{wallpaper_id}.{extension}"


def resolve_image_url(session: requests.Session, wallpaper_id: str, timeout: float = 15) -> str:
    jpg_url = image_url_for(wallpaper_id, "jpg")
    try:
        response = request_with_retries(
            session,
            "HEAD",
            jpg_url,
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return jpg_url

    if response.status_code != 404:
        return jpg_url
    return image_url_for(wallpaper_id, "png")


def fetch_wallpaper_links(
    url: str,
    page_count: int,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_PAGE_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> list[str]:
    session = requests.Session()
    session.headers.update(headers or build_headers())
    links: list[str] = []
    try:
        for page_url in iter_page_urls(url, page_count):
            response = request_with_retries(session, "GET", page_url, timeout=timeout, retries=retries)
            response.encoding = "utf-8"
            response.raise_for_status()
            links.extend(extract_wallpaper_links(response.text))
    finally:
        session.close()
    return dedupe(links)


def download_image(
    url: str,
    wallpaper_id: str,
    output_dir: str | Path,
    headers: dict[str, str] | None = None,
    overwrite: bool = False,
    timeout: float = DEFAULT_DOWNLOAD_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> DownloadResult:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(urlsplit(url).path).suffix or ".jpg"
    target_path = target_dir / f"{wallpaper_id}{extension}"

    if target_path.exists() and not overwrite:
        return DownloadResult(wallpaper_id, url, target_path, skipped=True)

    try:
        response = request_with_retries(
            requests,
            "GET",
            url,
            headers=headers or build_headers(),
            timeout=timeout,
            retries=retries,
        )
        response.raise_for_status()
        target_path.write_bytes(response.content)
    except Exception as exc:
        return DownloadResult(wallpaper_id, url, target_path, error=str(exc))

    return DownloadResult(wallpaper_id, url, target_path)


def download_wallpapers(
    url: str,
    page_count: int,
    output_dir: str | Path,
    max_workers: int = DEFAULT_MAX_WORKERS,
    overwrite: bool = False,
    progress_callback: ProgressCallback | None = None,
    failed_retry_rounds: int = DEFAULT_FAILED_RETRY_ROUNDS,
    write_failure_report_file: bool = True,
) -> list[DownloadResult]:
    headers = build_headers()
    links = fetch_wallpaper_links(url, page_count, headers=headers)
    if not links:
        return []

    def download_one(link: str) -> DownloadResult:
        wallpaper_id = wallpaper_id_from_url(link)
        session = requests.Session()
        session.headers.update(headers)
        try:
            image_url = resolve_image_url(session, wallpaper_id)
        finally:
            session.close()
        result = download_image(image_url, wallpaper_id, output_dir, headers=headers, overwrite=overwrite)
        if result.error and "404" in result.error and image_url.endswith(".jpg"):
            png_url = image_url_for(wallpaper_id, "png")
            return download_image(png_url, wallpaper_id, output_dir, headers=headers, overwrite=overwrite)
        return result

    results_by_id: dict[str, DownloadResult] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_one, link) for link in links]
        for future in as_completed(futures):
            result = future.result()
            results_by_id[result.wallpaper_id] = result
            if progress_callback is not None:
                progress_callback(result)

    for _ in range(failed_retry_rounds):
        failed_links = [
            link for link in links
            if (results_by_id.get(wallpaper_id_from_url(link)) is not None
                and results_by_id[wallpaper_id_from_url(link)].error is not None)
        ]
        if not failed_links:
            break
        time.sleep(DEFAULT_RETRY_DELAY * 2)
        for link in failed_links:
            result = download_one(link)
            results_by_id[result.wallpaper_id] = result
            if progress_callback is not None:
                progress_callback(result)

    results = [results_by_id[wallpaper_id_from_url(link)] for link in links if wallpaper_id_from_url(link) in results_by_id]
    if write_failure_report_file:
        write_failure_report(output_dir, results)
    return results


def download_from_search(
    output_dir: str | Path,
    sorting: str,
    top_range: str,
    purity: str = "110",
    categories: str = "110",
    start_page: int = 1,
    page_count: int = 1,
    max_workers: int = DEFAULT_MAX_WORKERS,
    progress_callback: ProgressCallback | None = None,
) -> list[DownloadResult]:
    url = build_search_url(
        sorting=sorting,
        top_range=top_range,
        purity=purity,
        categories=categories,
        start_page=start_page,
    )
    return download_wallpapers(
        url,
        page_count,
        output_dir,
        max_workers=max_workers,
        progress_callback=progress_callback,
    )


def request_with_retries(
    client,
    method: str,
    url: str,
    retries: int = DEFAULT_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    **kwargs,
) -> requests.Response:
    last_error: requests.RequestException | None = None
    for attempt in range(retries + 1):
        try:
            response = client.request(method, url, **kwargs)
            if response.status_code not in RETRY_STATUS_CODES or attempt >= retries:
                return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt >= retries:
                raise

        time.sleep(retry_delay * (attempt + 1))

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Request failed after {retries + 1} attempts: {url}")


def write_failure_report(output_dir: str | Path, results: Iterable[DownloadResult]) -> Path | None:
    failed = [item for item in results if item.error is not None]
    if not failed:
        return None

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    report_path = target_dir / "download_failures.txt"
    lines = ["wallpaper_id\turl\terror"]
    for item in failed:
        lines.append(f"{item.wallpaper_id}\t{item.url}\t{item.error}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def dedupe(values: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
