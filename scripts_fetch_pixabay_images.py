from pathlib import Path
import json
import os
import re
import time
from io import BytesIO

import requests
import yaml
from PIL import Image, ImageOps

ROOT = Path('/home/ubuntu/homeleakfix_work/homeleakfix')
CONTENT = ROOT / 'content/articles'
IMG_DIR = ROOT / 'static/images/uploads'
IMG_DIR.mkdir(parents=True, exist_ok=True)
KEY_FILE = Path(os.environ.get('PIXABAY_KEY_FILE', '/home/ubuntu/homeleakfix_work/.pixabay_key'))
API_KEY = KEY_FILE.read_text(encoding='utf-8').strip()

CATEGORY_QUERIES = {
    'Start Here': ['home inspection water damage', 'home waterproofing rain', 'house exterior maintenance'],
    'Flat Roof Leaks': ['flat roof repair', 'roof waterproofing', 'roof leak repair'],
    'Gutters & Downspouts': ['rain gutter', 'gutter downspout', 'roof drainage'],
    'Basements & Foundations': ['basement waterproofing', 'foundation wall', 'basement wall repair'],
    'Bathrooms & Wet Rooms': ['bathroom shower tiles', 'bathroom renovation waterproofing', 'tile grout shower'],
    'Windows, Doors & Walls': ['window rain', 'brick wall rain', 'exterior wall repair'],
    'Balconies & Exterior Concrete': ['concrete balcony', 'concrete patio repair', 'outdoor concrete'],
    'Sealants & Materials': ['caulking sealant', 'construction sealant', 'waterproof coating'],
    'Seasonal Prevention': ['home maintenance rain', 'autumn home maintenance', 'winter house roof'],
    'Emergency Repairs': ['roof leak rain', 'water leak repair', 'rain storm house'],
}

TITLE_KEYWORD_QUERIES = [
    ('gutter', 'rain gutter'), ('downspout', 'downspout'), ('flat roof', 'flat roof'),
    ('roof', 'roof repair'), ('basement', 'basement waterproofing'), ('foundation', 'foundation wall'),
    ('bathroom', 'bathroom tiles'), ('shower', 'shower tiles'), ('window', 'window rain'),
    ('door', 'front door rain'), ('balcony', 'balcony concrete'), ('concrete', 'concrete repair'),
    ('sealant', 'caulking sealant'), ('coating', 'waterproof coating'), ('mould', 'mold wall'),
    ('condensation', 'window condensation'), ('winter', 'winter house'), ('emergency', 'roof leak rain'),
]

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'HomeLeakFixImageFetcher/1.0'})

def front_matter(path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---'):
        return {}, text
    parts = text.split('---', 2)
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip('\n')
    return meta, body

def write_article(path, meta, body):
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).strip()
    path.write_text(f'---\n{fm}\n---\n\n{body}', encoding='utf-8')

def pixabay_search(query, page=1, per_page=60):
    params = {
        'key': API_KEY,
        'q': query,
        'image_type': 'photo',
        'orientation': 'horizontal',
        'safesearch': 'true',
        'per_page': per_page,
        'page': page,
        'min_width': 900,
        'min_height': 500,
        'order': 'popular',
    }
    r = SESSION.get('https://pixabay.com/api/', params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get('hits', [])

def build_pools():
    pools = {}
    credits = {}
    for cat, queries in CATEGORY_QUERIES.items():
        seen = set()
        pool = []
        for q in queries:
            for page in range(1, 4):
                try:
                    hits = pixabay_search(q, page=page, per_page=40)
                except Exception as exc:
                    print(f'Warning: Pixabay search failed for {cat}/{q}/page {page}: {exc}')
                    continue
                for h in hits:
                    pid = h.get('id')
                    if not pid or pid in seen:
                        continue
                    seen.add(pid)
                    pool.append(h)
                    credits[str(pid)] = {
                        'pixabay_id': pid,
                        'page_url': h.get('pageURL'),
                        'user': h.get('user'),
                        'tags': h.get('tags'),
                    }
                time.sleep(0.08)
        pools[cat] = pool
        print(f'{cat}: collected {len(pool)} candidate images')
    return pools, credits

def pick_query(title, category):
    text = title.lower()
    for needle, query in TITLE_KEYWORD_QUERIES:
        if needle in text:
            return query
    return CATEGORY_QUERIES.get(category, ['home repair'])[0]

def relevance_score(hit, title, query):
    hay = f"{hit.get('tags','')} {query}".lower()
    words = [w for w in re.split(r'[^a-z0-9]+', title.lower()) if len(w) > 3]
    score = 0
    for w in words:
        if w in hay:
            score += 2
    for w in re.split(r'[^a-z0-9]+', query.lower()):
        if len(w) > 2 and w in hay:
            score += 3
    score += int(hit.get('likes') or 0) / 500
    score += int(hit.get('downloads') or 0) / 50000
    return score

def make_alt(title, category):
    title = re.sub(r'\s+', ' ', title).strip()
    return f'{title} — {category.lower()} repair and waterproofing guidance'

def save_webp(hit, slug):
    url = hit.get('largeImageURL') or hit.get('webformatURL')
    if not url:
        raise ValueError('hit has no downloadable image URL')
    r = SESSION.get(url, timeout=45)
    r.raise_for_status()
    image = Image.open(BytesIO(r.content)).convert('RGB')
    image = ImageOps.exif_transpose(image)
    target = (1200, 675)
    src_ratio = image.width / image.height
    dst_ratio = target[0] / target[1]
    if src_ratio > dst_ratio:
        new_h = image.height
        new_w = int(new_h * dst_ratio)
        left = (image.width - new_w) // 2
        image = image.crop((left, 0, left + new_w, image.height))
    else:
        new_w = image.width
        new_h = int(new_w / dst_ratio)
        top = max(0, (image.height - new_h) // 2)
        image = image.crop((0, top, image.width, top + new_h))
    image = image.resize(target, Image.Resampling.LANCZOS)
    out = IMG_DIR / f'{slug}.webp'
    image.save(out, 'WEBP', quality=78, method=6)
    return out

def main():
    articles = []
    for path in sorted(CONTENT.glob('*.md')):
        if path.name == '_index.md':
            continue
        meta, body = front_matter(path)
        if not meta.get('categories'):
            continue
        articles.append((path, meta, body))
    pools, credits_by_id = build_pools()
    used = set()
    image_report = []
    for idx, (path, meta, body) in enumerate(articles, start=1):
        category = meta['categories'][0]
        title = meta['title']
        slug = meta.get('slug') or path.stem
        specific_query = pick_query(title, category)
        candidates = list(pools.get(category, []))
        # Promote images whose Pixabay tags align with the article title/query.
        candidates.sort(key=lambda h: relevance_score(h, title, specific_query), reverse=True)
        chosen = None
        for h in candidates:
            if h.get('id') not in used:
                chosen = h
                break
        # If a category pool has been exhausted, request a targeted fallback page.
        if chosen is None:
            try:
                for h in pixabay_search(specific_query, page=1, per_page=60):
                    if h.get('id') not in used:
                        chosen = h
                        break
            except Exception as exc:
                print(f'Warning: fallback search failed for {slug}: {exc}')
        if chosen is None:
            print(f'No image found for {slug}; leaving default image')
            continue
        try:
            out = save_webp(chosen, slug)
        except Exception as exc:
            print(f'Warning: download/optimization failed for {slug}: {exc}')
            continue
        pid = chosen.get('id')
        used.add(pid)
        meta['image'] = f'/images/uploads/{out.name}'
        meta['image_alt'] = make_alt(title, category)
        meta['pixabay_id'] = pid
        meta['pixabay_tags'] = chosen.get('tags', '')
        write_article(path, meta, body)
        image_report.append({
            'slug': slug,
            'title': title,
            'category': category,
            'image': meta['image'],
            'pixabay_id': pid,
            'pixabay_user': chosen.get('user'),
            'pixabay_page_url': chosen.get('pageURL'),
            'tags': chosen.get('tags'),
        })
        print(f'[{idx}/{len(articles)}] {slug} -> {out.name}')
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/pixabay_image_credits.json').write_text(json.dumps(image_report, indent=2, ensure_ascii=False), encoding='utf-8')
    report_lines = ['# Pixabay Image Assignment Report', '', f'Assigned {len(image_report)} unique Pixabay images to {len(articles)} articles.', '', '| Category | Images |', '|---|---:|']
    from collections import Counter
    counts = Counter(item['category'] for item in image_report)
    for cat, count in counts.most_common():
        report_lines.append(f'| {cat} | {count} |')
    report_lines += ['', '## Credits', '', '| Slug | Pixabay ID | User | Tags |', '|---|---:|---|---|']
    for item in image_report:
        report_lines.append(f"| `{item['slug']}` | {item['pixabay_id']} | {item.get('pixabay_user') or ''} | {item.get('tags') or ''} |")
    Path('/home/ubuntu/homeleakfix_work/image_assignment_report.md').write_text('\n'.join(report_lines) + '\n', encoding='utf-8')
    print(f'Assigned {len(image_report)} unique images.')

if __name__ == '__main__':
    main()
