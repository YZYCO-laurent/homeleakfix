#!/usr/bin/env python3
"""Final technical and on-page SEO audit for the generated Hugo public directory."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urldefrag, unquote

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
BASE_URL = "https://homeleakfix.com"
HOST = "homeleakfix.com"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

CORE_STATIC_PATHS = {
    "/about/",
    "/contact/",
    "/privacy-policy/",
    "/terms/",
    "/disclaimer/",
    "/sitemap/",
}

EXPECTED_PRIORITY = {
    "home": "1.0",
    "article": "0.9",
    "category": "0.8",
    "category_index": "0.7",
    "article_index": "0.6",
    "core": "0.5",
}

EXPECTED_CHANGEFREQ = {
    "home": "weekly",
    "article": "monthly",
    "category": "weekly",
    "category_index": "weekly",
    "article_index": "weekly",
    "core": "yearly",
}


def rel_from_file(path: Path) -> str:
    rel = path.relative_to(PUBLIC).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def file_from_rel(rel: str) -> Path:
    rel = rel.split("?", 1)[0]
    rel = unquote(rel)
    if rel == "/":
        return PUBLIC / "index.html"
    if rel.endswith("/"):
        return PUBLIC / rel.lstrip("/") / "index.html"
    return PUBLIC / rel.lstrip("/")


def classify_path(path: str) -> str:
    if path == "/":
        return "home"
    if path == "/articles/":
        return "article_index"
    if path == "/categories/":
        return "category_index"
    if path.startswith("/articles/") and re.match(r"^/articles/[^/]+/$", path):
        return "article"
    if path.startswith("/categories/") and re.match(r"^/categories/[^/]+/$", path):
        return "category"
    if path in CORE_STATIC_PATHS:
        return "core"
    if path.startswith("/tags/") or path == "/tags/":
        return "tag"
    if "/page/" in path:
        return "pagination"
    return "other"


def parse_html(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")


def text_attr(soup: BeautifulSoup, selector: str, attr: str | None = None) -> str:
    el = soup.select_one(selector)
    if not el:
        return ""
    if attr:
        return (el.get(attr) or "").strip()
    return el.get_text(" ", strip=True)


def all_generated_html() -> list[Path]:
    return sorted(PUBLIC.rglob("*.html"))


def sitemap_urls() -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    p = PUBLIC / "sitemap.xml"
    if not p.exists():
        return [], ["missing sitemap.xml"]
    try:
        root = ET.parse(p).getroot()
    except Exception as exc:
        return [], [f"invalid sitemap XML: {exc}"]
    urls = []
    for url in root.findall("s:url", NS):
        item = {child.tag.split("}", 1)[-1]: (child.text or "") for child in url}
        urls.append(item)
    return urls, errors


def audit() -> dict:
    report: dict = {
        "summary": {},
        "technical_files": {},
        "sitemap": {},
        "robots": {},
        "llms": {},
        "on_page": {},
        "internal_links": {},
        "images": {},
        "schema": {},
        "findings": [],
        "warnings": [],
        "ready_for_gsc": False,
    }

    html_files = all_generated_html()
    path_to_file = {rel_from_file(p): p for p in html_files}
    report["summary"]["generated_html_files"] = len(html_files)
    report["summary"]["article_pages_generated"] = sum(1 for p in path_to_file if classify_path(p) == "article")
    report["summary"]["category_pages_generated"] = sum(1 for p in path_to_file if classify_path(p) == "category")
    report["summary"]["category_index_generated"] = sum(1 for p in path_to_file if classify_path(p) == "category_index")
    report["summary"]["tag_pages_generated"] = sum(1 for p in path_to_file if classify_path(p) == "tag")
    report["summary"]["pagination_pages_generated"] = sum(1 for p in path_to_file if classify_path(p) == "pagination")

    for name in ["sitemap.xml", "robots.txt", "llms.txt", "index.xml", "404.html"]:
        fp = PUBLIC / name
        report["technical_files"][name] = {"present": fp.exists(), "bytes": fp.stat().st_size if fp.exists() else 0}
        if not fp.exists():
            report["findings"].append(f"Missing generated technical file: /{name}")

    urls, sitemap_errors = sitemap_urls()
    sitemap_locs = [u.get("loc", "") for u in urls]
    sitemap_paths = []
    for loc in sitemap_locs:
        parsed = urlparse(loc)
        sitemap_paths.append(parsed.path or "/")
        if parsed.scheme != "https" or parsed.netloc != HOST:
            report["findings"].append(f"Sitemap URL is not canonical HTTPS host: {loc}")
    duplicates = [loc for loc, c in Counter(sitemap_locs).items() if c > 1]
    sitemap_type_counts = Counter(classify_path(p) for p in sitemap_paths)
    missing_html_from_sitemap = []
    for path in sitemap_paths:
        if path.endswith(".xml"):
            continue
        fp = file_from_rel(path)
        if not fp.exists():
            missing_html_from_sitemap.append(path)
    sitemap_html_paths = set(sitemap_paths)
    high_value_paths = {p for p in path_to_file if classify_path(p) in {"home", "article_index", "article", "category", "category_index", "core"}}
    missing_high_value = sorted(high_value_paths - sitemap_html_paths)
    low_value_in_sitemap = sorted(p for p in sitemap_paths if classify_path(p) in {"tag", "pagination", "other"})
    priority_issues = []
    changefreq_issues = []
    for u, path in zip(urls, sitemap_paths):
        kind = classify_path(path)
        if kind in EXPECTED_PRIORITY and u.get("priority") != EXPECTED_PRIORITY[kind]:
            priority_issues.append({"path": path, "actual": u.get("priority"), "expected": EXPECTED_PRIORITY[kind]})
        if kind in EXPECTED_CHANGEFREQ and u.get("changefreq") != EXPECTED_CHANGEFREQ[kind]:
            changefreq_issues.append({"path": path, "actual": u.get("changefreq"), "expected": EXPECTED_CHANGEFREQ[kind]})
    report["sitemap"] = {
        "valid_xml": not sitemap_errors,
        "errors": sitemap_errors,
        "url_count": len(urls),
        "type_counts": dict(sitemap_type_counts),
        "duplicate_url_count": len(duplicates),
        "duplicates_sample": duplicates[:20],
        "missing_html_count": len(missing_html_from_sitemap),
        "missing_html_sample": missing_html_from_sitemap[:20],
        "missing_high_value_count": len(missing_high_value),
        "missing_high_value_sample": missing_high_value[:20],
        "low_value_url_count": len(low_value_in_sitemap),
        "low_value_url_sample": low_value_in_sitemap[:30],
        "priority_issue_count": len(priority_issues),
        "priority_issue_sample": priority_issues[:20],
        "changefreq_issue_count": len(changefreq_issues),
        "changefreq_issue_sample": changefreq_issues[:20],
    }
    if report["summary"]["tag_pages_generated"]:
        report["findings"].append(f"Generated {report['summary']['tag_pages_generated']} tag archive pages; tag archives should stay disabled to preserve crawl budget")
    if sitemap_errors:
        report["findings"].extend(sitemap_errors)
    if duplicates:
        report["findings"].append(f"Sitemap contains {len(duplicates)} duplicate URLs")
    if missing_html_from_sitemap:
        report["findings"].append(f"Sitemap references {len(missing_html_from_sitemap)} missing HTML routes")
    if missing_high_value:
        report["findings"].append(f"Sitemap omits {len(missing_high_value)} high-value pages")
    if low_value_in_sitemap:
        report["findings"].append(f"Sitemap includes {len(low_value_in_sitemap)} low-value tag/pagination/other URLs")
    if priority_issues:
        report["findings"].append(f"Sitemap has {len(priority_issues)} priority values that do not follow the crawl-budget plan")
    if changefreq_issues:
        report["warnings"].append(f"Sitemap has {len(changefreq_issues)} changefreq values outside the preferred plan")

    robots_path = PUBLIC / "robots.txt"
    robots_text = robots_path.read_text(encoding="utf-8", errors="replace") if robots_path.exists() else ""
    required_robot_lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /*?*",
        f"Sitemap: {BASE_URL}/sitemap.xml",
    ]
    missing_robot_lines = [line for line in required_robot_lines if line not in robots_text]
    report["robots"] = {
        "bytes": len(robots_text.encode()),
        "has_user_agent": "User-agent: *" in robots_text,
        "has_sitemap": f"Sitemap: {BASE_URL}/sitemap.xml" in robots_text,
        "missing_required_lines": missing_robot_lines,
        "text": robots_text,
    }
    if missing_robot_lines:
        report["findings"].append(f"robots.txt missing required crawl-budget directives: {missing_robot_lines}")
    for blocked_noindex_path in ["Disallow: /tags/", "Disallow: /articles/page/"]:
        if blocked_noindex_path in robots_text:
            report["findings"].append(f"robots.txt blocks {blocked_noindex_path.split(': ', 1)[1]}, which can prevent crawlers from seeing noindex/404 cleanup signals")

    llms_path = PUBLIC / "llms.txt"
    llms_text = llms_path.read_text(encoding="utf-8", errors="replace") if llms_path.exists() else ""
    llms_checks = {
        "has_title": llms_text.startswith("# Home Leak Fix"),
        "mentions_articles_or_guides": bool(re.search(r"articles|guides|knowledge", llms_text, re.I)),
        "mentions_safety_or_professionals": bool(re.search(r"safety|qualified professional|professional", llms_text, re.I)),
        "has_canonical_domain_or_sitemap": (HOST in llms_text or "sitemap" in llms_text.lower()),
    }
    report["llms"] = {"bytes": len(llms_text.encode()), **llms_checks}
    for k, ok in llms_checks.items():
        if not ok:
            report["warnings"].append(f"llms.txt check not satisfied: {k}")

    title_missing = []
    title_long = []
    desc_missing = []
    desc_long = []
    canonical_missing = []
    canonical_mismatch = []
    robots_noindex_indexable = []
    h1_missing = []
    h1_multiple = []
    og_missing = []
    ga_missing = []
    article_schema_missing = []
    html_lang_missing = []
    root_article_pages = []
    noindex_tag_pages = []
    indexable_low_value_pages = []
    broken_links = []
    external_http_links = []
    broken_images = []
    missing_alt_images = []
    jsonld_errors = []
    schema_type_counts = Counter()

    for p in html_files:
        rel = rel_from_file(p)
        kind = classify_path(rel)
        soup = parse_html(p)
        if not soup.html or not soup.html.get("lang"):
            html_lang_missing.append(rel)
        title = text_attr(soup, "title")
        desc = text_attr(soup, 'meta[name="description"]', "content")
        canonical = text_attr(soup, 'link[rel="canonical"]', "href")
        meta_robots = text_attr(soup, 'meta[name="robots"]', "content").lower()
        h1s = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
        required_og = [
            'meta[property="og:title"]',
            'meta[property="og:description"]',
            'meta[property="og:url"]',
            'meta[property="og:type"]',
            'meta[property="og:image"]',
        ]
        if not title:
            title_missing.append(rel)
        elif len(title) > 70 and kind != "article":
            title_long.append({"path": rel, "length": len(title), "title": title})
        if not desc:
            desc_missing.append(rel)
        elif len(desc) > 170:
            desc_long.append({"path": rel, "length": len(desc), "description": desc})
        if not canonical:
            canonical_missing.append(rel)
        else:
            expected = BASE_URL + rel
            # Paginated archive pages are deliberately noindex/follow and may canonicalize to the parent archive.
            if canonical != expected and not (kind == "pagination" and canonical == f"{BASE_URL}/articles/"):
                canonical_mismatch.append({"path": rel, "actual": canonical, "expected": expected})
        if len(h1s) == 0 and rel != "/404.html":
            h1_missing.append(rel)
        if len(h1s) > 1:
            h1_multiple.append({"path": rel, "count": len(h1s), "h1s": h1s[:5]})
        missing_og_for_page = [sel for sel in required_og if not soup.select_one(sel)]
        if missing_og_for_page:
            og_missing.append({"path": rel, "missing": missing_og_for_page})
        if "G-487SJKQK0M" not in str(soup):
            ga_missing.append(rel)
        if kind in {"home", "article_index", "article", "category", "category_index", "core"} and "noindex" in meta_robots:
            robots_noindex_indexable.append(rel)
        if kind in {"tag", "pagination", "other"} and rel not in {"/404.html"} and "noindex" not in meta_robots:
            indexable_low_value_pages.append(rel)
        if kind == "tag" and "noindex" in meta_robots:
            noindex_tag_pages.append(rel)
        if kind == "other" and rel != "/sitemap/" and re.match(r"^/[^/]+/$", rel):
            # root-level article-like pages are crawl traps after /articles/ permalink fix.
            if rel not in CORE_STATIC_PATHS and rel not in {"/categories/", "/tags/", "/articles/"}:
                root_article_pages.append(rel)

        page_schema_types = Counter()

        def collect_schema_types(node):
            if isinstance(node, dict):
                typ = node.get("@type")
                if isinstance(typ, list):
                    for t in typ:
                        page_schema_types[str(t)] += 1
                        schema_type_counts[str(t)] += 1
                elif typ:
                    page_schema_types[str(typ)] += 1
                    schema_type_counts[str(typ)] += 1
                graph = node.get("@graph")
                if graph is not None:
                    collect_schema_types(graph)
            elif isinstance(node, list):
                for item in node:
                    collect_schema_types(item)

        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            data = script.string or script.get_text() or ""
            try:
                collect_schema_types(json.loads(data))
            except Exception as exc:
                jsonld_errors.append({"path": rel, "error": str(exc)})
        if kind == "article" and "Article" not in page_schema_types:
            article_schema_missing.append(rel)

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            parsed = urlparse(href)
            if parsed.scheme in {"http", "https"}:
                if parsed.netloc == HOST:
                    target_path = urldefrag(parsed.path or "/")[0]
                else:
                    if parsed.scheme == "http":
                        external_http_links.append({"from": rel, "href": href})
                    continue
            else:
                target_path = urldefrag(parsed.path or href)[0]
            if target_path.startswith("/"):
                target_file = file_from_rel(target_path)
                if not target_file.exists():
                    broken_links.append({"from": rel, "href": href, "resolved": target_path})
        for img in soup.find_all("img"):
            src = (img.get("src") or "").strip()
            if not src or src.startswith(("data:", "http://", "https://")):
                continue
            target_path = urlparse(src).path
            target_file = file_from_rel(target_path)
            if not target_file.exists():
                broken_images.append({"from": rel, "src": src})
            alt = img.get("alt")
            if alt is None or not alt.strip():
                missing_alt_images.append({"from": rel, "src": src})

    report["on_page"] = {
        "title_missing_count": len(title_missing),
        "title_missing_sample": title_missing[:30],
        "title_long_non_article_count": len(title_long),
        "title_long_non_article_sample": title_long[:20],
        "description_missing_count": len(desc_missing),
        "description_missing_sample": desc_missing[:30],
        "description_long_count": len(desc_long),
        "description_long_sample": desc_long[:20],
        "canonical_missing_count": len(canonical_missing),
        "canonical_missing_sample": canonical_missing[:30],
        "canonical_mismatch_count": len(canonical_mismatch),
        "canonical_mismatch_sample": canonical_mismatch[:20],
        "robots_noindex_on_high_value_count": len(robots_noindex_indexable),
        "robots_noindex_on_high_value_sample": robots_noindex_indexable[:30],
        "indexable_low_value_count": len(indexable_low_value_pages),
        "indexable_low_value_sample": indexable_low_value_pages[:30],
        "noindex_tag_page_count": len(noindex_tag_pages),
        "h1_missing_count": len(h1_missing),
        "h1_missing_sample": h1_missing[:30],
        "h1_multiple_count": len(h1_multiple),
        "h1_multiple_sample": h1_multiple[:20],
        "og_missing_count": len(og_missing),
        "og_missing_sample": og_missing[:20],
        "ga_missing_count": len(ga_missing),
        "ga_missing_sample": ga_missing[:20],
        "html_lang_missing_count": len(html_lang_missing),
        "html_lang_missing_sample": html_lang_missing[:20],
        "root_article_like_pages_count": len(root_article_pages),
        "root_article_like_pages_sample": root_article_pages[:20],
    }
    report["schema"] = {
        "jsonld_error_count": len(jsonld_errors),
        "jsonld_error_sample": jsonld_errors[:20],
        "article_schema_missing_count": len(article_schema_missing),
        "article_schema_missing_sample": article_schema_missing[:20],
        "schema_type_counts": dict(schema_type_counts),
    }
    report["internal_links"] = {
        "broken_internal_link_count": len(broken_links),
        "broken_internal_link_sample": broken_links[:30],
        "external_http_link_count": len(external_http_links),
        "external_http_link_sample": external_http_links[:20],
    }
    report["images"] = {
        "broken_image_count": len(broken_images),
        "broken_image_sample": broken_images[:30],
        "missing_alt_image_count": len(missing_alt_images),
        "missing_alt_image_sample": missing_alt_images[:30],
    }

    blocking_checks = [
        report["technical_files"]["sitemap.xml"]["present"],
        report["technical_files"]["robots.txt"]["present"],
        report["technical_files"]["llms.txt"]["present"],
        report["sitemap"]["valid_xml"],
        report["sitemap"]["duplicate_url_count"] == 0,
        report["sitemap"]["missing_html_count"] == 0,
        report["sitemap"]["missing_high_value_count"] == 0,
        report["sitemap"]["low_value_url_count"] == 0,
        report["sitemap"]["priority_issue_count"] == 0,
        len(missing_robot_lines) == 0,
        report["on_page"]["description_missing_count"] == 0,
        report["on_page"]["canonical_missing_count"] == 0,
        report["on_page"]["canonical_mismatch_count"] == 0,
        report["on_page"]["robots_noindex_on_high_value_count"] == 0,
        report["on_page"]["root_article_like_pages_count"] == 0,
        report["schema"]["jsonld_error_count"] == 0,
        report["schema"]["article_schema_missing_count"] == 0,
        report["internal_links"]["broken_internal_link_count"] == 0,
        report["images"]["broken_image_count"] == 0,
    ]
    report["ready_for_gsc"] = all(blocking_checks)
    return report


if __name__ == "__main__":
    result = audit()
    out = ROOT.parent / "final_seo_audit.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "ready_for_gsc": result["ready_for_gsc"],
        "findings": result["findings"],
        "warnings": result["warnings"],
        "summary": result["summary"],
        "sitemap": result["sitemap"],
        "robots": {k: v for k, v in result["robots"].items() if k != "text"},
        "on_page": result["on_page"],
        "schema": result["schema"],
        "internal_links": result["internal_links"],
        "images": result["images"],
    }, indent=2, ensure_ascii=False))
