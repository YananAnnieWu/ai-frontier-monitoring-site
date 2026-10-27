# AI Frontier Monitoring — public site v1

An intentionally **public-only editorial website**, separate from the private research and ingestion systems. Contains curated paper metadata, original short summaries, one launch report and methods. No raw candidate database, raw abstracts, GPT batch JSONs, internal analysis history or Drive material.

## Reproduce the static site

Requirements: Python 3.10+ (standard library only).

```bash
python scripts/build.py
python scripts/check.py
python -m http.server 8000 --directory site
```

Preview at `http://localhost:8000`. The site generator reads **only** `content/papers.json`, `content/issue.json` and `content/site.json`. All content is intentionally public. Avoid adding private exports, personal data, API keys, or source analysis packets to this repository.

## Publish on GitHub Pages

1. Create a **new, public** GitHub repository, e.g. `ai-frontier-monitoring-site`. **Do not** change the private ingestion repository to public.
2. Upload the contents of this directory (or push them with Git). Set the default branch to `main`.
3. Repository **Settings → Pages → Build and deployment → Source → GitHub Actions**. The included workflow `.github/workflows/pages.yml` builds, validates and deploys the static website on push to `main`.
4. For local-only first publication, use the separately supplied `ai-frontier-public-built-v1.zip` as a static-site archive. The preferred long-term deployment is the source repository and Actions workflow.

The live website URL is assigned by GitHub only after a successful Pages deployment. Do not infer that a URL is live simply because files were generated.

## Editorial workflow

- Source material is collected and analyzed in a **separate private environment**.
- Curate only externally shareable DOI-linked papers in `content/papers.json`; all site-facing fields are an explicit allowlist.
- Draft reports in `content/issue.json`, which should receive an editorial check before public release.
- Commit the reviewed content. The build regenerates all HTML; Git history forms the public version record.
- Never let the public repo's CI fetch from the private repo or Drive. There is **no automatic transfer** between the two systems by design.

## Content discipline

- Link to primary DOI records, not paywalled copies.
- State findings conservatively and separate study claims from interpretation.
- Do not claim full-text review when only abstract or source excerpts were checked.
- No copied full abstracts or long copyrighted text passages.
- This is a selective research brief, not an exhaustive systematic review or clinical guidance.

## Files

- `content/`: small public editorial data files, not the screening database.
- `scripts/build.py`: deterministic site generator.
- `scripts/check.py`: privacy/DOI, content and internal link checks.
- `assets/`: design CSS and zero-dependency interactive search.
- `site/`: generated HTML, also suitable for static hosting.
- `.github/workflows/pages.yml`: public Pages deployment with source-only permissions.

All commentary is editorial, and links lead to the original publications for verification. This website is not affiliated with the journals or publishers it cites.
