"""Issue 002 correction regression: original DOI accounting and safe publication gate."""
import json
from pathlib import Path
import unittest
from weekly_issue import validate_issue

ROOT=Path(__file__).resolve().parents[1]
OLD_DOIS={
 "10.2196/94543","10.1038/s41746-026-03303-z","10.2196/100531",
 "10.1001/jamanetworkopen.2026.41364","10.1287/mnsc.2024.06477",
 "10.1038/s42256-026-01322-9","10.1126/sciadv.aef5674",
 "10.1126/sciadv.aef6378","10.1287/mksc.2024.0983",
 "10.1287/mnsc.2024.05808","10.1287/mnsc.2024.06771",
 "10.1073/pnas.2610670123"
}
BACKFILL={"10.1287/mnsc.2024.06477","10.1287/mnsc.2024.05808",
          "10.1287/mnsc.2024.06771"}
PENDING={"10.1126/sciadv.aef5674","10.1126/sciadv.aef6378"}


class Issue002Revision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issue=json.loads((ROOT/"content/issues/002.json").read_text())
        cls.paper_catalog=json.loads((ROOT/"content/papers.json").read_text())
        cls.byd={p["doi"]:p for p in cls.paper_catalog}

    def test_original_twelve_have_one_audited_disposition(self):
        selected={p["doi"] for p in self.issue["publications"]}
        self.assertEqual(len(selected),7)
        self.assertEqual(selected|BACKFILL|PENDING,OLD_DOIS)
        self.assertFalse((selected&BACKFILL)|(selected&PENDING)|(BACKFILL&PENDING))
        self.assertTrue(selected.issubset(self.byd))

    def test_week_dates_and_doi_evidence_contract(self):
        self.assertEqual(validate_issue(self.issue,self.byd,"002.json"),"v3")
        self.assertEqual((self.issue["week_start"],self.issue["week_end"]),
                         ("2026-10-26","2026-11-01"))
        self.assertEqual(self.issue["date"],"2026-11-04")
        self.assertEqual(self.issue["coverage"]["checked"],0)
        self.assertEqual(self.issue["coverage"]["unverified"],88)
        self.assertEqual(self.issue["coverage"]["discovered_candidates"],12)
        self.assertEqual(self.issue["coverage"]["screened_candidates"],12)
        self.assertIn("NOT a completed discovery sweep",self.issue["coverage"]["notes"])

    def test_signals_are_limited_to_selected_do_is(self):
        selected={p["doi"] for p in self.issue["publications"]}
        self.assertTrue(all(set(s["dois"]).issubset(selected) for s in self.issue["signals"]))
        self.assertEqual(self.issue["significant_developments"],[])

    def test_stage2_effect_sizes_and_reporting_caveats(self):
        p={x["doi"]:x for x in self.issue["publications"]}
        self.assertIn("17/74",p["10.2196/94543"]["main_finding"])
        self.assertIn("0/72",p["10.2196/94543"]["main_finding"])
        self.assertIn("0.897",p["10.1038/s41746-026-03303-z"]["main_finding"])
        self.assertIn("0.904",p["10.1038/s41746-026-03303-z"]["main_finding"])
        self.assertIn("30.8%",p["10.2196/100531"]["main_finding"])
        self.assertIn("53.4%",p["10.2196/100531"]["main_finding"])
        self.assertIn("8.6%",p["10.1001/jamanetworkopen.2026.41364"]["main_finding"])
        self.assertIn("29.5%",p["10.1001/jamanetworkopen.2026.41364"]["main_finding"])
        self.assertIn("observational",p["10.1001/jamanetworkopen.2026.41364"]["evidence_boundary"].lower())
        self.assertIn("PubMed",self.issue["coverage"]["notes"])
        self.assertIn("HTTP 403",self.issue["coverage"]["notes"])
        self.assertEqual(self.issue["coverage"]["checked"],0)
        self.assertEqual(self.issue["significant_developments"],[])

    def test_preserve_original_issue001_and_no_committed_issue003(self):
        one=json.loads((ROOT/"content/issues/001.json").read_text())
        self.assertEqual(one["id"],"001")
        self.assertNotIn("schema_version",one)
        self.assertFalse((ROOT/"content/issues/003.json").exists())


if __name__=="__main__":
    unittest.main()
