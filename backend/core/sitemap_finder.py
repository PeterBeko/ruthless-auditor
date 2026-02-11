import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin

# ÚJ: Standard böngésző fejléc az álcázáshoz
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def _parse_sitemap(sitemap_url: str) -> list[str]:
    try:
        # MÓDOSÍTVA: headers=HEADERS hozzáadva
        response = requests.get(sitemap_url, timeout=10, headers=HEADERS)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        namespace = ''
        if '}' in root.tag:
            namespace = root.tag.split('}')[0][1:]
        urls = []
        for sitemap in root.findall(f'{{{namespace}}}sitemap'):
            loc = sitemap.find(f'{{{namespace}}}loc')
            if loc is not None and loc.text:
                urls.extend(_parse_sitemap(loc.text))
        for url_element in root.findall(f'{{{namespace}}}url'):
            loc = url_element.find(f'{{{namespace}}}loc')
            if loc is not None and loc.text:
                urls.append(loc.text)
        return list(set(urls))
    except (requests.RequestException, ET.ParseError):
        return []

def get_urls_from_sitemap(base_url: str) -> list[str]:
    parsed_url = urlparse(base_url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    sitemap_url = urljoin(domain, '/sitemap.xml')
    urls = _parse_sitemap(sitemap_url)
    if urls:
        return urls
    try:
        robots_url = urljoin(domain, '/robots.txt')
        # MÓDOSÍTVA: headers=HEADERS hozzáadva
        response = requests.get(robots_url, timeout=5, headers=HEADERS)
        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.lower().startswith('sitemap:'):
                    sitemap_url_from_robots = line.split(':', 1)[1].strip()
                    urls = _parse_sitemap(sitemap_url_from_robots)
                    if urls:
                        return urls
    except requests.RequestException:
        pass
    return []