from pathlib import Path
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
import json

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
BASE_URL = "https://homeleakfix.com"

html_files = sorted(PUBLIC.rglob("*.html"))
existing_files = {p.resolve() for p in PUBLIC.rglob("*") if p.is_file()}

def local_path_from_url(url: str, current_html: Path):
    if not url or url.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in {"homeleakfix.com", "www.homeleakfix.com"}:
        return None
    path = unquote(parsed.path or "")
    if not path:
        return None
    if path.startswith("/"):
        target = PUBLIC / path.lstrip("/")
    else:
        target = current_html.parent / path
    if path.endswith("/") or target.suffix == "":
        target = target / "index.html"
    return target.resolve()

def is_html_redirect(soup: BeautifulSoup) -> bool:
    refresh = soup.find("meta", attrs={"http-equiv": lambda v: v and v.lower() == "refresh"})
    return bool(refresh)

broken_links = []
broken_images = []
missing_canonical = []
missing_title = []
missing_desc = []
missing_og = []
jsonld_errors = []
redirect_pages = []

for html in html_files:
    rel = "/" + html.relative_to(PUBLIC).as_posix()
    soup = BeautifulSoup(html.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    if is_html_redirect(soup):
        redirect_pages.append(rel)
        continue
    if not soup.find("title") or not soup.find("title").get_text(strip=True):
        missing_title.append(rel)
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if not meta_desc or not meta_desc.get("content", "").strip():
        missing_desc.append(rel)
    if not soup.find("link", rel=lambda v: v and "canonical" in v):
        missing_canonical.append(rel)
    if not soup.find("meta", property="og:title") or not soup.find("meta", property="og:description"):
        missing_og.append(rel)
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        try:
            json.loads(raw)
        except Exception as e:
            jsonld_errors.append({"page": rel, "error": str(e)[:160]})
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        target = local_path_from_url(href, html)
        if target and target not in existing_files:
            broken_links.append({"page": rel, "href": href, "target": str(target.relative_to(PUBLIC) if PUBLIC in target.parents else target)})
    for tag, attr in [("img", "src"), ("meta", "content")]:
        for node in soup.find_all(tag):
            if tag == "meta" and node.get("property") not in {"og:image", "twitter:image"}:
                continue
            url = node.get(attr)
            target = local_path_from_url(url, html)
            if target and target not in existing_files:
                broken_images.append({"page": rel, "src": url, "target": str(target.relative_to(PUBLIC) if PUBLIC in target.parents else target)})

category_pages = sorted((PUBLIC / "categories").glob("*/index.html")) if (PUBLIC / "categories").exists() else []
category_summary = []
for p in category_pages:
    soup = BeautifulSoup(p.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    category_summary.append({
        "url": "/" + p.relative_to(PUBLIC).as_posix().replace("index.html", ""),
        "h1": soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "",
        "cards": len(soup.select(".article-card")),
        "eyebrow": soup.select_one(".eyebrow").get_text(" ", strip=True) if soup.select_one(".eyebrow") else "",
    })

root_exclusions = {"about", "contact", "privacy-policy", "terms", "disclaimer", "categories", "articles", "tags", "page", "css", "images", "sitemap"}
root_article_pages = [
    p for p in html_files
    if (p.parent / "index.html") == p and p.parent.parent == PUBLIC and p.parent.name not in root_exclusions
]
article_pages_under_articles = sorted((PUBLIC / "articles").glob("*/index.html")) if (PUBLIC / "articles").exists() else []
webp_images = sorted((PUBLIC / "images" / "uploads").glob("*.webp")) if (PUBLIC / "images" / "uploads").exists() else []

report = {
    "html_files": len(html_files),
    "redirect_pages": redirect_pages[:50],
    "redirect_page_count": len(redirect_pages),
    "article_pages_at_root": len(root_article_pages),
    "article_pages_under_articles": len(article_pages_under_articles),
    "category_pages": len(category_pages),
    "article_images_webp": len(webp_images),
    "broken_internal_links": broken_links[:200],
    "broken_internal_link_count": len(broken_links),
    "broken_images": broken_images[:200],
    "broken_image_count": len(broken_images),
    "missing_titles": missing_title,
    "missing_title_count": len(missing_title),
    "missing_descriptions": missing_desc,
    "missing_description_count": len(missing_desc),
    "missing_canonicals": missing_canonical,
    "missing_canonical_count": len(missing_canonical),
    "missing_og_pages": missing_og,
    "missing_og_count": len(missing_og),
    "jsonld_error_count": len(jsonld_errors),
    "jsonld_errors": jsonld_errors[:50],
    "category_summary": category_summary,
    "key_files": {
        "sitemap_xml": (PUBLIC / "sitemap.xml").exists(),
        "robots_txt": (PUBLIC / "robots.txt").exists(),
        "rss_index": (PUBLIC / "index.xml").exists(),
        "llms_txt": (PUBLIC / "llms.txt").exists(),
    }
}

out = ROOT.parent / "seo_link_image_audit.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2)[:12000])
print(f"\nFull audit saved to {out}")
if broken_links or broken_images or missing_canonical or missing_desc or missing_title or missing_og or jsonld_errors:
    raise SystemExit(1)
