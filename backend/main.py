from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from core.crawler import crawl_site
from core.parser import parse_page
from core.sitemap_finder import get_urls_from_sitemap # ÚJ import

app = FastAPI()

# CORS Middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    urls: list[str]

# 1. VÉGPONT: Feltérképezés (crawl)
@app.get("/crawl")
def start_crawl(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    urls_found = crawl_site(start_url=url, max_pages=100) 
    return {"urls": urls_found}

# 2. ÚJ VÉGPONT: Audit a Sitemap alapján
@app.get("/audit-from-sitemap")
def start_audit_from_sitemap(url: str):
    """
    Megkeresi a weboldal sitemap.xml fájlját és visszaadja a benne található URL-eket.
    """
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        urls_found = get_urls_from_sitemap(url)
        if not urls_found:
            raise HTTPException(status_code=404, detail="Nem található sitemap vagy nincsenek benne URL-ek.")
        return {"urls": urls_found}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a sitemap feldolgozása közben: {str(e)}")


# 3. VÉGPONT: Audit futtatása a kiválasztott listán
@app.post("/run-audit")
def run_audit_on_selection(request: AuditRequest):
    audit_results = []
    for page_url in request.urls:
        try:
            page_data = parse_page(url=page_url)
            audit_results.append(page_data)
        except Exception as e:
            audit_results.append({
                "url": page_url, "error": f"Elemzési hiba: {e}"
            })
    return {"pages_audited": len(audit_results), "results": audit_results}