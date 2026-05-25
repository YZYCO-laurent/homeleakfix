from pathlib import Path

ROOT = Path('/home/ubuntu/homeleakfix_work/homeleakfix')

def write(rel, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip('\n'), encoding='utf-8')

write('hugo.yaml', r'''
baseURL: "https://homeleakfix.com/"
languageCode: "en-us"
title: "Home Leak Fix"
timeZone: "Europe/Brussels"
defaultContentLanguage: "en"
enableRobotsTXT: true
enableGitInfo: false
buildFuture: true
summaryLength: 28
paginate: 18

permalinks:
  articles: "/:slug/"

outputs:
  home:
    - HTML
    - RSS
  section:
    - HTML
  taxonomy:
    - HTML
  term:
    - HTML

markup:
  goldmark:
    renderer:
      unsafe: true
  tableOfContents:
    startLevel: 2
    endLevel: 3
    ordered: false

sitemap:
  changefreq: "weekly"
  priority: 0.7
  filename: "sitemap.xml"

taxonomies:
  category: "categories"
  tag: "tags"

params:
  description: "Practical DIY guides for finding, fixing, and preventing leaks around roofs, gutters, basements, bathrooms, balconies, exterior walls, windows, and doors."
  author: "Home Leak Fix Editorial Team"
  publisher: "Home Leak Fix"
  defaultImage: "/images/site/homeleakfix-og.svg"
  primaryColor: "#0f5e63"
  accentColor: "#f59e0b"
  domain: "homeleakfix.com"
  disclaimer: "Home Leak Fix publishes general DIY information for homeowners. Water intrusion can involve structural, electrical, height, mould, or insurance risks. Use proper safety equipment, follow local building rules, and call a qualified professional when a repair is unsafe, unclear, or beyond your experience."
  categories:
    start-here:
      title: "Start Here"
      description: "Foundational guides that explain how water moves through a home and how to choose safe repair priorities."
      icon: "compass"
    flat-roof-leaks:
      title: "Flat Roof Leaks"
      description: "Diagnosis and repair guidance for flat roofs, membranes, coatings, flashing, ponding water, blisters, and edge leaks."
      icon: "roof"
    gutters-downspouts:
      title: "Gutters & Downspouts"
      description: "Practical help for overflowing gutters, leaking seams, blocked downspouts, sagging runs, end caps, winter repair, and roofline drainage."
      icon: "gutter"
    basements-foundations:
      title: "Basements & Foundations"
      description: "Guides to damp basements, foundation cracks, hydrostatic pressure, drain tile, sump pumps, efflorescence, and below-grade waterproofing."
      icon: "foundation"
    bathrooms-wet-rooms:
      title: "Bathrooms & Wet Rooms"
      description: "Shower, wet-room, tile, grout, silicone, and bathroom leak repair guidance for durable interior waterproofing."
      icon: "shower"
    windows-doors-walls:
      title: "Windows, Doors & Walls"
      description: "Exterior wall damp, driving rain, window frame leaks, thresholds, wall penetrations, masonry, render, and indoor moisture problems."
      icon: "window"
    balconies-exterior-concrete:
      title: "Balconies & Exterior Concrete"
      description: "Waterproofing help for balconies, patios, outdoor concrete, brick, garden walls, frost damage, and exposed surfaces."
      icon: "concrete"
    sealants-materials:
      title: "Sealants & Materials"
      description: "Comparisons of sealants, caulks, coatings, membranes, bitumen, acrylic, silicone, polyurethane, MS polymer, and liquid rubber."
      icon: "tube"
    seasonal-prevention:
      title: "Seasonal Prevention"
      description: "Maintenance calendars, prevention checklists, cold-weather advice, ventilation, mould prevention, and low-cost leak-proofing routines."
      icon: "calendar"
    emergency-repairs:
      title: "Emergency Repairs"
      description: "Immediate leak response, documentation, temporary patches, wet-weather safety, and when to stop DIY work."
      icon: "alert"

menu:
  main:
    - name: "Knowledge Base"
      url: "/articles/"
      weight: 10
    - name: "Categories"
      url: "/categories/"
      weight: 20
    - name: "Start Here"
      url: "/categories/start-here/"
      weight: 30
    - name: "Emergency Guide"
      url: "/emergency-leak-repair-guide-what-to-do-during-heavy-rain-bef/"
      weight: 40
    - name: "Contact"
      url: "/contact/"
      weight: 50
  footer:
    - name: "About"
      url: "/about/"
      weight: 10
    - name: "Contact"
      url: "/contact/"
      weight: 20
    - name: "Privacy Policy"
      url: "/privacy-policy/"
      weight: 30
    - name: "Terms"
      url: "/terms/"
      weight: 40
    - name: "Disclaimer"
      url: "/disclaimer/"
      weight: 50
    - name: "Sitemap"
      url: "/sitemap/"
      weight: 60
''')

write('layouts/_default/baseof.html', r'''
<!doctype html>
<html lang="{{ site.Language.LanguageCode | default "en" }}">
<head>
  {{ partial "head.html" . }}
</head>
<body class="{{ if .IsHome }}is-home{{ end }}">
  {{ partial "header.html" . }}
  <main id="main-content">
    {{ block "main" . }}{{ end }}
  </main>
  {{ partial "footer.html" . }}
</body>
</html>
''')

write('layouts/partials/head.html', r'''
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{{ $siteTitle := site.Title }}
{{ $rawTitle := cond .IsHome $siteTitle (printf "%s | %s" .Title $siteTitle) }}
{{ $title := $rawTitle | plainify | htmlUnescape }}
{{ if gt (len $title) 68 }}{{ $title = printf "%s…" (substr $title 0 67) }}{{ end }}
{{ $desc := .Description | default .Params.description | default site.Params.description | plainify | htmlUnescape }}
{{ if gt (len $desc) 165 }}{{ $desc = printf "%s…" (substr $desc 0 164) }}{{ end }}
<title>{{ $title }}</title>
<meta name="description" content="{{ $desc }}">
<link rel="canonical" href="{{ .Permalink }}">
<meta name="robots" content="{{ if .Params.noindex }}noindex,follow{{ else }}index,follow{{ end }}">
<meta property="og:site_name" content="{{ site.Title }}">
<meta property="og:title" content="{{ $title }}">
<meta property="og:description" content="{{ $desc }}">
<meta property="og:url" content="{{ .Permalink }}">
<meta property="og:type" content="{{ if .IsPage }}article{{ else }}website{{ end }}">
{{ $img := .Params.image | default site.Params.defaultImage }}
{{ $imgAbs := absURL $img }}
<meta property="og:image" content="{{ $imgAbs }}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ $title }}">
<meta name="twitter:description" content="{{ $desc }}">
<meta name="twitter:image" content="{{ $imgAbs }}">
<link rel="preload" href="/css/main.css" as="style">
<link rel="stylesheet" href="/css/main.css">
<link rel="alternate" type="application/rss+xml" title="{{ site.Title }}" href="{{ "index.xml" | absURL }}">
<link rel="icon" href="/images/site/favicon.svg" type="image/svg+xml">
{{ partial "schema.html" . }}
''')

write('layouts/partials/schema.html', r'''
{{ $img := .Params.image | default site.Params.defaultImage | absURL }}
{{ $desc := .Description | default .Params.description | default site.Params.description | plainify | htmlUnescape }}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "{{ site.BaseURL }}#organization",
      "name": "{{ site.Title }}",
      "url": "{{ site.BaseURL }}",
      "logo": "{{ site.Params.defaultImage | absURL }}"
    }{{ if .IsHome }},
    {
      "@type": "WebSite",
      "@id": "{{ site.BaseURL }}#website",
      "url": "{{ site.BaseURL }}",
      "name": "{{ site.Title }}",
      "description": "{{ site.Params.description }}",
      "publisher": {"@id": "{{ site.BaseURL }}#organization"}
    }{{ end }}{{ if and .IsPage (eq .Section "articles") }},
    {
      "@type": "Article",
      "@id": "{{ .Permalink }}#article",
      "mainEntityOfPage": "{{ .Permalink }}",
      "headline": "{{ .Title | plainify }}",
      "description": "{{ $desc }}",
      "image": ["{{ $img }}"],
      "datePublished": "{{ .Date.Format "2006-01-02T15:04:05Z07:00" }}",
      "dateModified": "{{ .Lastmod.Format "2006-01-02T15:04:05Z07:00" }}",
      "author": {"@type": "Organization", "name": "{{ site.Params.author }}"},
      "publisher": {"@id": "{{ site.BaseURL }}#organization"},
      "articleSection": {{ .Params.categories | jsonify }},
      "keywords": {{ .Params.tags | default .Params.secondary_keywords | jsonify }}
    }{{ end }}
  ]
}
</script>
''')

write('layouts/partials/header.html', r'''
<header class="site-header">
  <a class="skip-link" href="#main-content">Skip to content</a>
  <div class="container header-inner">
    <a class="brand" href="/" aria-label="Home Leak Fix home">
      <span class="brand-mark">HLF</span>
      <span class="brand-text"><strong>Home Leak Fix</strong><small>DIY waterproofing knowledge base</small></span>
    </a>
    <nav class="main-nav" aria-label="Main navigation">
      {{ range site.Menus.main }}<a href="{{ .URL }}">{{ .Name }}</a>{{ end }}
    </nav>
  </div>
</header>
''')

write('layouts/partials/footer.html', r'''
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <a class="brand footer-brand" href="/">
        <span class="brand-mark">HLF</span>
        <span class="brand-text"><strong>Home Leak Fix</strong><small>Dry homes, safer repairs.</small></span>
      </a>
      <p>{{ site.Params.description }}</p>
    </div>
    <div>
      <h2>Explore</h2>
      <nav class="footer-links" aria-label="Footer navigation">{{ range site.Menus.footer }}<a href="{{ .URL }}">{{ .Name }}</a>{{ end }}</nav>
    </div>
    <div>
      <h2>Safety note</h2>
      <p>Use these guides as general education. Stop and call a professional when height, structure, wiring, mould, active flooding, or uncertainty creates risk.</p>
    </div>
  </div>
  <div class="container copyright">© {{ now.Format "2006" }} Home Leak Fix. Independent informational resource.</div>
</footer>
''')

write('layouts/partials/article-card.html', r'''
<article class="card article-card">
  <a class="card-media" href="{{ .RelPermalink }}" aria-label="Read {{ .Title }}">
    {{ $image := .Params.image | default site.Params.defaultImage }}
    <img src="{{ $image }}" alt="{{ .Params.image_alt | default (printf "Illustration for %s" .Title) }}" loading="lazy">
  </a>
  <div class="card-body">
    <div class="meta-row">
      {{ with index .Params.categories 0 }}<a class="badge" href="{{ printf "/categories/%s/" (. | urlize) }}">{{ . }}</a>{{ end }}
      <span>{{ .ReadingTime }} min read</span>
    </div>
    <h2><a href="{{ .RelPermalink }}">{{ .Title }}</a></h2>
    <p>{{ .Description | default .Summary | plainify | truncate 155 }}</p>
  </div>
</article>
''')

write('layouts/index.html', r'''
{{ define "main" }}
{{ $articles := where site.RegularPages "Section" "articles" }}
<section class="hero">
  <div class="container hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">DIY leak diagnosis and waterproofing guidance</p>
      <h1>Find the leak, understand the cause, and choose the safer fix.</h1>
      <p class="lead">Home Leak Fix organizes practical homeowner guidance for roofs, gutters, basements, bathrooms, balconies, walls, windows, doors, sealants, and seasonal leak prevention.</p>
      <div class="hero-actions"><a class="button primary" href="/articles/">Browse the knowledge base</a><a class="button secondary" href="/categories/">Explore by problem area</a></div>
    </div>
    <div class="hero-panel">
      <div class="panel-topline">Most repairs start with three checks</div>
      <ol>
        <li>Trace where water appears, not just where it enters.</li>
        <li>Separate drainage failures from waterproofing failures.</li>
        <li>Use temporary patches only when they do not hide a larger risk.</li>
      </ol>
    </div>
  </div>
</section>

<section class="container section-block">
  <div class="section-heading">
    <p class="eyebrow">Topic clusters</p>
    <h2>Start with the part of the home that is leaking</h2>
    <p>Each hub collects related guides so you can move from symptoms to likely causes, repair choices, and prevention habits.</p>
  </div>
  <div class="category-grid">
    {{ range $slug, $cat := site.Params.categories }}
      {{ $term := index site.Taxonomies.categories $slug }}
      <a class="category-card" href="/categories/{{ $slug }}/">
        <span class="category-icon">{{ substr $cat.title 0 1 }}</span>
        <strong>{{ $cat.title }}</strong>
        <span>{{ $cat.description }}</span>
        <em>{{ len $term }} guides</em>
      </a>
    {{ end }}
  </div>
</section>

<section class="feature-strip">
  <div class="container feature-grid">
    <div><strong>Content-first structure</strong><span>Long-form guides grouped into stable topical hubs.</span></div>
    <div><strong>DIY safety framing</strong><span>Clear boundaries between homeowner checks and professional repairs.</span></div>
    <div><strong>Maintenance focus</strong><span>Prevention guidance for rainy, cold, and exposed climates.</span></div>
  </div>
</section>

<section class="container section-block">
  <div class="section-heading split">
    <div><p class="eyebrow">Latest guides</p><h2>Recently added leak repair articles</h2></div>
    <a class="text-link" href="/articles/">View all guides</a>
  </div>
  <div class="article-grid">
    {{ range first 9 (sort $articles "Date" "desc") }}{{ partial "article-card.html" . }}{{ end }}
  </div>
</section>

<section class="container mission-block">
  <div>
    <p class="eyebrow">Editorial mission</p>
    <h2>Helpful repairs begin with better diagnosis.</h2>
  </div>
  <p>Home Leak Fix is built for homeowners who want to understand why a leak happens before buying products or starting demolition. The site prioritizes clear explanations, repair context, maintenance routines, and safety limits over one-size-fits-all fixes.</p>
</section>
{{ end }}
''')

write('layouts/_default/list.html', r'''
{{ define "main" }}
<section class="page-hero compact">
  <div class="container">
    <p class="eyebrow">Knowledge base</p>
    <h1>{{ .Title }}</h1>
    <p class="lead">{{ .Description | default "Browse practical DIY leak repair and waterproofing guides by topic, symptom, and repair context." }}</p>
  </div>
</section>
<section class="container archive-layout">
  <aside class="archive-sidebar">
    <h2>Problem areas</h2>
    <nav>{{ range $slug, $cat := site.Params.categories }}<a href="/categories/{{ $slug }}/">{{ $cat.title }}</a>{{ end }}</nav>
  </aside>
  <div>
    <div class="archive-summary">{{ len .Pages }} guides in this section</div>
    <div class="article-grid list-grid">
      {{ range .Paginator.Pages }}{{ partial "article-card.html" . }}{{ end }}
    </div>
    {{ template "_internal/pagination.html" . }}
  </div>
</section>
{{ end }}
''')

write('layouts/_default/terms.html', r'''
{{ define "main" }}
<section class="page-hero compact">
  <div class="container">
    <p class="eyebrow">Category hub</p>
    <h1>Leak repair topics</h1>
    <p class="lead">Use these content hubs to move from the visible symptom to the repair area, material choice, and prevention routine that best matches your home.</p>
  </div>
</section>
<section class="container section-block">
  <div class="category-grid expanded">
    {{ range $slug, $cat := site.Params.categories }}
      {{ $term := index site.Taxonomies.categories $slug }}
      <a class="category-card" href="/categories/{{ $slug }}/">
        <span class="category-icon">{{ substr $cat.title 0 1 }}</span>
        <strong>{{ $cat.title }}</strong>
        <span>{{ $cat.description }}</span>
        <em>{{ len $term }} guides</em>
      </a>
    {{ end }}
  </div>
</section>
{{ end }}
''')

write('layouts/_default/taxonomy.html', r'''
{{ define "main" }}
{{ $slug := .Data.Term }}
{{ $cat := index site.Params.categories $slug }}
<section class="page-hero compact">
  <div class="container">
    <nav class="breadcrumbs"><a href="/">Home</a><span>/</span><a href="/categories/">Categories</a></nav>
    <p class="eyebrow">{{ len .Pages }} guides</p>
    <h1>{{ with $cat }}{{ .title }}{{ else }}{{ .Title }}{{ end }}</h1>
    <p class="lead">{{ with $cat }}{{ .description }}{{ else }}Browse related Home Leak Fix guides in this topic cluster.{{ end }}</p>
  </div>
</section>
<section class="container archive-layout">
  <aside class="archive-sidebar">
    <h2>All topics</h2>
    <nav>{{ range $s, $c := site.Params.categories }}<a class="{{ if eq $s $slug }}active{{ end }}" href="/categories/{{ $s }}/">{{ $c.title }}</a>{{ end }}</nav>
  </aside>
  <div class="article-grid list-grid">
    {{ range .Pages.ByTitle }}{{ partial "article-card.html" . }}{{ end }}
  </div>
</section>
{{ end }}
''')

write('layouts/_default/single.html', r'''
{{ define "main" }}
{{ if eq .Section "articles" }}
<article class="article-shell">
  <header class="article-header">
    <div class="container article-header-grid">
      <div>
        <nav class="breadcrumbs"><a href="/">Home</a><span>/</span><a href="/articles/">Knowledge Base</a>{{ with index .Params.categories 0 }}<span>/</span><a href="{{ printf "/categories/%s/" (. | urlize) }}">{{ . }}</a>{{ end }}</nav>
        <div class="meta-row category-row">{{ range .Params.categories }}<a class="badge" href="{{ printf "/categories/%s/" (. | urlize) }}">{{ . }}</a>{{ end }}</div>
        <h1>{{ .Title }}</h1>
        <p class="lead">{{ .Description | default .Summary | plainify }}</p>
        <div class="article-meta">By {{ site.Params.author }} · Updated {{ .Lastmod.Format "Jan 2, 2006" }} · {{ .ReadingTime }} min read</div>
      </div>
      <figure class="article-hero-image">
        {{ $image := .Params.image | default site.Params.defaultImage }}
        <img src="{{ $image }}" alt="{{ .Params.image_alt | default (printf "Featured image for %s" .Title) }}">
      </figure>
    </div>
  </header>
  <div class="container article-layout">
    <aside class="toc-wrap">
      <div class="toc-card"><strong>On this page</strong>{{ .TableOfContents }}</div>
    </aside>
    <div class="article-content">
      {{ .Content }}
      <section class="disclaimer-box">
        <h2>DIY safety disclaimer</h2>
        <p>{{ site.Params.disclaimer }}</p>
      </section>
      <section class="article-taxonomy">
        <h2>Related topics</h2>
        <div class="tag-list">{{ range .Params.categories }}<a href="{{ printf "/categories/%s/" (. | urlize) }}">{{ . }}</a>{{ end }}{{ range .Params.tags }}<span>{{ . }}</span>{{ end }}</div>
      </section>
    </div>
  </div>
  <section class="container related-section">
    <div class="section-heading split"><div><p class="eyebrow">Keep learning</p><h2>Related leak repair guides</h2></div></div>
    <div class="article-grid">
      {{ $cats := .Params.categories }}
      {{ $shown := 0 }}
      {{ range where site.RegularPages "Section" "articles" }}
        {{ if and (ne .RelPermalink $.RelPermalink) (gt (len (intersect .Params.categories $cats)) 0) (lt $shown 6) }}
          {{ partial "article-card.html" . }}
          {{ $shown = add $shown 1 }}
        {{ end }}
      {{ end }}
    </div>
  </section>
</article>
{{ else }}
<section class="page-hero compact"><div class="container"><h1>{{ .Title }}</h1>{{ with .Description }}<p class="lead">{{ . }}</p>{{ end }}</div></section>
<section class="container page-content article-content">{{ .Content }}</section>
{{ end }}
{{ end }}
''')

write('layouts/404.html', r'''
{{ define "main" }}
<section class="page-hero compact not-found">
  <div class="container">
    <p class="eyebrow">404</p>
    <h1>That page is not available.</h1>
    <p class="lead">The guide may have moved, or the URL may be mistyped. Start from the knowledge base or browse by leak problem area.</p>
    <div class="hero-actions"><a class="button primary" href="/articles/">Browse all guides</a><a class="button secondary" href="/categories/">View categories</a></div>
  </div>
</section>
{{ end }}
''')

write('layouts/sitemap/single.html', r'''
{{ define "main" }}
<section class="page-hero compact"><div class="container"><h1>{{ .Title }}</h1><p class="lead">A human-readable overview of the most important Home Leak Fix pages and guides.</p></div></section>
<section class="container sitemap-page">
  <h2>Main pages</h2>
  <ul>{{ range site.Menus.main }}<li><a href="{{ .URL }}">{{ .Name }}</a></li>{{ end }}</ul>
  <h2>Article guides</h2>
  <ul>{{ range where site.RegularPages "Section" "articles" }}<li><a href="{{ .RelPermalink }}">{{ .Title }}</a></li>{{ end }}</ul>
</section>
{{ end }}
''')

write('static/css/main.css', r'''
:root{--ink:#102327;--muted:#5f6f73;--line:#dbe6e3;--bg:#f5f8f6;--card:#fff;--teal:#0f5e63;--teal-dark:#0b4549;--mint:#dff0eb;--amber:#f59e0b;--amber-soft:#fff5d8;--shadow:0 18px 45px rgba(16,35,39,.09);--radius:22px;--max:1180px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg);line-height:1.65}a{color:inherit;text-decoration:none}img{max-width:100%;display:block}.container{width:min(var(--max),calc(100% - 40px));margin-inline:auto}.skip-link{position:absolute;left:-999px;top:auto}.skip-link:focus{left:20px;top:12px;z-index:20;background:#fff;padding:10px 14px;border-radius:10px}.site-header{position:sticky;top:0;z-index:10;background:rgba(245,248,246,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}.header-inner{display:flex;align-items:center;justify-content:space-between;gap:28px;padding:16px 0}.brand{display:flex;align-items:center;gap:12px}.brand-mark{display:grid;place-items:center;width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,var(--teal),#168f8a);color:#fff;font-weight:800;letter-spacing:.04em}.brand-text{display:flex;flex-direction:column;line-height:1.15}.brand-text small{color:var(--muted);font-size:.78rem;margin-top:2px}.main-nav{display:flex;align-items:center;gap:18px;font-weight:700;font-size:.95rem}.main-nav a{color:#294145}.main-nav a:hover{color:var(--teal)}.hero{padding:78px 0 58px;background:radial-gradient(circle at 78% 20%,#d5ede9 0,transparent 34%),linear-gradient(180deg,#fff 0%,var(--bg) 100%)}.hero-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(320px,.85fr);gap:42px;align-items:center}.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-weight:800;color:var(--teal);font-size:.78rem;margin:0 0 12px}.hero h1,.page-hero h1{font-size:clamp(2.5rem,5vw,5.2rem);line-height:.98;margin:0 0 22px;letter-spacing:-.055em}.lead{font-size:1.18rem;color:#405559;max-width:760px;margin:0 0 28px}.hero-actions{display:flex;gap:14px;flex-wrap:wrap}.button{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:13px 19px;font-weight:800;border:1px solid transparent}.button.primary{background:var(--teal);color:#fff;box-shadow:0 12px 26px rgba(15,94,99,.22)}.button.primary:hover{background:var(--teal-dark)}.button.secondary{background:#fff;border-color:var(--line);color:var(--teal)}.hero-panel{background:var(--card);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:var(--radius);padding:28px}.panel-topline{font-weight:900;margin-bottom:12px}.hero-panel ol{margin:0;padding-left:22px}.hero-panel li{margin:10px 0;color:#32484c}.section-block{padding:64px 0}.section-heading{max-width:760px;margin-bottom:28px}.section-heading h2,.mission-block h2,.feature-grid strong{font-size:clamp(1.8rem,3vw,2.8rem);line-height:1.06;letter-spacing:-.04em;margin:0 0 12px}.section-heading p{color:var(--muted);margin:0}.split{display:flex;align-items:end;justify-content:space-between;gap:20px;max-width:none}.text-link{font-weight:900;color:var(--teal);border-bottom:2px solid var(--teal)}.category-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}.category-grid.expanded{grid-template-columns:repeat(3,minmax(0,1fr))}.category-card{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:20px;min-height:220px;display:flex;flex-direction:column;gap:11px;box-shadow:0 10px 24px rgba(16,35,39,.04);transition:transform .2s ease,box-shadow .2s ease}.category-card:hover{transform:translateY(-3px);box-shadow:var(--shadow)}.category-icon{width:42px;height:42px;display:grid;place-items:center;border-radius:14px;background:var(--mint);color:var(--teal);font-weight:900}.category-card strong{font-size:1.08rem}.category-card span:not(.category-icon){color:var(--muted);font-size:.92rem}.category-card em{margin-top:auto;color:var(--teal);font-weight:900;font-style:normal;font-size:.88rem}.feature-strip{background:var(--teal);color:#fff;padding:28px 0}.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.feature-grid div{display:flex;flex-direction:column;gap:6px}.feature-grid strong{font-size:1.25rem}.feature-grid span{color:#dcefed}.article-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;box-shadow:0 10px 24px rgba(16,35,39,.05)}.card-media{display:block;aspect-ratio:16/9;background:linear-gradient(135deg,#dff0eb,#fff5d8);overflow:hidden}.card-media img{width:100%;height:100%;object-fit:cover;transition:transform .25s ease}.card:hover img{transform:scale(1.04)}.card-body{padding:18px}.meta-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:.84rem;font-weight:700}.badge{display:inline-flex;align-items:center;border-radius:999px;background:var(--amber-soft);color:#8a5300;padding:5px 10px;font-size:.76rem;font-weight:900}.card h2{font-size:1.18rem;line-height:1.25;margin:12px 0 10px;letter-spacing:-.02em}.card h2 a:hover{color:var(--teal)}.card p{margin:0;color:var(--muted);font-size:.95rem}.mission-block{margin:28px auto 76px;padding:34px;border-radius:var(--radius);background:#fff;border:1px solid var(--line);display:grid;grid-template-columns:.9fr 1.1fr;gap:30px;box-shadow:var(--shadow)}.mission-block p:last-child{margin:0;color:#405559}.page-hero{padding:58px 0;background:#fff;border-bottom:1px solid var(--line)}.page-hero.compact h1{font-size:clamp(2.2rem,4vw,4rem)}.breadcrumbs{display:flex;gap:9px;align-items:center;flex-wrap:wrap;color:var(--muted);font-weight:800;font-size:.9rem;margin-bottom:18px}.breadcrumbs a{color:var(--teal)}.archive-layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:30px;padding:44px 0 72px}.archive-sidebar{position:sticky;top:86px;align-self:start;background:#fff;border:1px solid var(--line);border-radius:20px;padding:20px}.archive-sidebar h2{font-size:1rem;margin:0 0 12px}.archive-sidebar nav{display:grid;gap:8px}.archive-sidebar a{color:#405559;font-weight:800;padding:8px 10px;border-radius:12px}.archive-sidebar a:hover,.archive-sidebar a.active{background:var(--mint);color:var(--teal)}.archive-summary{margin-bottom:18px;color:var(--muted);font-weight:800}.list-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pagination{display:flex;gap:10px;justify-content:center;list-style:none;padding:28px 0 0;margin:0}.pagination a,.pagination span{display:grid;place-items:center;min-width:40px;height:40px;border-radius:12px;background:#fff;border:1px solid var(--line);font-weight:800}.pagination .active a{background:var(--teal);color:#fff}.article-header{background:linear-gradient(180deg,#fff 0%,var(--bg) 100%);padding:42px 0;border-bottom:1px solid var(--line)}.article-header-grid{display:grid;grid-template-columns:minmax(0,1fr) 420px;gap:36px;align-items:center}.category-row{margin-bottom:14px}.article-header h1{font-size:clamp(2.2rem,4.5vw,4.5rem);line-height:1;letter-spacing:-.055em;margin:0 0 18px}.article-meta{color:var(--muted);font-weight:800}.article-hero-image{margin:0;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);border:1px solid var(--line);background:#fff;aspect-ratio:16/10}.article-hero-image img{width:100%;height:100%;object-fit:cover}.article-layout{display:grid;grid-template-columns:270px minmax(0,760px);gap:42px;padding:48px 0}.toc-wrap{position:relative}.toc-card{position:sticky;top:94px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px;max-height:calc(100vh - 120px);overflow:auto}.toc-card strong{display:block;margin-bottom:10px}.toc-card nav ul{list-style:none;padding-left:0;margin:0}.toc-card nav ul ul{padding-left:12px;margin-top:6px}.toc-card a{display:block;color:#50666a;font-size:.9rem;padding:4px 0}.toc-card a:hover{color:var(--teal)}.article-content{font-size:1.05rem}.article-content h2{font-size:2rem;line-height:1.15;letter-spacing:-.035em;margin:42px 0 14px}.article-content h3{font-size:1.35rem;line-height:1.25;margin:28px 0 10px}.article-content p{margin:0 0 18px}.article-content a{color:var(--teal);font-weight:800;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}.article-content ul,.article-content ol{padding-left:24px}.article-content li{margin:8px 0}.article-content table{width:100%;border-collapse:collapse;margin:24px 0;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 0 0 1px var(--line)}.article-content th,.article-content td{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}.article-content th{background:var(--mint);text-align:left}.article-content blockquote{margin:24px 0;padding:18px 20px;border-left:5px solid var(--teal);background:#fff;border-radius:0 16px 16px 0;color:#405559}.disclaimer-box,.article-taxonomy{margin-top:38px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px}.disclaimer-box h2,.article-taxonomy h2{font-size:1.35rem;margin:0 0 10px}.tag-list{display:flex;flex-wrap:wrap;gap:10px}.tag-list a,.tag-list span{border:1px solid var(--line);border-radius:999px;padding:7px 12px;font-size:.88rem;font-weight:800;background:#fff}.related-section{padding:16px 0 80px}.page-content{max-width:840px;padding:44px 0 76px}.sitemap-page{padding:44px 0 76px}.sitemap-page a{color:var(--teal);font-weight:800}.site-footer{background:#102327;color:#d9e7e4;padding:46px 0 22px}.footer-grid{display:grid;grid-template-columns:1.4fr .8fr 1fr;gap:34px}.footer-brand .brand-mark{background:#fff;color:var(--teal)}.site-footer p{color:#b8cac6;margin:14px 0 0}.site-footer h2{font-size:1rem;color:#fff;margin:0 0 12px}.footer-links{display:grid;gap:8px}.footer-links a{color:#d9e7e4;font-weight:700}.footer-links a:hover{color:#fff}.copyright{border-top:1px solid rgba(255,255,255,.13);margin-top:32px;padding-top:18px;color:#a7bbb7;font-size:.9rem}@media (max-width:980px){.main-nav{display:none}.hero-grid,.article-header-grid,.article-layout,.archive-layout,.mission-block,.footer-grid{grid-template-columns:1fr}.category-grid,.category-grid.expanded,.article-grid,.list-grid,.feature-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.toc-card{position:static}.article-layout{padding-top:28px}.archive-sidebar{position:static}.hero{padding-top:48px}}@media (max-width:640px){.container{width:min(100% - 26px,var(--max))}.category-grid,.category-grid.expanded,.article-grid,.list-grid,.feature-grid{grid-template-columns:1fr}.hero-actions{display:grid}.button{width:100%}.hero h1,.page-hero.compact h1,.article-header h1{letter-spacing:-.04em}.section-block{padding:44px 0}.article-content h2{font-size:1.65rem}.header-inner{padding:12px 0}.brand-text small{display:none}}
''')

write('static/images/site/homeleakfix-og.svg', r'''
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0f5e63"/><stop offset="1" stop-color="#168f8a"/></linearGradient></defs>
  <rect width="1200" height="630" fill="#f5f8f6"/>
  <circle cx="955" cy="132" r="190" fill="#dff0eb"/>
  <rect x="90" y="110" width="1020" height="410" rx="42" fill="white" stroke="#dbe6e3" stroke-width="4"/>
  <rect x="140" y="160" width="118" height="118" rx="28" fill="url(#g)"/>
  <text x="199" y="232" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="38" font-weight="800">HLF</text>
  <text x="140" y="352" fill="#102327" font-family="Arial, sans-serif" font-size="72" font-weight="800">Home Leak Fix</text>
  <text x="140" y="420" fill="#405559" font-family="Arial, sans-serif" font-size="34">DIY waterproofing and leak repair guides</text>
</svg>
''')

write('static/images/site/favicon.svg', r'''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#0f5e63"/><text x="32" y="39" text-anchor="middle" fill="white" font-family="Arial" font-size="20" font-weight="800">HLF</text></svg>
''')

write('static/robots.txt', r'''
User-agent: *
Allow: /
Disallow: /tags/
Disallow: /page/
Disallow: /*?*

Sitemap: https://homeleakfix.com/sitemap.xml
''')

write('static/llms.txt', r'''
# Home Leak Fix

Home Leak Fix is an independent DIY home leak repair and waterproofing knowledge base for homeowners. It explains how to identify, understand, repair, and prevent common water intrusion problems around roofs, gutters, basements, bathrooms, balconies, exterior walls, windows, and doors.

Core topical clusters include flat roof leaks, gutters and downspouts, basements and foundations, bathrooms and wet rooms, windows doors and walls, balconies and exterior concrete, waterproofing materials and sealants, seasonal prevention, emergency repairs, and foundational home waterproofing guides.

Editorial standards: content is informational, practical, safety-aware, and organized by durable categories. Articles are designed to help readers distinguish DIY maintenance from situations requiring qualified professionals.

Disclaimer: this website provides general information only. Water intrusion can involve structural, electrical, mould, height, insurance, and regulatory risks. Readers should follow local rules and call a qualified professional when needed.
''')

write('netlify.toml', r'''
[build]
  command = "hugo --gc --minify"
  publish = "public"

[build.environment]
  HUGO_VERSION = "0.161.1"
  HUGO_ENV = "production"
  HUGO_ENABLEGITINFO = "false"

[[headers]]
  for = "/*"
  [headers.values]
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
    X-Frame-Options = "DENY"

[[redirects]]
  from = "/blog/*"
  to = "/articles/:splat"
  status = 301
''')

# Legal/trust pages and sitemap content page
pages = {
'content/about.md': '''---\ntitle: "About Home Leak Fix"\ndescription: "Learn how Home Leak Fix organizes practical DIY leak repair and waterproofing guidance for homeowners."\nlayout: "single"\n---\n\nHome Leak Fix is an independent informational website focused on helping homeowners understand common leak paths before choosing a repair. The site covers roofs, gutters, basements, bathrooms, balconies, exterior walls, windows, doors, sealants, coatings, and seasonal prevention.\n\nOur editorial approach is practical and safety-aware. We explain likely causes, repair options, maintenance habits, and warning signs that indicate a professional should be involved. The aim is to help readers make better decisions, not to replace qualified inspection, local code requirements, or specialist repair work.\n''',
'content/contact.md': '''---\ntitle: "Contact"\ndescription: "Contact information for Home Leak Fix editorial enquiries."\nlayout: "single"\n---\n\nFor editorial enquiries, corrections, or partnership questions, please contact the Home Leak Fix editorial team through the site owner. If you are dealing with active flooding, structural movement, electrical hazards, mould contamination, or roof-height work, contact a qualified local professional immediately.\n''',
'content/privacy-policy.md': '''---\ntitle: "Privacy Policy"\ndescription: "Privacy policy for Home Leak Fix."\nlayout: "single"\n---\n\nHome Leak Fix is an informational website. Basic server logs, analytics, or contact details may be processed to operate, secure, and improve the website. We do not publish personal information provided by readers. Third-party services such as hosting, analytics, or image delivery may process limited technical data according to their own policies.\n\nIf contact forms, comments, or newsletters are added in the future, this page should be updated to describe the data collected, the purpose of processing, retention rules, and opt-out methods.\n''',
'content/terms.md': '''---\ntitle: "Terms of Use"\ndescription: "Terms of use for Home Leak Fix."\nlayout: "single"\n---\n\nBy using Home Leak Fix, you agree that the content is provided for general information only. The website does not provide professional building, roofing, structural, legal, insurance, or health advice. You are responsible for assessing site conditions, following local rules, using appropriate protective equipment, and hiring qualified professionals where needed.\n\nNo guarantee is made that a repair described on this website is suitable for a specific building, climate, material, or warranty condition.\n''',
'content/disclaimer.md': '''---\ntitle: "DIY Safety Disclaimer"\ndescription: "Important safety and professional-advice disclaimer for Home Leak Fix guides."\nlayout: "single"\n---\n\nHome Leak Fix publishes general DIY information for homeowners. Water intrusion can involve structural defects, electrical hazards, mould contamination, roof-height work, insurance documentation, hidden rot, and local building regulations.\n\nStop DIY work and call a qualified professional when a leak is active, unsafe to access, connected to wiring, related to structural movement, inside a roof assembly, affecting a shared building, or not clearly understood. Temporary patches should not be treated as permanent repairs unless the material and building detail support that use.\n''',
'content/sitemap.md': '''---\ntitle: "Sitemap"\ndescription: "Human-readable sitemap for Home Leak Fix."\nlayout: "sitemap"\n---\n'''
}
for rel, txt in pages.items():
    write(rel, txt)

write('content/articles/_index.md', '''---\ntitle: "Home Leak Repair Knowledge Base"\ndescription: "Browse all Home Leak Fix DIY guides for roofs, gutters, basements, bathrooms, balconies, exterior walls, sealants, emergency repairs, and seasonal prevention."\n---\n''')

print('Custom Hugo scaffold written.')
