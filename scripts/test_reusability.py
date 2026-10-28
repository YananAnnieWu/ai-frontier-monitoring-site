#!/usr/bin/env python3
"""Smoke-test future editions + additional research without publishing fake items."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SRC = Path(__file__).resolve().parents[1]


def run(folder, expected):
    for f in ("scripts/build.py", "scripts/check.py"):
        subprocess.run([sys.executable, str(folder/f)], cwd=folder, check=True, capture_output=True, text=True)
    for p in expected:
        assert (folder/"site"/p).is_file(), f"Missing expected future page {p}"
    return (folder/"site"/"index.html").read_text(encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory(prefix="frontier-site-regression-") as td:
        dst=Path(td)
        for dirname in ("assets", "scripts", "content"):
            shutil.copytree(SRC/dirname,dst/dirname)
        original=(dst/"content"/"issues"/"001.json").read_bytes()
        run(dst,["reports/issue-001/index.html", "archive/index.html", "papers/index.html"])
        assert not (dst/"site"/"methodology").exists()
        assert "Methodology" not in (dst/"site"/"index.html").read_text(encoding="utf-8")
        template=json.loads(original)
        themes=json.loads((dst/"content"/"themes.json").read_text(encoding="utf-8"))
        themes["New research theme"]="An additional discipline that does not require a template change."
        (dst/"content"/"themes.json").write_text(json.dumps(themes,indent=2,ensure_ascii=False),encoding="utf-8")
        papers=json.loads((dst/"content"/"papers.json").read_text(encoding="utf-8"))
        sample=dict(papers[0]);sample.update({
           "doi":"10.5555/frontier-v2-fixture-01",
           "title":"Synthetic regression-test paper (never published)",
           "theme":"New research theme", "featured":False,
           "summary":"This is a synthetic regression-test record, not actual research.",
           "why":"Proves future records need no code changes.",
           "caution":"Not a real paper and not committed to the repository."
        })
        papers.append(sample)
        (dst/"content"/"papers.json").write_text(json.dumps(papers,indent=2,ensure_ascii=False),encoding="utf-8")
        for number,when in ((2,"2026-11-10"),(3,"2026-11-24")):
            issue=dict(template)
            issue.update({"id":f"{number:03d}","date":when,"title":f"Synthetic issue {number:03d} (test only)",
                          "subtitle":"Regression testing, never published", "signals":[dict(template["signals"][0])],
                          "watchlist":["Did the prior issue remain accessible?"]})
            if number==3:
                issue["signals"][0]["dois"]=[sample["doi"]]
            (dst/"content"/"issues"/f"{number:03d}.json").write_text(json.dumps(issue,ensure_ascii=False,indent=2),encoding="utf-8")
        homepage=run(dst,["reports/issue-001/index.html","reports/issue-002/index.html","reports/issue-003/index.html",
                          "papers/p-10-5555-frontier-v2-fixture-01/index.html"])
        assert "Synthetic issue 003 (test only)" in homepage
        assert "Latest report" in homepage
        assert "Independent research observatory" not in homepage
        assert not (dst/"site"/"methodology").exists()
        reports=(dst/"site"/"reports"/"index.html").read_text(encoding="utf-8")
        archive=(dst/"site"/"archive"/"index.html").read_text(encoding="utf-8")
        for i in ("001","002","003"):
            assert f"issue-{i}/" in reports and f"issue-{i}/" in archive
        assert archive.index("issue-003/") < archive.index("issue-002/") < archive.index("issue-001/")
        assert (dst/"content"/"issues"/"001.json").read_bytes()==original
        # Negative test: a DOI cited by a report but absent from the public shelf is rejected.
        broken=json.loads((dst/"content"/"issues"/"003.json").read_text(encoding="utf-8"))
        broken["signals"][0]["dois"]=["10.9999/nonexistent-doi"]
        (dst/"content"/"issues"/"003.json").write_text(json.dumps(broken),encoding="utf-8")
        failed=subprocess.run([sys.executable,str(dst/"scripts"/"build.py")],cwd=dst,capture_output=True,text=True)
        assert failed.returncode!=0, "Unlisted report DOI should fail closed"
        print("REUSABILITY PASS: additive issues 001/002/003, 17 papers, new theme, archives, latest selection and invalid DOI rejection")


if __name__=="__main__":main()
