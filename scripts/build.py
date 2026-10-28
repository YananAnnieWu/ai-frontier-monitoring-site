#!/usr/bin/env python3
"""Build a fully static, intentionally public-only research website.

Only reads three explicit public content files. Zero network, zero access to
private databases, unpublished review packets, Drive, or credentials.
"""
import html
import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site"
PAPERS = json.loads((ROOT / "content/papers.json").read_text(encoding="utf-8"))
CONFIG = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
THEMES = json.loads((ROOT / "content/themes.json").read_text(encoding="utf-8"))
ISSUE_FILES = sorted((ROOT / "content/issues").glob("[0-9][0-9][0-9].json"))
ISSUES = [json.loads(p.read_text(encoding="utf-8")) for p in ISSUE_FILES]
ISSUES.sort(key=lambda issue: (issue["date"], issue["id"]), reverse=True)
if not ISSUES:
    raise ValueError("At least one public issue JSON is required")
ISSUE = ISSUES[0]  # newest dated published issue


def issue_path(issue):
    return "issue-" + issue["id"] + "/"


def issue_date(issue):
    return datetime.strptime(issue["date"], "%Y-%m-%d").strftime("%d %B %Y")


def esc(v):
    return html.escape(str(v), quote=True)


def slug(doi):
    return "p-" + re.sub(r"[^a-z0-9]+", "-", doi.lower()).strip("-")


def page_href(doi, depth):
    return "../" * depth + "papers/" + slug(doi) + "/"


def doi_href(doi):
    return "https://doi.org/" + doi


def write(rel, text):
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def layout(title, desc, body, *, depth=0, active="", page_type="website"):
    prefix = "../" * depth
    nav_items = [
        ("Home", "", "home"), ("Reports", "reports/", "reports"),
        ("Papers", "papers/", "papers"), ("Topics", "themes/", "themes"),
        ("Archive", "archive/", "archive"),
    ]
    nav = "\n".join(f'<a href="{prefix}{dest}" {"aria-current=\"page\"" if active==key else ""}>{esc(label)}</a>' for label, dest, key in nav_items)
    footer_nav = "".join(f'<a href="{prefix}{dest}">{esc(label)}</a>' for label, dest, key in nav_items[1:])
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#102e37">
  <meta name="description" content="{esc(desc)}">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="robots" content="noindex, nofollow">
  <meta property="og:type" content="{esc(page_type)}">
  <meta property="og:title" content="{esc(title)} — AI Frontier Monitoring">
  <meta property="og:description" content="{esc(desc)}">
  <title>{esc(title)} | AI Frontier Monitoring</title>
  <link rel="icon" type="image/svg+xml" href="{prefix}assets/favicon.svg">
  <link rel="stylesheet" href="{prefix}assets/style.css">
  <script src="{prefix}assets/app.js" defer></script>
</head>
<body>
<a href="#main" class="skip">Skip to content</a>
<header class="site-header"><div class="container head-row">
  <a href="{prefix}" class="brand" aria-label="AI Frontier Monitoring home">
    <span class="brand-mark" aria-hidden="true">A<span style="font-size:.65em">·</span></span>
    <span><span class="brand-title">AI Frontier Monitoring</span><span class="brand-sub">Research reference</span></span>
  </a>
  <button class="menu-toggle" type="button" aria-label="Toggle navigation" aria-controls="primary-nav" aria-expanded="false" data-menu-toggle>Menu</button>
  <nav class="nav-links" id="primary-nav" aria-label="Primary navigation" data-nav>{nav}</nav>
</div></header>
<main id="main">{body}</main>
<footer class="footer"><div class="container">
 <div class="footer-top"><div><a class="brand" href="{prefix}"><span class="brand-mark" aria-hidden="true">A·</span><span><span class="brand-title">AI Frontier Monitoring</span><span class="brand-sub">Research notes and sources</span></span></a>
 <p style="font-size:.83rem;max-width:380px;margin-top:16px">Research reports, selected papers and original-source links.</p></div>
 <nav aria-label="Footer navigation">{footer_nav}</nav></div>
 <div class="footer-bottom">AI Frontier Monitoring · Research reference · Verify findings against the original publications.</div>
</div></footer>
</body></html>'''


def heading(title, subtitle, crumb, depth=1):
    return f'''<section class="page-hero"><div class="container">
      <div class="breadcrumbs"><a href="{'../'*depth}" >Home</a> / {esc(crumb.replace('/',' / '))}</div>
      <h1>{esc(title)}</h1><p>{esc(subtitle)}</p>
    </div></section>'''


def article_link(p, depth=0, label="Read editorial note"):
    return f'<a class="text-link" href="{page_href(p["doi"], depth)}">{esc(label)}</a>'


def mini_paper(p, depth=0):
    href=page_href(p["doi"],depth)
    return f'''<article class="tile"><span class="mini">{esc(p['theme'])} · {esc(p['type'])}</span>
       <h3><a href="{href}">{esc(p['title'])}</a></h3><p>{esc(p['summary'])}</p>
       <div class="paper-source"><span>{esc(p['journal'])}</span><span>{p['year']}</span></div></article>'''


def paper_card(p, depth=1):
    link=page_href(p["doi"],depth)
    meta=" ".join([p["title"],p["journal"],p["doi"],p["theme"],p["summary"]]).lower()
    return f'''<article class="paper-card" data-paper-card data-search="{esc(meta)}" data-theme="{esc(p['theme'])}">
       <div class="pill-row"><span class="tag">{esc(p['theme'])}</span><span class="tag tag-soft">{esc(p['type'])}</span></div>
       <h3><a href="{link}">{esc(p['title'])}</a></h3>
       <p>{esc(p['summary'])}</p>
       <div class="paper-source"><span>{esc(p['journal'])}</span><span>{p['year']}</span></div>
       <div class="card-bottom"><a class="text-link" href="{link}">Read note</a><a href="{esc(doi_href(p['doi']))}" target="_blank" rel="noopener noreferrer">Original DOI ↗</a></div>
    </article>'''


def build_home():
    featured = [p for p in PAPERS if p["featured"]]
    latest_href = "reports/" + issue_path(ISSUE)
    followups = ''.join(f'<li>{esc(question)}</li>' for question in ISSUE['watchlist'][:4])
    body=f'''<section class="hero"><div class="container hero-inner">
        <div class="eyebrow">Issue {esc(ISSUE['id'])} · {esc(ISSUE['date'])}</div>
        <h1>AI literature tracking</h1>
        <p class="lead">Research reports, selected papers, and references organized by topic.</p>
        <div class="hero-actions"><a class="button button-primary" href="{latest_href}">Latest report</a>
         <a class="button button-outline" href="papers/">Browse papers</a></div>
        <div class="hero-meta"><span>{len(ISSUES)} reports</span><span>{len(PAPERS)} papers</span><span>{len(THEMES)} topics</span></div>
      </div></section>
      <section class="section"><div class="container"><div class="section-head"><div><div class="section-kicker">Reports</div><h2>Latest report</h2></div><a class="text-link" href="reports/">All reports</a></div>
      <div class="cards-2"><article class="brief-feature"><span class="tag">Issue {esc(ISSUE['id'])} · {esc(ISSUE['date'])}</span>
        <h3>{esc(ISSUE['title'])}</h3><p>{esc(ISSUE['lead'])}</p>
        <a class="button button-quiet" href="{latest_href}">View report</a>
        </article><aside class="brief-side"><span class="eyebrow">Follow-up questions</span>
        <ul>{followups}</ul></aside></div></div></section>
      <section class="section section-alt"><div class="container"><div class="section-head"><div><div class="section-kicker">References</div><h2>Selected papers</h2></div><a href="papers/" class="text-link">View all {len(PAPERS)} papers</a></div>
      <div class="tile-grid">{''.join(mini_paper(p) for p in featured[:6])}</div></div></section>
      <section class="section"><div class="container"><div class="section-head"><div><div class="section-kicker">Index</div><h2>Topics</h2></div><a href="themes/" class="text-link">All topics</a></div>
      <div class="topic-list">{''.join(f'<a class="topic-card" href="themes/#{slug(t)}"><span class="topic-number">{sum(p["theme"]==t for p in PAPERS):02d} papers</span><h3>{esc(t)}</h3><p>{esc(d)}</p></a>' for t,d in THEMES.items())}</div></div></section>'''
    write("index.html",layout("Home",CONFIG["description"],body,active="home"))


def build_papers():
    options=''.join(f'<option value="{esc(t)}">{esc(t)} ({sum(p["theme"]==t for p in PAPERS)})</option>' for t in THEMES)
    body=heading("Papers","Research notes and links to original publications.","papers")+f'''<div class="container main-content">
      <div class="filters"><input class="search-box" type="search" placeholder="Search title, topic, journal, DOI…" aria-label="Search papers" data-paper-search>
      <select class="select-box" data-theme-filter aria-label="Filter by research area"><option value="">All research areas</option>{options}</select></div>
      <p class="result-status" role="status" aria-live="polite" data-result-status>{len(PAPERS)} selected papers shown</p>
      <div class="paper-list">{''.join(paper_card(p) for p in PAPERS)}</div>
      <div class="disclaimer" style="margin-top:32px">Selected references only; not the complete research database. Check the original paper for specific methods and results.</div>
      </div>'''
    write("papers/index.html",layout("Papers","Selected papers with DOI links and research notes.",body,depth=1,active="papers"))
    for p in PAPERS:
        src=doi_href(p['doi'])
        body=f'''{heading(p['title'],f"{p['journal']} · {p['year']} · {p['type']}","papers / research note",depth=2)}
          <section class="main-content"><div class="container"><div class="reading-shell">
          <div class="pill-row"><span class="tag">{esc(p['theme'])}</span><span class="tag tag-soft">Research note</span></div>
          <div class="paper-fact"><div class="fact"><div class="label">Journal</div><div>{esc(p['journal'])}</div></div>
          <div class="fact"><div class="label">Source and identity</div><div><a href="{esc(src)}" target="_blank" rel="noopener noreferrer">{esc(p['doi'])} ↗</a></div></div></div>
          <h2>What the study examines</h2><p>{esc(p['summary'])}</p>
          <h2>Research relevance</h2><p>{esc(p['why'])}</p>
          <h2>Limitations and caveats</h2><p>{esc(p['caution'])}</p>
          <div class="disclaimer">Based on available abstracts and source excerpts; independent full-text verification is not implied.</div>
          <p style="margin-top:30px"><a class="button button-primary" href="{esc(src)}" target="_blank" rel="noopener noreferrer">Open original DOI ↗</a></p>
          <p><a href="../">← Back to papers</a></p>
          </div></div></section>'''
        write("papers/"+slug(p['doi'])+"/index.html",layout(p["title"],p["summary"],body,depth=2,active="papers",page_type="article"))


def build_reports():
    rows=[]
    byid={p['doi']:p for p in PAPERS}
    for issue in ISSUES:
        rows.append(f'''<article class="archive-row"><div><div class="section-kicker">Issue {esc(issue['id'])} · {esc(issue['date'])}</div>
           <h3><a href="{issue_path(issue)}">{esc(issue['title'])}</a></h3><p>{esc(issue['subtitle'])}</p></div>
           <div class="archive-meta">{len(issue['signals'])} topics<br>{issue_date(issue)}</div></article>''')
    body=heading("Reports","Research summaries organized by date.","reports")+f'''<section class="main-content"><div class="container">
       {''.join(rows)}
       
       </div></section>'''
    write("reports/index.html",layout("Reports","Reports and research summaries by date.",body,depth=1,active="reports"))
    for issue in ISSUES:
        signal_html=[]
        for signal in issue['signals']:
            refs=''.join(f'<a href="{page_href(doi,2)}">{esc(byid[doi]["journal"])} · {esc(byid[doi]["year"])} ↗</a>' for doi in signal['dois'])
            signal_html.append(f'''<section class="signal"><div class="eyebrow">{esc(signal['eyebrow'])}</div><h2>{esc(signal['title'])}</h2>
              <p>{esc(signal['body'])}</p><div class="takeaway">Follow-up: {esc(signal['takeaway'])}</div>
              <div class="source-list" aria-label="References for this signal">References: {refs}</div></section>''')
        items=''.join(f'<li>{esc(x)}</li>' for x in issue['watchlist'])
        body=f'''<section class="page-hero"><div class="container"><div class="breadcrumbs"><a href="../../">Home</a> / <a href="../">Reports</a> / Issue {esc(issue['id'])}</div>
         <div class="section-kicker" style="margin-top:24px">Report · Issue {esc(issue['id'])}</div><h1>{esc(issue['title'])}</h1><p>{esc(issue['subtitle'])}</p>
         <div class="byline"><span>Published {issue_date(issue)}</span><span>{len(issue['signals'])} topics</span></div></div></section>
         <section class="main-content"><div class="container"><article class="reading-shell"><p class="report-lead">{esc(issue['lead'])}</p>
           
           {''.join(signal_html)}
           <h2>Follow-up questions</h2><ol>{items}</ol>
           <div class="disclaimer" style="margin-top:30px"><strong>Source basis.</strong> {esc(issue['scope'])}</div>
           <p style="margin-top:30px"><a href="../">← All research reports</a></p>
         </article></div></section>'''
        write("reports/"+issue_path(issue)+"index.html",layout(issue['title'],issue['subtitle'],body,depth=2,active="reports",page_type="article"))


def build_themes():
    blocks=[]
    for i,(t,d) in enumerate(THEMES.items(),1):
        ps=[p for p in PAPERS if p['theme']==t]
        blocks.append(f'''<section class="signal" id="{slug(t)}"><div class="eyebrow">Topic {i:02d} · {len(ps)} papers</div>
           <h2>{esc(t)}</h2><p>{esc(d)}</p>
           <ul>{''.join(f'<li><a href="{page_href(p["doi"],1)}">{esc(p["title"])}</a> <span class="section-note">— {esc(p["journal"])}</span></li>' for p in ps)}</ul></section>''')
    body=heading("Topics","Papers grouped by research area.","themes")+f'<div class="container main-content"><div class="reading-shell">{"".join(blocks)}</div></div>'
    write("themes/index.html",layout("Topics",f"Papers organized under {len(THEMES)} topics.",body,depth=1,active="themes"))


def build_archive():
    groups=[]
    current_year=None
    for issue in ISSUES:
        year=issue['date'][:4]
        if year!=current_year:
            groups.append(f'<div class="section-kicker">{esc(year)}</div>')
            current_year=year
        groups.append(f'''<article class="archive-row"><div><h3><a href="../reports/{issue_path(issue)}">{issue_date(issue)} · Issue {esc(issue['id'])}</a></h3>
           <p><strong>{esc(issue['title'])}</strong> — {esc(issue['subtitle'])}</p></div><div class="archive-meta">{len(issue['signals'])} topics</div></article>''')
    body=heading("Archive","Previous reports, grouped by year.","archive")+f'''<section class="main-content"><div class="container">
       {''.join(groups)}
       
       </div></section>'''
    write("archive/index.html",layout("Archive","Previous reports by date.",body,depth=1,active="archive"))


def build_404():
    body='<div class="container main-content"><div class="reading-shell"><div class="section-kicker">Page not found</div><h1>That page is not here.</h1><p>The research note may have moved or the link may be incorrect.</p><a class="button button-quiet" href="./">Return to home</a></div></div>'
    write("404.html",layout("Page not found","This address does not match a published page.",body,depth=0))


def build():
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT/"assets",OUT/"assets")
    (OUT/".nojekyll").write_text("",encoding="utf-8")
    (OUT/"robots.txt").write_text("User-agent: *\nDisallow: /\n",encoding="utf-8")
    build_home();build_papers();build_reports();build_themes();build_archive();build_404()
    # Build a portable, public-only catalogue for future editorial workflows.
    safe_keys=("doi","title","journal","year","theme","type","summary","why","caution","featured")
    catalogue=[{k:p[k] for k in safe_keys} for p in PAPERS]
    write("data/featured-papers.json",json.dumps(catalogue,ensure_ascii=False,indent=2)+"\n")
    print(f"Generated {len(list(OUT.rglob('index.html')))} index pages, {len(ISSUES)} issues and {len(PAPERS)} research notes at {OUT}")

if __name__=="__main__":build()
