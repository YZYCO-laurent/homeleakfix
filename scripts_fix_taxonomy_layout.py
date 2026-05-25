from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content" / "articles"
CONFIG = ROOT / "hugo.yaml"

cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
category_params = cfg.get("params", {}).get("categories", {})
title_to_slug = {v.get("title"): k for k, v in category_params.items()}
# Preserve values already converted in future reruns.
valid_slugs = set(category_params.keys())

changed_files = 0
for path in sorted(CONTENT.glob("*.md")):
    if path.name == "_index.md":
        continue
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        continue
    fm = yaml.safe_load(m.group(1)) or {}
    cats = fm.get("categories") or []
    new_cats = []
    changed = False
    for cat in cats:
        slug = title_to_slug.get(cat, cat)
        if slug not in valid_slugs:
            # Last-resort cleanup for unexpected values.
            slug = re.sub(r"[^a-z0-9]+", "-", str(cat).lower()).strip("-")
        new_cats.append(slug)
        changed = changed or slug != cat
    if changed:
        fm["categories"] = new_cats
        body = text[m.end():]
        new_front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000).strip()
        path.write_text(f"---\n{new_front}\n---\n{body}", encoding="utf-8")
        changed_files += 1

# Helper partial for turning stored category slugs into public labels.
(ROOT / "layouts" / "partials" / "category-title.html").write_text("""{{- $slug := . -}}{{- with index site.Params.categories $slug -}}{{ .title }}{{- else -}}{{ replace $slug \"-\" \" \" | title }}{{- end -}}\n""", encoding="utf-8")

# Homepage counts now use stored category slugs directly.
index_path = ROOT / "layouts" / "index.html"
index_text = index_path.read_text(encoding="utf-8")
index_text = index_text.replace(
    '{{ $count := len (where $articles "Params.categories" "intersect" (slice $cat.title)) }}',
    '{{ $count := len (where $articles "Params.categories" "intersect" (slice $slug)) }}'
)
index_path.write_text(index_text, encoding="utf-8")

# Article card should link to clean slugs and display friendly names.
(ROOT / "layouts" / "partials" / "article-card.html").write_text("""<article class=\"card article-card\">\n  <a class=\"card-media\" href=\"{{ .RelPermalink }}\" aria-label=\"Read {{ .Title }}\">\n    {{ $image := .Params.image | default site.Params.defaultImage }}\n    <img src=\"{{ $image }}\" alt=\"{{ .Params.image_alt | default (printf \"Illustration for %s\" .Title) }}\" loading=\"lazy\">\n  </a>\n  <div class=\"card-body\">\n    <div class=\"meta-row\">\n      {{ with index .Params.categories 0 }}<a class=\"badge\" href=\"{{ printf \"/categories/%s/\" . }}\">{{ partial \"category-title.html\" . }}</a>{{ end }}\n      <span>{{ .ReadingTime }} min read</span>\n    </div>\n    <h2><a href=\"{{ .RelPermalink }}\">{{ .Title }}</a></h2>\n    <p>{{ .Description | default .Summary | plainify | truncate 155 }}</p>\n  </div>\n</article>\n""", encoding="utf-8")

# Single template category links and labels.
(ROOT / "layouts" / "_default" / "single.html").write_text("""{{ define \"main\" }}\n{{ if eq .Section \"articles\" }}\n<article class=\"article-shell\">\n  <header class=\"article-header\">\n    <div class=\"container article-header-grid\">\n      <div>\n        <nav class=\"breadcrumbs\"><a href=\"/\">Home</a><span>/</span><a href=\"/articles/\">Knowledge Base</a>{{ with index .Params.categories 0 }}<span>/</span><a href=\"{{ printf \"/categories/%s/\" . }}\">{{ partial \"category-title.html\" . }}</a>{{ end }}</nav>\n        <div class=\"meta-row category-row\">{{ range .Params.categories }}<a class=\"badge\" href=\"{{ printf \"/categories/%s/\" . }}\">{{ partial \"category-title.html\" . }}</a>{{ end }}</div>\n        <h1>{{ .Title }}</h1>\n        <p class=\"lead\">{{ .Description | default .Summary | plainify }}</p>\n        <div class=\"article-meta\">By {{ site.Params.author }} · Updated {{ .Lastmod.Format \"Jan 2, 2006\" }} · {{ .ReadingTime }} min read</div>\n      </div>\n      <figure class=\"article-hero-image\">\n        {{ $image := .Params.image | default site.Params.defaultImage }}\n        <img src=\"{{ $image }}\" alt=\"{{ .Params.image_alt | default (printf \"Featured image for %s\" .Title) }}\">\n      </figure>\n    </div>\n  </header>\n  <div class=\"container article-layout\">\n    <aside class=\"toc-wrap\">\n      <div class=\"toc-card\"><strong>On this page</strong>{{ .TableOfContents }}</div>\n    </aside>\n    <div class=\"article-content\">\n      {{ .Content }}\n      <section class=\"disclaimer-box\">\n        <h2>DIY safety disclaimer</h2>\n        <p>{{ site.Params.disclaimer }}</p>\n      </section>\n      <section class=\"article-taxonomy\">\n        <h2>Related topics</h2>\n        <div class=\"tag-list\">{{ range .Params.categories }}<a href=\"{{ printf \"/categories/%s/\" . }}\">{{ partial \"category-title.html\" . }}</a>{{ end }}{{ range .Params.tags }}<span>{{ . }}</span>{{ end }}</div>\n      </section>\n    </div>\n  </div>\n  <section class=\"container related-section\">\n    <div class=\"section-heading split\"><div><p class=\"eyebrow\">Keep learning</p><h2>Related leak repair guides</h2></div></div>\n    <div class=\"article-grid\">\n      {{ $cats := .Params.categories }}\n      {{ $shown := 0 }}\n      {{ range where site.RegularPages \"Section\" \"articles\" }}\n        {{ if and (ne .RelPermalink $.RelPermalink) (gt (len (intersect .Params.categories $cats)) 0) (lt $shown 6) }}\n          {{ partial \"article-card.html\" . }}\n          {{ $shown = add $shown 1 }}\n        {{ end }}\n      {{ end }}\n    </div>\n  </section>\n</article>\n{{ else }}\n<section class=\"page-hero compact\"><div class=\"container\"><h1>{{ .Title }}</h1>{{ with .Description }}<p class=\"lead\">{{ . }}</p>{{ end }}</div></section>\n<section class=\"container page-content article-content\">{{ .Content }}</section>\n{{ end }}\n{{ end }}\n""", encoding="utf-8")

# Schema should expose human-readable articleSection labels even though taxonomy stores slugs.
schema_path = ROOT / "layouts" / "partials" / "schema.html"
schema_text = schema_path.read_text(encoding="utf-8")
schema_text = schema_text.replace('{{ $desc := .Description | default .Params.description | default site.Params.description | plainify | htmlUnescape }}', '{{ $desc := .Description | default .Params.description | default site.Params.description | plainify | htmlUnescape }}\n{{ $sections := slice }}\n{{ range .Params.categories }}{{ $sections = $sections | append (partial "category-title.html" .) }}{{ end }}')
schema_text = schema_text.replace('"articleSection": {{ .Params.categories | jsonify }},', '"articleSection": {{ $sections | jsonify }},')
schema_path.write_text(schema_text, encoding="utf-8")

# CSS: make body a column flex container so short pages do not leave white space below the footer.
css_files = list((ROOT / "assets").rglob("*.css")) + list((ROOT / "static").rglob("*.css"))
if css_files:
    css_path = css_files[0]
    css = css_path.read_text(encoding="utf-8")
    if "body{min-height:100vh;display:flex;flex-direction:column}" not in css:
        css = css.replace("*{box-sizing:border-box}", "*{box-sizing:border-box}html{min-height:100%}")
        css = css.replace("body{margin:0;", "body{min-height:100vh;display:flex;flex-direction:column;margin:0;")
        css = css.replace("main{display:block}", "main{display:block;flex:1 0 auto}")
        css = css.replace(".site-footer{background:", ".site-footer{flex-shrink:0;background:")
        css_path.write_text(css, encoding="utf-8")

print(f"Updated category front matter in {changed_files} article files.")
print("Patched category display templates, schema category labels, and sticky footer CSS.")
