# AI Frontier Monitoring — research reference site

A research reference website for reports and selected papers. The site is publicly reachable but intended primarily as a working reference for the research team. It remains separate from private research records. The project tracks AI research broadly, rather than focusing solely on radiology quality control.

## What changes in V2

This is a **reusable content-driven publisher**, not a fixed collection of 16 pages:

- Reports: each dated issue has its own permanent JSON file under `content/issues/NNN.json`, automatically rendered at `/reports/issue-NNN/`.
- Homepage: automatically displays the most recently **dated** published issue.
- Reports and Archive: automatically include **all issues**, grouped by year in the archive.
- Paper shelf: `content/papers.json` can grow; pages, filters and counts are regenerated from the data.
- Research areas: edit `content/themes.json` to add or revise topics without modifying Python templates.
- Publication safeguards: all cited DOIs must exist in the public paper shelf; links, page structure, schema, and privacy rules are checked before deployment.
- Deploy: a push to `main` rebuilds GitHub Pages. Pull requests run the same build and tests **without deploying**, allowing editorial review before merging.

**Do not** copy private SQLite, original abstracts, GPT review packets, Drive archives, drafts, medical records or authentication tokens into this repository. It has no connector to the private repo or Google Drive.

## Standard update procedure

### Publish a new dated report

1. Copy `content/issues/001.json` to `content/issues/002.json` (and later `003.json`, etc.).
2. Change `id` (`"002"`), `date` (`YYYY-MM-DD`), title, subtitle, lead, `signals`, `watchlist`, and scope. The filename must equal the three-digit ID.
3. Every DOI in `signals[].dois` must already be listed in `content/papers.json`. Add any new **approved, publicly appropriate** paper notes there first.
4. Optionally add new theme descriptions in `content/themes.json`. Existing reports stay as their original files and URL paths.
5. Create a pull request for editorial verification; after approval, merge into `main`. GitHub Actions deploys it automatically.

No Python, CSS or HTML changes are required for a new issue or paper. Historical issues are not overwritten; correction to an already published issue should be made in a separate, descriptive PR/commit and documented publicly if substantive.

### Add a paper

Append a JSON object to `content/papers.json` with **exactly**:

`doi`, `title`, `journal`, `year`, `theme`, `type`, `summary`, `why`, `caution`, and `featured`.

The `doi` is the paper's stable identity, `theme` must exist in `content/themes.json`, `featured` is a Boolean, and prose must be an original short synthesis. The site generates the paper page and counts automatically. Do not copy source abstracts wholesale.

### Add a new research area

Add a new name/short description in `content/themes.json`, then assign papers to the new theme.

## Local validation

Python 3.10+ standard library, no extra dependencies:

```bash
python scripts/build.py
python scripts/check.py
python scripts/test_reusability.py
python -m http.server 8000 --directory site
```

Preview locally at `http://localhost:8000`. The **reusability regression test** creates fake issues 002/003, an additional paper, and a new topic **inside a temporary directory only**. Synthetic data is never committed or published.

## Publishing and provenance

- Public deployment: GitHub Pages via `.github/workflows/pages.yml`.
- Site outputs: generated under `site/` (not authoritative; the public JSON inputs and source code are authoritative).
- Public record: issue URLs, Git history, commits, and reviewed pull requests. The issue number is permanent; a correction does not reuse that number for a different edition.
- Editorial reviews: separate claims supported by article abstracts/source excerpts from interpretive synthesis. “Full-text verified” is reserved for documented independent verification.
- The website is a selective briefing service, **not** a systematic literature review or clinical advice.

This repository and its public deployments are deliberately isolated from the private research dataset, including non-selected and unverified candidate publications.

## Website presentation

Navigation: Home, Reports, Papers, Topics, Archive. No Methodology tab or promotional sections. Source and evidence limitations remain in relevant research notes. A `noindex, nofollow` meta tag and robots.txt `Disallow: /` reduce discoverability; **neither makes this public website private**.
