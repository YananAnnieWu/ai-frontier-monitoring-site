#!/usr/bin/env python3
"""Pre-publication QA: minimal PII/secret hygiene, canonical DOI and local link checks."""
from __future__ import annotations
from html.parser import HTMLParser
import json
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit, unquote
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'site'
REQUIRED={
 'index.html','reports/index.html','papers/index.html',
 'themes/index.html','methodology/index.html','archive/index.html','404.html',
 'assets/style.css','assets/app.js','assets/favicon.svg','data/featured-papers.json','.nojekyll'
}
PUBLIC_KEYS={'doi','title','journal','year','theme','type','summary','why','caution','featured'}
FORBIDDEN=[
 'github.com/',
 'drive.google.com', 'docs.google.com', 'sqlite', '.db-journal',
 'OPENALEX_API_KEY', 'GH_TOKEN', 'BEGIN PRIVATE KEY', 'AIza',
 'review_packets/', 'fast_screenings', 'file_00000000',
 'source_occurrences',
]
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs=[];self.bad_blank=[];self.ids=set();self.has_main=False
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.add(d['id'])
        if tag=='main':self.has_main=True
        if tag in ('a','link','script','img'):
            attr={'a':'href','link':'href','script':'src','img':'src'}[tag]
            if attr in d:self.hrefs.append((tag,d[attr]))
        if tag=='a' and d.get('target')=='_blank' and 'noopener' not in d.get('rel',''):
            self.bad_blank.append(d.get('href',''))

def validate():
    problems=[]
    files={x.relative_to(OUT).as_posix() for x in OUT.rglob('*') if x.is_file()}
    for f in REQUIRED-files:problems.append('Missing '+f)
    papers=json.loads((ROOT/'content/papers.json').read_text())
    public=json.loads((OUT/'data/featured-papers.json').read_text())
    issue_files=sorted((ROOT/'content/issues').glob('*.json'))
    themes=json.loads((ROOT/'content/themes.json').read_text())
    if not isinstance(papers,list) or not papers or not isinstance(public,list) or public!=papers:
        problems.append('Missing or inconsistent public paper catalogue')
    if not isinstance(themes,dict) or not themes or any(not k or not isinstance(v,str) or not v for k,v in themes.items()):
        problems.append('Invalid editable theme index')
    if not all(set(p)==PUBLIC_KEYS for p in papers):problems.append('Paper content must use explicit public field allowlist')
    dois=[x['doi'] for x in papers]
    if len(set(dois))!=len(dois):problems.append('Duplicate DOI')
    for p in papers:
        if p.get('theme') not in themes:problems.append('Unlisted theme '+repr(p.get('theme')))
        if not isinstance(p.get('year'),int) or not 1900<=p['year']<=2200:
            problems.append('Invalid publication year '+p.get('doi','?'))
        if not isinstance(p.get('featured'),bool):problems.append('Nonboolean feature flag '+p.get('doi','?'))
    ids=set();issues=[];pairs=set()
    if not issue_files:problems.append('No dated issues found')
    for path in issue_files:
        try:issue=json.loads(path.read_text(encoding='utf-8'))
        except (ValueError,UnicodeError) as e:
            problems.append('Malformed issue JSON '+path.name+': '+str(e));continue
        issue_id=issue.get('id','')
        if not re.fullmatch(r'[0-9]{3}',str(issue_id)) or path.stem!=issue_id:
            problems.append('Issue ID must equal its 3-digit JSON filename '+path.name)
        if issue_id in ids:problems.append('Repeated issue ID '+str(issue_id))
        ids.add(issue_id)
        try:
            pub_date=date.fromisoformat(issue.get('date',''))
            if pub_date.isoformat()!=issue['date']:raise ValueError('non-ISO publication date')
        except (ValueError,TypeError):problems.append('Invalid issue publication date '+str(issue_id))
        pair=(issue.get('date'),issue_id)
        if pair in pairs:problems.append('Duplicate publication edition '+str(pair))
        pairs.add(pair)
        for required_key in ('title','subtitle','lead','scope'):
            if not isinstance(issue.get(required_key),str) or not issue[required_key].strip():
                problems.append('Incomplete issue '+str(issue_id)+' / '+required_key)
        if not isinstance(issue.get('watchlist'),list) or not all(isinstance(w,str) and w.strip() for w in issue['watchlist']):
            problems.append('Invalid issue watchlist '+str(issue_id))
        if not isinstance(issue.get('signals'),list) or not issue['signals']:
            problems.append('Issue has no research signals '+str(issue_id))
        else:
            for signal in issue['signals']:
                for key in ('eyebrow','title','body','takeaway'):
                    if not isinstance(signal.get(key),str) or not signal[key].strip():
                        problems.append('Incomplete signal '+str(issue_id)+' / '+key)
                if not isinstance(signal.get('dois'),list) or not signal['dois']:
                    problems.append('Signal has no DOI references '+str(issue_id))
                else:
                    for doi in signal['dois']:
                        if doi not in dois:problems.append('Issue '+str(issue_id)+' references unlisted DOI '+str(doi))
        required_issue_page='reports/issue-'+str(issue_id)+'/index.html'
        if required_issue_page not in files:problems.append('Missing generated issue page '+required_issue_page)
        issues.append(issue)
    for p in papers:
        if not re.match(r'^10\.\d{4,9}/[^\s<>]+$',p.get('doi','')):problems.append('Invalid DOI '+repr(p.get('doi')))
        if not p.get('caution') or not p.get('summary') or not p.get('why'):problems.append('Incomplete editorial boundary '+p['doi'])
        if len(p['summary'])>490 or len(p['caution'])>490:problems.append('Overlong public note '+p['doi'])
        if f"https://doi.org/{p['doi']}" not in (OUT/'papers'/('p-'+re.sub(r'[^a-z0-9]+','-',p['doi'].lower()).strip('-'))/'index.html').read_text():
            problems.append('No original source DOI in paper note '+p['doi'])
    for f in OUT.rglob('*'):
        if not f.is_file() or f.suffix not in ('.html','.css','.js','.json','.svg','.txt'):continue
        contents=f.read_text(encoding='utf-8')
        for needle in FORBIDDEN:
            if needle.lower() in contents.lower():problems.append('Sensitive/private marker in public output '+str(f.relative_to(OUT))+' ['+needle+']')
        if f.suffix!='.html':continue
        parsed=Parser();parsed.feed(contents)
        if not parsed.has_main:problems.append('Missing main landmark '+str(f))
        if parsed.bad_blank:problems.append('External tab without noopener '+str(f))
        for tag,link in parsed.hrefs:
            if not link or link.startswith('#'):
                if link.startswith('#') and link[1:] not in parsed.ids:
                    problems.append('Missing in-page anchor '+str(f)+': '+link)
                continue
            parts=urlsplit(link)
            if parts.scheme or parts.netloc or link.startswith('mailto:'):continue
            target=(f.parent/unquote(parts.path)).resolve()
            if parts.path=='':target=f
            if target.is_dir():target=target/'index.html'
            if not target.is_file():problems.append('Broken local link '+f.relative_to(OUT).as_posix()+' -> '+link)
            elif parts.fragment and target.suffix=='.html':
                sub=Parser();sub.feed(target.read_text())
                if unquote(parts.fragment) not in sub.ids:
                    problems.append('Broken fragment link '+f.relative_to(OUT).as_posix()+' -> '+link)
    if any(f.name.lower().endswith(('.sqlite','.xlsx','.pdf','.zip','.jsonl')) for f in OUT.rglob('*') if f.is_file()):
        problems.append('Disallowed raw/archive type present in public output')
    if problems:
        print('PUBLICATION QA FAILED:\n'+'\n'.join('- '+x for x in problems),file=sys.stderr)
        raise SystemExit(1)
    count=len(list(OUT.rglob('*.html')))
    print(json.dumps({'status':'PUBLICATION QA PASS','html_pages':count,'selected_papers':len(papers),
                      'issues':len(issues),'research_signals':sum(len(issue['signals']) for issue in issues),'private_links_or_raw_databases':0,
                      'broken_links':0},indent=2))

if __name__=='__main__':validate()
