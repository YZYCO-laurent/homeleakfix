from pathlib import Path
import json
import re

root = Path('public')
index = (root / 'index.html').read_text(encoding='utf-8')
counts = re.findall(r'<em>(\d+ guides)</em>', index)
print('category_counts:', counts)
print('zero_counts_present:', '0 guides' in index)
for p in ['sitemap.xml', 'robots.txt', 'index.xml', 'articles/index.html', 'categories/index.html']:
    f = root / p
    print(f'{p}: exists={f.exists()} size={f.stat().st_size if f.exists() else 0}')
article = root / 'flat-roof-leak-after-heavy-rain-diagnosis-and-repair-options' / 'index.html'
html = article.read_text(encoding='utf-8')
print('sample_article:', article)
print('has_canonical:', 'rel=canonical' in html or 'rel="canonical"' in html)
print('has_schema:', 'application/ld+json' in html)
print('has_og_image:', 'property="og:image"' in html)
print('has_toc:', 'On this page' in html)
print('article_title:', re.search(r'<title>(.*?)</title>', html).group(1))
print('webp_count:', len(list(Path('static/images/uploads').glob('*.webp'))))
credits = json.loads(Path('data/pixabay_image_credits.json').read_text(encoding='utf-8'))
print('image_credits:', len(credits))
for slug in ['flat-roof-leak-after-heavy-rain-diagnosis-and-repair-options', 'why-gutters-leak-at-the-joints-and-how-to-fix-them', 'can-you-fix-a-leaking-shower-without-removing-tiles']:
    sample = [c for c in credits if c['slug'] == slug]
    print(f'credit_sample_{slug}:', sample[:1])
