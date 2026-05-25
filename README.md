# Home Leak Fix

Home Leak Fix is a Hugo static content authority site for DIY leak diagnosis, waterproofing, drainage, and home repair guidance. The site is designed for Netlify deployment and uses a custom lightweight Hugo layout rather than an external theme dependency.

## What is included

The repository contains the complete Hugo source for the website, including imported long-form Markdown guides, custom templates, SEO partials, category hubs, static assets, and Netlify configuration.

| Area | Implementation |
|---|---|
| Static generator | Hugo Extended `0.161.1` |
| Deployment target | Netlify, publishing the generated `public` directory |
| Content inventory | 200 imported homeowner waterproofing and leak-repair guides |
| Image system | 200 unique optimized WebP featured images sourced from Pixabay |
| Main sections | Knowledge Base, Categories, Start Here, Emergency Guide, Contact |
| SEO output | Canonicals, Open Graph, Twitter cards, article schema, breadcrumbs, RSS, sitemap, robots, and `llms.txt` |

## Local development

Install Hugo Extended, then run the local preview server from the repository root.

```bash
hugo server --disableFastRender
```

Build the production output with the same command Netlify uses.

```bash
hugo --gc --minify
```

## Netlify deployment

The `netlify.toml` file defines the build command and Hugo version.

```toml
[build]
  command = "hugo --gc --minify"
  publish = "public"
```

When connecting this repository to Netlify, use the repository root as the base directory and let Netlify read the existing `netlify.toml` file.

## Content maintenance

Articles live under `content/articles/`. Each article uses YAML front matter with title, description, date, category, tags, featured image, image alt text, and Pixabay attribution metadata. Static images live under `static/images/uploads/`, and the consolidated image-credit data is stored in `data/pixabay_image_credits.json`.

The helper scripts in the repository document the import, image assignment, and audit process used to build the initial site. They are intentionally kept outside the public output so future imports can follow the same structure.
