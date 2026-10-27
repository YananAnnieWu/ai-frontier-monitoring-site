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
ISSUE = json.loads((ROOT / "content/issue.json").read_text(encoding="utf-8"))
CONFIG = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
THEMES = {
    "AI agents": "Collaboration, tool use and autonomous research workflows.",
    "AI reliability": "Confidence, evaluation, reference standards and measurement.",
    "Human–AI interaction": "Explanations, trust, calibrated reliance and user expertise.",
    "Clinical AI": "Clinical model evaluation, dynamic diagnosis and safety boundaries.",
    "AI for science": "Computational methods linked to experimental discovery.",
    "AI & organizations": "Innovation, work design, managerial decisions and markets.",
    "AI governance": "Alignment, incentives, accountability and societal risks.",
}


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
        ("Overview", "", "home"), ("Reports", "reports/", "reports"),
        ("Featured papers", "papers/", "papers"), ("Research areas", "themes/", "themes"),
        ("Methodology", "methodology/", "methodology"), ("Archive", "archive/", "archive"),
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
    <span><span class="brand-title">AI Frontier Monitoring</span><span class="brand-sub">Independent research observatory</span></span>
  </a>
  <button class="menu-toggle" type="button" aria-label="Toggle navigation" aria-controls="primary-nav" aria-expanded="false" data-menu-toggle>Menu</button>
  <nav class="nav-links" id="primary-nav" aria-label="Primary navigation" data-nav>{nav}</nav>
</div></header>
<main id="main">{body}</main>
<footer class="footer"><div class="container">
 <div class="footer-top"><div><a class="brand" href="{prefix}"><span class="brand-mark" aria-hidden="true">A·</span><span><span class="brand-title">AI Frontier Monitoring</span><span class="brand-sub">Curated. Cited. Revisited.</span></span></a>
 <p style="font-size:.83rem;max-width:380px;margin-top:16px">Independent editorial syntheses and direct links to original research. Not affiliated with the journals or publishers referenced.</p></div>
 <nav aria-label="Footer navigation">{footer_nav}</nav></div>
 <div class="footer-bottom">© 2026 AI Frontier Monitoring · Selective research briefing, not a systematic review or professional advice. · First published 27 October 2026.</div>
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
       <div class="card-bottom"><a class="text-link" href="{link}">View research note</a><a href="{esc(doi_href(p['doi']))}" target="_blank" rel="noopener noreferrer">Original DOI ↗</a></div>
    </article>'''


def build_home():
    featured = [p for p in PAPERS if p["featured"]]
    body=f'''<section class="hero"><div class="container hero-inner">
        <div class="eyebrow"><span class="dot"></span> Volume 01 · October 2026</div>
        <h1>Reading the signal<br>in AI research.</h1>
        <p class="lead">An independent, evidence-aware observatory of work shaping artificial intelligence—across systems, people, healthcare, scientific discovery and organizations.</p>
        <div class="hero-actions"><a class="button button-primary" href="reports/issue-001/">Read the inaugural briefing <span aria-hidden="true">↗</span></a>
         <a class="button button-outline" href="papers/">Explore selected papers</a></div>
        <div class="hero-meta"><span><b>Public edition 001</b> · 27 October 2026</span><span>Original DOI links</span><span>Evidence limits shown</span></div>
      </div></section>
      <section class="section"><div class="container"><div class="section-head"><div><div class="section-kicker">Research briefing</div><h2>This edition's central questions</h2></div><p>Five connected signals from published research, presented with source links and bounded interpretations.</p></div>
      <div class="cards-2"><article class="brief-feature"><span class="tag">Featured editorial · Issue 001</span>
        <h3>{esc(ISSUE['title'])}</h3><p>{esc(ISSUE['lead'])}</p>
        <a class="button button-quiet" href="reports/issue-001/">Read the complete brief <span aria-hidden="true">↗</span></a>
        </article><aside class="brief-side"><span class="eyebrow">Inside this edition</span>
        <h3>From technical capability to practical accountability.</h3>
        <ul><li>When do AI agents benefit from teamwork?</li><li>Can explanations improve—or impair—human oversight?</li><li>How can we tell useful AI science from promising demos?</li><li>Is AI changing the quantity or the nature of work?</li></ul>
        <a href="reports/issue-001/">Explore all five signals ↗</a></aside></div></div></section>
      <section class="section section-alt"><div class="container"><div class="section-head"><div><div class="section-kicker">Paper selection</div><h2>Start with the studies</h2></div><a href="papers/" class="text-link">Browse all {len(PAPERS)} papers</a></div>
      <div class="tile-grid">{''.join(mini_paper(p) for p in featured[:6])}</div></div></section>
      <section class="section"><div class="container"><div class="section-head"><div><div class="section-kicker">Areas of inquiry</div><h2>One frontier, many disciplines</h2></div><p>We follow questions that cross traditional journal and domain boundaries.</p></div>
      <div class="topic-list">{''.join(f'<a class="topic-card" href="themes/#{slug(t)}"><span class="topic-number">{sum(p["theme"]==t for p in PAPERS):02d} selected papers</span><h3>{esc(t)}</h3><p>{esc(d)}</p></a>' for t,d in THEMES.items())}</div></div></section>
      <section class="section-tight section-alt"><div class="container"><div class="disclaimer"><strong>Evidence-first publishing.</strong> Summaries are editorial syntheses based primarily on source-linked abstracts and limited accessible excerpts. We distinguish original research, methods and perspectives, and do not represent these notes as independently verified full-text reviews. <a href="methodology/">Read our methodology ↗</a></div></div></section>'''
    write("index.html",layout("Overview",CONFIG["description"],body,active="home"))


def build_papers():
    options=''.join(f'<option value="{esc(t)}">{esc(t)} ({sum(p["theme"]==t for p in PAPERS)})</option>' for t in THEMES)
    body=heading("Featured papers","A deliberately small, source-linked reading shelf. Each entry explains the contribution and the limits of what the available evidence supports.","papers")+f'''<div class="container main-content">
      <div class="filters"><input class="search-box" type="search" placeholder="Search title, topic, journal, DOI…" aria-label="Search featured papers" data-paper-search>
      <select class="select-box" data-theme-filter aria-label="Filter by research area"><option value="">All research areas</option>{options}</select></div>
      <p class="result-status" role="status" aria-live="polite" data-result-status>{len(PAPERS)} selected papers shown</p>
      <div class="paper-list">{''.join(paper_card(p) for p in PAPERS)}</div>
      <div class="disclaimer" style="margin-top:32px">This is an editorial selection, not a ranked list or a complete database. DOI links lead to publishers or registered primary records. Study claims must be checked against the original publication before use in new research.</div>
      </div>'''
    write("papers/index.html",layout("Featured papers","Selected published AI research with DOI links, findings, significance and caveats.",body,depth=1,active="papers"))
    for p in PAPERS:
        src=doi_href(p['doi'])
        body=f'''{heading(p['title'],f"{p['journal']} · {p['year']} · {p['type']}","papers / research note",depth=2)}
          <section class="main-content"><div class="container"><div class="reading-shell">
          <div class="pill-row"><span class="tag">{esc(p['theme'])}</span><span class="tag tag-soft">Editorial research note</span></div>
          <div class="paper-fact"><div class="fact"><div class="label">Journal</div><div>{esc(p['journal'])}</div></div>
          <div class="fact"><div class="label">Source and identity</div><div><a href="{esc(src)}" target="_blank" rel="noopener noreferrer">{esc(p['doi'])} ↗</a></div></div></div>
          <h2>What the study examines</h2><p>{esc(p['summary'])}</p>
          <h2>Why it matters</h2><p>{esc(p['why'])}</p>
          <h2>Interpretation boundary</h2><p>{esc(p['caution'])}</p>
          <div class="disclaimer">This is a short editorial synthesis primarily based on publication abstracts and source-linked material; it is not a claim of full-text verification. For precise methods, effect sizes or limitations, consult the original article.</div>
          <p style="margin-top:30px"><a class="button button-primary" href="{esc(src)}" target="_blank" rel="noopener noreferrer">Open original DOI ↗</a></p>
          <p><a href="../">← Back to all featured papers</a></p>
          </div></div></section>'''
        write("papers/"+slug(p['doi'])+"/index.html",layout(p["title"],p["summary"],body,depth=2,active="papers",page_type="article"))


def build_reports():
    body=heading("Research reports","Curated syntheses that connect papers into research questions, track implications and state what remains uncertain.","reports")+f'''<section class="main-content"><div class="container">
       <article class="archive-row"><div><div class="section-kicker">Issue {esc(ISSUE['id'])} · {esc(ISSUE['date'])}</div>
       <h3><a href="issue-001/">{esc(ISSUE['title'])}</a></h3><p>{esc(ISSUE['subtitle'])}</p></div><div class="archive-meta">{len(ISSUE['signals'])} research signals<br>Inaugural edition</div></article>
       <p class="section-note" style="margin-top:22px">Reports are published as dated editions. A future substantive correction will be documented in the public archive.</p>
       </div></section>'''
    write("reports/index.html",layout("Reports","Dated editorial research reports and cross-disciplinary AI frontier briefs.",body,depth=1,active="reports"))
    signal_html=[]
    byid={p['doi']:p for p in PAPERS}
    for s in ISSUE['signals']:
        refs=''.join(f'<a href="{page_href(doi,2)}">{esc(byid[doi]["journal"])} · {esc(byid[doi]["year"])} ↗</a>' for doi in s['dois'])
        signal_html.append(f'''<section class="signal"><div class="eyebrow">{esc(s['eyebrow'])}</div><h2>{esc(s['title'])}</h2>
          <p>{esc(s['body'])}</p><div class="takeaway">What to watch: {esc(s['takeaway'])}</div>
          <div class="source-list" aria-label="References for this signal">Read the original studies through their linked notes: {refs}</div></section>''')
    items=''.join(f'<li>{esc(x)}</li>' for x in ISSUE['watchlist'])
    body=f'''<section class="page-hero"><div class="container"><div class="breadcrumbs"><a href="../../">Home</a> / <a href="../">Reports</a> / Issue 001</div>
     <div class="section-kicker" style="margin-top:24px">Research briefing · Volume 01</div><h1>{esc(ISSUE['title'])}</h1><p>{esc(ISSUE['subtitle'])}</p>
     <div class="byline"><span>Published {esc(ISSUE['date'])}</span><span>5 signals</span><span>Selective editorial synthesis</span></div></div></section>
     <section class="main-content"><div class="container"><article class="reading-shell"><p class="report-lead">{esc(ISSUE['lead'])}</p>
       <p>We organize this issue around research questions rather than performance headlines. Each signal points to selected source publications and explicitly distinguishes the evidence from wider inferences.</p>
       {''.join(signal_html)}
       <h2>Questions for the next edition</h2><ol>{items}</ol>
       <div class="disclaimer" style="margin-top:30px"><strong>Scope and evidence.</strong> {esc(ISSUE['scope'])}</div>
       <p style="margin-top:30px"><a href="../">← All research reports</a></p>
     </article></div></section>'''
    write("reports/issue-001/index.html",layout(ISSUE['title'],ISSUE['subtitle'],body,depth=2,active="reports",page_type="article"))


def build_themes():
    blocks=[]
    for i,(t,d) in enumerate(THEMES.items(),1):
        ps=[p for p in PAPERS if p['theme']==t]
        blocks.append(f'''<section class="signal" id="{slug(t)}"><div class="eyebrow">Research area {i:02d} · {len(ps)} selected studies</div>
           <h2>{esc(t)}</h2><p>{esc(d)}</p>
           <ul>{''.join(f'<li><a href="{page_href(p["doi"],1)}">{esc(p["title"])}</a> <span class="section-note">— {esc(p["journal"])}</span></li>' for p in ps)}</ul></section>''')
    body=heading("Research areas","A question-led map of selected AI work across scientific and social domains.","themes")+f'<div class="container main-content"><div class="reading-shell">{"".join(blocks)}</div></div>'
    write("themes/index.html",layout("Research areas","Browse seven research themes and source-linked highlights.",body,depth=1,active="themes"))


def build_methodology():
    body=heading("How we monitor the frontier","A selective, versioned editorial process—not a claim to have exhaustively reviewed the literature.","methodology")+'''<section class="main-content"><div class="container"><article class="reading-shell">
       <p class="report-lead">A useful research observatory needs two things at once: broad discovery and a deliberately narrow public signal.</p>
       <h2>01. Discovery is broader than publication</h2><p>Our monitoring program surveys research across leading general-science, medical, AI-related and business journals. The public site is a separate curated publication layer. It does not expose raw search results, automated classifications, private databases or internal analysis files.</p>
       <h2>02. Selection is editorial—not exhaustive</h2><p>Topic relevance, research design, scientific interest, and verifiable publication information guide which studies become candidates for notes. The website may emphasize studies with clear contributions or notable editorial attention, but attention and journal prestige are not substitutes for evidence.</p>
       <h2>03. Evidence language is deliberately limited</h2>
       <table class="info-table"><thead><tr><th>Label</th><th>Meaning for public notes</th></tr></thead><tbody>
       <tr><td>Publication-linked</td><td>The title and DOI point to a registered original work. The reader should follow the original source for precise methods and figures.</td></tr>
       <tr><td>Abstract-based synthesis</td><td>Core claims are bounded by published abstracts and available source excerpts. No independent complete-text check is claimed.</td></tr>
       <tr><td>Full-text verified</td><td>Reserved for future notes only if the complete source is independently reviewed and that review is documented.</td></tr>
       <tr><td>Editorial interpretation</td><td>Cross-paper trends and recommendations are our synthesis, not statements made verbatim by any one study.</td></tr>
       </tbody></table>
       <h2>04. We track limitations, not just outcomes</h2><p>A convincing benchmark is not automatically a deployment result. Laboratory viability is not clinical effectiveness. A theoretical paper is not an observational estimate. Survey associations are not causal effects. Each selected paper note therefore includes an interpretation boundary.</p>
       <h2>05. Publication and provenance</h2><p>Reports are dated and collected in a public archive. The public site repository contains only its public editorial content and static pages. Source metadata and the wider internal screening workflow remain private and are not connected to this website at build or deployment time. Public revisions are recorded by Git history.</p>
       <h2>06. Intended use</h2><p>These briefs support research discovery and topic formation. They are not a systematic review, clinical guidance, financial advice, or an independent certification of published findings. Readers should verify claims against the linked primary article.</p>
       <div class="disclaimer"><strong>Editorial policy:</strong> Source a paper by DOI, keep the research type clear, label uncertainty and avoid reproducing full copyrighted abstracts or publisher text. Substantive corrections should be versioned and described in the archive.</div>
       </article></div></section>'''
    write("methodology/index.html",layout("Methodology","Transparent and cautious methods for curated AI research monitoring.",body,depth=1,active="methodology"))


def build_archive():
    body=heading("Publication archive","The public record of our editorial editions and significant updates.","archive")+f'''<section class="main-content"><div class="container">
       <div class="section-kicker">2026</div>
       <article class="archive-row"><div><h3><a href="../reports/issue-001/">27 October 2026 · Issue 001</a></h3>
       <p><strong>{esc(ISSUE['title'])}</strong> — the inaugural cross-disciplinary research brief.</p></div><div class="archive-meta">5 research signals<br>16 linked papers</div></article>
       <div class="disclaimer" style="margin-top:30px">Public release 1.0. This archive is intentionally small. Future editions and corrections will be added with explicit dates. Internal review histories, screening databases and unpublished drafts are not part of the public archive.</div>
       </div></section>'''
    write("archive/index.html",layout("Archive","Dated issues and public research editorial updates.",body,depth=1,active="archive"))


def build_404():
    body='<div class="container main-content"><div class="reading-shell"><div class="section-kicker">Page not found</div><h1>That page is not here.</h1><p>The research note may have moved or the link may be incorrect.</p><a class="button button-quiet" href="./">Return to overview</a></div></div>'
    write("404.html",layout("Page not found","This address does not match a published page.",body,depth=0))


def build():
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT/"assets",OUT/"assets")
    (OUT/".nojekyll").write_text("",encoding="utf-8")
    (OUT/"robots.txt").write_text("User-agent: *\nAllow: /\n",encoding="utf-8")
    build_home();build_papers();build_reports();build_themes();build_methodology();build_archive();build_404()
    # Build a portable, public-only catalogue for future editorial workflows.
    safe_keys=("doi","title","journal","year","theme","type","summary","why","caution","featured")
    catalogue=[{k:p[k] for k in safe_keys} for p in PAPERS]
    write("data/featured-papers.json",json.dumps(catalogue,ensure_ascii=False,indent=2)+"\n")
    print(f"Generated {len(list(OUT.rglob('index.html')))} index pages and {len(PAPERS)} research notes at {OUT}")

if __name__=="__main__":build()
