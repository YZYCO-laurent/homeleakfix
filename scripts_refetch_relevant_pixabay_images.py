from pathlib import Path
import json
import os
import re
import time
from io import BytesIO
from collections import Counter

import requests
import yaml
from PIL import Image, ImageOps

ROOT = Path('/home/ubuntu/homeleakfix_work/homeleakfix')
CONTENT = ROOT / 'content/articles'
IMG_DIR = ROOT / 'static/images/uploads'
IMG_DIR.mkdir(parents=True, exist_ok=True)
KEY_FILE = Path(os.environ.get('PIXABAY_KEY_FILE', '/home/ubuntu/homeleakfix_work/.pixabay_key'))
API_KEY = KEY_FILE.read_text(encoding='utf-8').strip()

NEGATIVE_WORDS = {
    'portrait','woman','man','girl','boy','fashion','beauty','makeup','model','person','people','child','kid','baby',
    'music','guitar','instrument','car','automotive','motorcycle','scooter','beetle','food','animal','dog','cat',
    'flower','beach','wedding','computer','phone','app','ux','business','coffee','depression','sad','bench'
}

CATEGORY_RULES = {
    'Start Here': {
        'queries': ['house exterior rain', 'home inspection house', 'water damage house', 'house roof rain'],
        'positive': {'house','home','roof','rain','water','building','exterior','architecture','window','wall','facade'}
    },
    'Flat Roof Leaks': {
        'queries': ['roof repair house', 'roof waterproofing', 'roof construction', 'rooftop building', 'house roof rain'],
        'positive': {'roof','roofing','rooftop','house','home','building','construction','architecture','rain','storm','water'}
    },
    'Gutters & Downspouts': {
        'queries': ['rain gutter house', 'gutter downspout', 'roof gutter', 'rainwater pipe house', 'house roof drainage'],
        'positive': {'gutter','gutters','downspout','pipe','roof','rain','water','house','home','drain','drainage'}
    },
    'Basements & Foundations': {
        'queries': ['basement wall', 'cellar wall', 'foundation concrete', 'concrete crack wall', 'water damage wall'],
        'positive': {'basement','cellar','foundation','concrete','wall','crack','water','damp','moisture','brick','stone'}
    },
    'Bathrooms & Wet Rooms': {
        'queries': ['bathroom tiles', 'shower bathroom', 'bathroom renovation', 'tile grout bathroom', 'plumbing bathroom'],
        'positive': {'bathroom','shower','tile','tiles','grout','bathtub','bath','plumbing','sink','water','renovation'}
    },
    'Windows, Doors & Walls': {
        'queries': ['window rain house', 'house exterior wall', 'brick wall rain', 'front door rain', 'window frame house'],
        'positive': {'window','door','wall','brick','house','home','rain','exterior','facade','masonry','building','water'}
    },
    'Balconies & Exterior Concrete': {
        'queries': ['balcony concrete', 'concrete patio', 'terrace balcony', 'outdoor concrete', 'concrete crack'],
        'positive': {'balcony','terrace','concrete','patio','outdoor','wall','crack','stone','brick','pavement','building'}
    },
    'Sealants & Materials': {
        'queries': ['caulking gun', 'construction tools', 'paint roller wall', 'waterproof coating', 'adhesive construction'],
        'positive': {'tool','tools','caulk','caulking','sealant','silicone','paint','coating','construction','repair','wall','brush','roller','adhesive','material'}
    },
    'Seasonal Prevention': {
        'queries': ['house rain storm', 'winter house roof', 'autumn house leaves', 'snow roof house', 'home maintenance tools'],
        'positive': {'house','home','roof','rain','storm','winter','snow','autumn','leaves','water','weather','tools','maintenance'}
    },
    'Emergency Repairs': {
        'queries': ['water leak plumbing', 'storm house rain', 'roof leak rain', 'emergency repair tools', 'water damage house'],
        'positive': {'water','leak','plumbing','rain','storm','roof','house','repair','tools','pipe','damage','flood'}
    },
}

TITLE_HINTS = [
    ('gutter', ['rain gutter house','roof gutter','gutter downspout']),
    ('downspout', ['gutter downspout','rainwater pipe house']),
    ('flat roof', ['roof repair house','rooftop building','roof waterproofing']),
    ('roof', ['roof repair house','house roof rain','roof construction']),
    ('basement', ['basement wall','cellar wall','water damage wall']),
    ('foundation', ['foundation concrete','concrete foundation wall']),
    ('bathroom', ['bathroom tiles','bathroom renovation','shower bathroom']),
    ('shower', ['shower bathroom','tile grout bathroom']),
    ('wet room', ['bathroom tiles','shower bathroom']),
    ('window', ['window rain house','window frame house']),
    ('door', ['front door rain','house door']),
    ('wall', ['house exterior wall','brick wall rain','water damage wall']),
    ('balcony', ['balcony concrete','terrace balcony']),
    ('terrace', ['terrace balcony','concrete patio']),
    ('concrete', ['concrete crack','outdoor concrete']),
    ('sealant', ['caulking gun','construction sealant','construction tools']),
    ('silicone', ['caulking gun','bathroom silicone']),
    ('coating', ['paint roller wall','waterproof coating']),
    ('bitumen', ['roof repair house','waterproof coating']),
    ('membrane', ['roof waterproofing','construction roof']),
    ('mould', ['water damage wall','damp wall']),
    ('condensation', ['window condensation','window rain house']),
    ('winter', ['winter house roof','snow roof house']),
    ('frost', ['winter house roof','snow concrete']),
    ('storm', ['storm house rain','house rain storm']),
    ('emergency', ['water leak plumbing','emergency repair tools']),
]

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'HomeLeakFixRelevantImageFetcher/2.0'})
CACHE = {}


def front_matter(path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---'):
        return {}, text
    parts = text.split('---', 2)
    return yaml.safe_load(parts[1]) or {}, parts[2].lstrip('\n')


def write_article(path, meta, body):
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).strip()
    path.write_text(f'---\n{fm}\n---\n\n{body}', encoding='utf-8')


def pixabay_search(query, page=1, per_page=60):
    key = (query, page, per_page)
    if key in CACHE:
        return CACHE[key]
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
    hits = r.json().get('hits', [])
    CACHE[key] = hits
    time.sleep(0.04)
    return hits


def words(text):
    return [w for w in re.split(r'[^a-z0-9]+', (text or '').lower()) if len(w) > 2]


def article_queries(title, category):
    title_l = title.lower()
    qs = []
    for needle, query_list in TITLE_HINTS:
        if needle in title_l:
            qs.extend(query_list)
    qs.extend(CATEGORY_RULES[category]['queries'])
    seen = []
    for q in qs:
        if q not in seen:
            seen.append(q)
    return seen[:7]


def relevance_score(hit, title, category):
    tag_words = set(words(hit.get('tags', '')))
    rule = CATEGORY_RULES[category]
    positive = rule['positive']
    negative_hits = tag_words & NEGATIVE_WORDS
    positive_hits = tag_words & positive
    if not positive_hits:
        return -9999
    score = 12 * len(positive_hits) - 18 * len(negative_hits)
    for w in words(title):
        if w in tag_words:
            score += 4
    score += min(int(hit.get('likes') or 0), 500) / 100
    score += min(int(hit.get('downloads') or 0), 50000) / 10000
    # Prefer images with a clear home/building/material context over generic backgrounds.
    if {'house','home','roof','gutter','bathroom','window','door','concrete','wall','tool','tools'} & tag_words:
        score += 8
    return score


def collect_candidates(title, category):
    candidates = {}
    for query in article_queries(title, category):
        for page in (1, 2):
            try:
                for hit in pixabay_search(query, page=page, per_page=40):
                    pid = hit.get('id')
                    if pid:
                        candidates[pid] = hit
            except Exception as exc:
                print(f'Warning: Pixabay search failed for {query}/page {page}: {exc}')
    scored = sorted(candidates.values(), key=lambda h: relevance_score(h, title, category), reverse=True)
    return [h for h in scored if relevance_score(h, title, category) > -9999]


def make_alt(title, category):
    clean_title = re.sub(r'\s+', ' ', title).strip()
    return f'{clean_title} — {category.lower()} repair and waterproofing guidance'


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
    image.save(out, 'WEBP', quality=80, method=6)
    return out


def main():
    articles = []
    for path in sorted(CONTENT.glob('*.md')):
        if path.name == '_index.md':
            continue
        meta, body = front_matter(path)
        if meta.get('categories'):
            articles.append((path, meta, body))

    used = set()
    report = []
    weak = []
    for idx, (path, meta, body) in enumerate(articles, 1):
        category = meta['categories'][0]
        title = meta['title']
        slug = meta.get('slug') or path.stem
        candidates = collect_candidates(title, category)
        chosen = None
        for h in candidates:
            if h.get('id') not in used:
                chosen = h
                break
        if chosen is None:
            weak.append(slug)
            print(f'No filtered image found for {slug}; keeping existing image')
            continue
        try:
            out = save_webp(chosen, slug)
        except Exception as exc:
            weak.append(slug)
            print(f'Warning: download failed for {slug}: {exc}')
            continue
        used.add(chosen.get('id'))
        meta['image'] = f'/images/uploads/{out.name}'
        meta['image_alt'] = make_alt(title, category)
        meta['pixabay_id'] = chosen.get('id')
        meta['pixabay_tags'] = chosen.get('tags', '')
        write_article(path, meta, body)
        score = round(relevance_score(chosen, title, category), 2)
        report.append({
            'slug': slug,
            'title': title,
            'category': category,
            'image': meta['image'],
            'pixabay_id': chosen.get('id'),
            'pixabay_user': chosen.get('user'),
            'pixabay_page_url': chosen.get('pageURL'),
            'tags': chosen.get('tags'),
            'score': score,
        })
        print(f'[{idx}/{len(articles)}] {slug} -> {out.name} (score {score}, tags: {chosen.get("tags")})')

    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/pixabay_image_credits.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = ['# Relevant Pixabay Image Assignment Report', '', f'Assigned {len(report)} unique filtered Pixabay images to {len(articles)} articles.', f'Unchanged or weak assignments: {len(weak)}', '', '| Category | Images |', '|---|---:|']
    counts = Counter(item['category'] for item in report)
    for cat, count in counts.most_common():
        lines.append(f'| {cat} | {count} |')
    lines += ['', '## Credits', '', '| Slug | Pixabay ID | Score | User | Tags |', '|---|---:|---:|---|---|']
    for item in report:
        lines.append(f"| `{item['slug']}` | {item['pixabay_id']} | {item['score']} | {item.get('pixabay_user') or ''} | {item.get('tags') or ''} |")
    if weak:
        lines += ['', '## Weak or unchanged assignments', ''] + [f'- `{slug}`' for slug in weak]
    Path('/home/ubuntu/homeleakfix_work/image_assignment_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Assigned {len(report)} unique filtered images. Weak/unchanged: {len(weak)}')

if __name__ == '__main__':
    main()
