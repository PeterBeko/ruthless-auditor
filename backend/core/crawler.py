import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque

LANGUAGE_PREFIXES = ['/en/', '/de/']

# ÚJ: Standard böngésző fejléc az álcázáshoz
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def crawl_site(start_url: str, max_pages: int = 100) -> list:
    parsed_start_url = urlparse(start_url)
    start_url_netloc = parsed_start_url.netloc
    clean_start_url = urlunparse(parsed_start_url._replace(fragment=""))
    is_starting_from_root = parsed_start_url.path in ('', '/')
    pages_to_visit = deque([clean_start_url])
    visited_urls = {clean_start_url}

    while pages_to_visit and len(visited_urls) < max_pages:
        current_url = pages_to_visit.popleft()
        try:
            # MÓDOSÍTVA: headers=HEADERS hozzáadva
            response = requests.get(current_url, timeout=10, headers=HEADERS)
            response.raise_for_status()
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue
            soup = BeautifulSoup(response.text, 'lxml')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_link = urljoin(current_url, href)
                parsed_link = urlparse(absolute_link)
                clean_link = urlunparse(parsed_link._replace(fragment=""))
                is_internal = parsed_link.netloc == start_url_netloc
                is_new = clean_link not in visited_urls
                is_html = not any(clean_link.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.mp4', '.xml', '.svg'])
                if not (is_internal and is_new and is_html):
                    continue
                if is_starting_from_root:
                    link_path = parsed_link.path
                    if any(link_path.startswith(prefix) for prefix in LANGUAGE_PREFIXES):
                        continue
                if len(visited_urls) < max_pages:
                    visited_urls.add(clean_link)
                    pages_to_visit.append(clean_link)
        except requests.RequestException:
            continue
    return list(visited_urls)