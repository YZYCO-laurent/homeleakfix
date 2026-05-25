from pathlib import Path
import re
import yaml
from datetime import datetime, timedelta

SRC = Path('/home/ubuntu/homeleakfix_work/content_export')
DST = Path('/home/ubuntu/homeleakfix_work/homeleakfix/content/articles')
DST.mkdir(parents=True, exist_ok=True)

CATEGORY_TITLES = {
    'start-here': 'Start Here',
    'flat-roof-leaks': 'Flat Roof Leaks',
    'gutters-downspouts': 'Gutters & Downspouts',
    'basements-foundations': 'Basements & Foundations',
    'bathrooms-wet-rooms': 'Bathrooms & Wet Rooms',
    'windows-doors-walls': 'Windows, Doors & Walls',
    'balconies-exterior-concrete': 'Balconies & Exterior Concrete',
    'sealants-materials': 'Sealants & Materials',
    'seasonal-prevention': 'Seasonal Prevention',
    'emergency-repairs': 'Emergency Repairs',
}

CATEGORY_RULES = [
    ('emergency-repairs', ['emergency', 'active leak', 'temporary patch', 'heavy rain before', 'wet weather safe', 'repair in wet weather']),
    ('start-here', ['complete guide', 'finding and fixing', 'home waterproofing', 'diy waterproofing vs professional', 'where water enters', 'before they become disasters']),
    ('gutters-downspouts', ['gutter', 'downspout', 'downspouts', 'roofline drainage', 'box gutter', 'box gutters']),
    ('flat-roof-leaks', ['flat roof', 'epdm', 'felt roof', 'fibreglass flat roof', 'roof coating', 'ponding water', 'roof blisters', 'roof drainage', 'garage roof']),
    ('basements-foundations', ['basement', 'foundation', 'sump pump', 'french drain', 'tanking', 'hydrostatic', 'efflorescence on basement', 'damp proof course', 'cellar']),
    ('bathrooms-wet-rooms', ['bathroom', 'shower', 'wet room', 'wet-room', 'grout', 'tile', 'tiling', 'silicone failure']),
    ('windows-doors-walls', ['window', 'door', 'wall', 'walls', 'render', 'masonry', 'driving rain', 'damp patch', 'threshold', 'dormer', 'garage wall']),
    ('balconies-exterior-concrete', ['balcony', 'concrete', 'garden wall', 'outdoor', 'patio', 'path', 'freeze-thaw', 'frost', 'brick', 'exterior concrete']),
    ('sealants-materials', ['sealant', 'sealants', 'coating', 'membrane', 'bitumen', 'liquid rubber', 'polyurethane', 'acrylic', 'silicone', 'cementitious', 'crystalline', 'ms polymer', 'paint over waterproof']),
    ('seasonal-prevention', ['maintenance checklist', 'schedule', 'winter', 'summer', 'seasonal', 'prevention', 'ventilation', 'mould', 'mold', 'condensation', 'rainy european climates', 'coastal homes']),
]

SECONDARY_RULES = {
    'sealants-materials': ['sealant', 'coating', 'membrane', 'bitumen', 'rubber', 'polyurethane', 'acrylic', 'silicone', 'cementitious', 'crystalline', 'paint'],
    'seasonal-prevention': ['maintenance', 'checklist', 'schedule', 'winter', 'summer', 'frost', 'freeze', 'mould', 'mold', 'condensation', 'prevention'],
    'emergency-repairs': ['emergency', 'temporary', 'wet weather', 'heavy rain'],
}

IMAGE_QUERY_BY_CATEGORY = {
    'Start Here': 'home waterproofing inspection',
    'Flat Roof Leaks': 'flat roof repair waterproofing',
    'Gutters & Downspouts': 'rain gutter repair',
    'Basements & Foundations': 'basement waterproofing wall',
    'Bathrooms & Wet Rooms': 'bathroom waterproofing shower',
    'Windows, Doors & Walls': 'window rain wall repair',
    'Balconies & Exterior Concrete': 'concrete balcony waterproofing',
    'Sealants & Materials': 'caulking sealant repair',
    'Seasonal Prevention': 'home maintenance rain',
    'Emergency Repairs': 'roof leak repair rain',
}

FRONT_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n?', re.S)

def parse_doc(text):
    m = FRONT_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    try:
        meta = yaml.safe_load(raw) or {}
    except Exception:
        meta = {}
    return meta, body

def slug_from_filename(path):
    stem = path.stem
    if stem.endswith('-final'):
        stem = stem[:-6]
    return stem

def clean_body(body, title):
    body = body.replace('\r\n', '\n')
    lines = body.split('\n')
    # Remove first duplicate H1 if it matches title closely.
    if lines and lines[0].strip().startswith('# '):
        first = re.sub(r'^#\s+', '', lines[0].strip()).strip()
        if re.sub(r'\W+', '', first.lower()) == re.sub(r'\W+', '', title.lower()):
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines = lines[1:]
    body = '\n'.join(lines).strip() + '\n'
    # Normalize a common malformed list continuation seen in some generated exports.
    body = re.sub(r'\n(\d+)\s*\*\s+', r'\n\1. ', body)
    body = re.sub(r'\n\s*\t', '\n    ', body)
    return body

def first_paragraph(body):
    for block in re.split(r'\n\s*\n', body):
        block = block.strip()
        if not block or block.startswith('#') or block.startswith('|') or block.startswith('-') or block.startswith('*'):
            continue
        clean = re.sub(r'[*_`>#\[\]()]+', '', block)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if len(clean) > 60:
            return clean
    return ''

def make_description(meta, body, title):
    desc = meta.get('description') or meta.get('meta_description') or first_paragraph(body)
    desc = re.sub(r'\s+', ' ', str(desc)).strip()
    if not desc:
        desc = f'Practical DIY guidance for {title.lower()} with diagnosis, repair options, prevention tips, and safety limits.'
    if len(desc) > 158:
        desc = desc[:155].rsplit(' ', 1)[0] + '...'
    return desc

def parse_tags(meta, title):
    raw = meta.get('secondary_keywords', '') or ''
    tags = []
    if isinstance(raw, list):
        tags.extend(raw)
    else:
        tags.extend([p.strip() for p in str(raw).split(',') if p.strip()])
    main = meta.get('main_keyword')
    if main:
        tags.insert(0, str(main).strip())
    # Add concise topical tags from title words when the source tags are thin.
    if len(tags) < 3:
        for phrase in ['flat roof', 'basement', 'gutter', 'shower', 'window', 'foundation', 'waterproofing', 'sealant']:
            if phrase in title.lower() and phrase not in tags:
                tags.append(phrase)
    seen, clean = set(), []
    for tag in tags:
        tag = re.sub(r'\s+', ' ', str(tag).strip().lower())
        if tag and tag not in seen:
            clean.append(tag)
            seen.add(tag)
    return clean[:8]

def choose_categories(slug, title, body, tags):
    text = ' '.join([slug.replace('-', ' '), title, ' '.join(tags), body[:1000]]).lower()
    scores = {k: 0 for k in CATEGORY_TITLES}
    for cat, needles in CATEGORY_RULES:
        for n in needles:
            if n in text:
                scores[cat] += 3 if n in title.lower() or n in slug.replace('-', ' ') else 1
    # Add secondary category hints without overriding the strongest primary topic.
    for cat, needles in SECONDARY_RULES.items():
        for n in needles:
            if n in text:
                scores[cat] += 1
    # Priority correction: material posts tied to one area should keep the area as primary.
    if scores['flat-roof-leaks'] > 0 and any(x in text for x in ['roof coating', 'flat roof', 'epdm', 'felt roof']):
        scores['flat-roof-leaks'] += 2
    if scores['basements-foundations'] > 0 and any(x in text for x in ['basement', 'foundation']):
        scores['basements-foundations'] += 2
    if scores['bathrooms-wet-rooms'] > 0 and any(x in text for x in ['bathroom', 'shower', 'wet room', 'wet-room']):
        scores['bathrooms-wet-rooms'] += 2
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = 'start-here'
    ordered = [best]
    for cat, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
        if cat != best and score >= 3 and len(ordered) < 3:
            ordered.append(cat)
    return [CATEGORY_TITLES[c] for c in ordered]

def parse_date(meta, offset):
    raw = meta.get('completed_at') or meta.get('date')
    if raw:
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S%z']:
            try:
                return datetime.strptime(str(raw), fmt)
            except Exception:
                pass
    return datetime(2026, 5, 25, 9, 0, 0) + timedelta(minutes=offset)

def dump_front_matter(data):
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=1000).strip()

records = []
for i, src in enumerate(sorted(SRC.glob('*.md'))):
    raw = src.read_text(encoding='utf-8')
    meta, body = parse_doc(raw)
    title = str(meta.get('title') or slug_from_filename(src).replace('-', ' ').title()).strip()
    slug = slug_from_filename(src)
    body = clean_body(body, title)
    desc = make_description(meta, body, title)
    tags = parse_tags(meta, title)
    cats = choose_categories(slug, title, body, tags)
    date = parse_date(meta, i)
    image_query = IMAGE_QUERY_BY_CATEGORY.get(cats[0], 'home waterproofing repair')
    out_meta = {
        'title': title,
        'description': desc,
        'date': date.strftime('%Y-%m-%dT%H:%M:%S+03:00'),
        'lastmod': date.strftime('%Y-%m-%dT%H:%M:%S+03:00'),
        'draft': False,
        'slug': slug,
        'categories': cats,
        'tags': tags,
        'main_keyword': meta.get('main_keyword', ''),
        'image': '',
        'image_alt': f'{title} - practical home leak repair guidance',
        'image_query': image_query,
        'content_score': meta.get('content_score', ''),
    }
    out = '---\n' + dump_front_matter(out_meta) + '\n---\n\n' + body
    (DST / f'{slug}.md').write_text(out, encoding='utf-8')
    records.append((slug, title, cats[0], len(body.split())))

# Write import report.
from collections import Counter
counts = Counter(r[2] for r in records)
report = ['# Content Import Report', '', f'Imported {len(records)} Markdown articles into `content/articles/`.', '', '| Category | Article Count |', '|---|---:|']
for cat, count in counts.most_common():
    report.append(f'| {cat} | {count} |')
report += ['', '## Imported Articles', '', '| Slug | Category | Words |', '|---|---|---:|']
for slug, title, cat, words in records:
    report.append(f'| `{slug}` | {cat} | {words} |')
(Path('/home/ubuntu/homeleakfix_work/content_import_report.md')).write_text('\n'.join(report) + '\n', encoding='utf-8')
print(f'Imported {len(records)} articles.')
for cat, count in counts.most_common():
    print(f'{cat}: {count}')
