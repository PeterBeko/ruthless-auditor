import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchFrameException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def setup_driver():
    """Initializes a headless Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def _parse_source(page_source: str) -> dict:
    """Helper function to parse HTML source and extract SEO data."""
    soup = BeautifulSoup(page_source, 'lxml')
    title = soup.find('title').get_text(strip=True) if soup.find('title') else ''
    meta_description_tag = soup.find('meta', attrs={'name': 'description'})
    meta_description = meta_description_tag['content'] if meta_description_tag and 'content' in meta_description_tag.attrs else ''
    h1_tags = soup.find_all('h1')
    h1_count = len(h1_tags)
    h1_text = h1_tags[0].get_text(strip=True) if h1_count > 0 else ''
    word_count = len(soup.get_text().split())
    images = soup.find_all('img')
    images_missing_alt = sum(1 for img in images if not img.get('alt', '').strip())
    return {
        "title": title, "meta_description": meta_description, "h1_text": h1_text,
        "h1_count": h1_count, "word_count": word_count, "image_count": len(images),
        "images_missing_alt": images_missing_alt
    }

def parse_page(url: str) -> dict:
    """
    Fetches a URL, intelligently checks for content within iframes, and parses SEO data.
    """
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 1. Elemzés a fő oldalon
        main_page_source = driver.page_source
        main_results = _parse_source(main_page_source)
        
        # 2. ÚJ LOGIKA: iframe keresése és elemzése, ha van 'src' attribútuma
        iframe_results = None
        try:
            # Megkeressük az összes iframe-et
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            
            # Végigmegyünk rajtuk, és az elsőt, aminek van 'src' attribútuma, elemezzük
            candidate_iframe = None
            for frame in iframes:
                if frame.get_attribute('src'):
                    candidate_iframe = frame
                    break # Megvan az első jelölt, kilépünk a ciklusból
            
            if candidate_iframe:
                driver.switch_to.frame(candidate_iframe)
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                iframe_source = driver.page_source
                iframe_results = _parse_source(iframe_source)

        except (NoSuchFrameException, TimeoutException):
            # Ha az iframe elemzése sikertelen, az iframe_results None marad, ami nem okoz problémát
            pass
        finally:
            # Mindig visszaváltunk a fő tartalomra, hogy a driver.quit() tiszta állapotban fusson le
            driver.switch_to.default_content()

        # 3. Döntés: A több tartalmat tartalmazó eredményt adjuk vissza
        if iframe_results and iframe_results['word_count'] > main_results['word_count']:
            final_results = iframe_results
        else:
            final_results = main_results

        final_results['url'] = url
        final_results['status_code'] = 200
        return final_results

    except TimeoutException:
        return {"url": url, "error": "Page load timed out."}
    except (WebDriverException, requests.RequestException) as e:
        return {"url": url, "error": str(e)}
    finally:
        if driver:
            driver.quit()