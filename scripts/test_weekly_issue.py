"""V3 public-only schema negative tests; fixtures stay in memory."""
import copy
import unittest

from weekly_issue import validate_issue


class WeeklyIssueGateTests(unittest.TestCase):
    def setUp(self):
        self.doi = "10.5555/test-only-v3"
        self.papers = {self.doi: {"doi": self.doi, "title": "Synthetic study", "journal": "Example journal"}}
        self.base = {
            "schema_version": 3, "id": "003", "date": "2026-11-09",
            "week_start": "2026-11-02", "week_end": "2026-11-08",
            "title": "Synthetic weekly test", "subtitle": "Test only",
            "lead": "A synthetic record, not an actual publication.",
            "scope": "Synthetic fixture; not valid editorial verification.",
            "watchlist": [],
            "signals": [{"eyebrow":"Test", "title":"Test signal", "body":"Synthetic",
                         "takeaway":"No factual conclusion","dois":[self.doi]}],
            "publications": [{
                "doi": self.doi, "first_online_date": "2026-11-05",
                "publisher_evidence": {
                    "published_at": "2026-11-05", "granularity": "day",
                    "event_type": "journal_first_online", "authority": "publisher",
                    "source_url": "https://publisher.test/research",
                    "retrieved_at": "2026-11-09T09:00:00+08:00",
                    "verification_status": "verified", "conflicting": False,
                },
                "contribution": "Synthetic contribution",
                "main_finding": "Synthetic finding",
                "evidence_boundary": "Synthetic evidence limitation",
            }],
            "significant_developments": [],
            "coverage": {"target_journals": 88, "checked": 0, "partial": 0,
                         "failed": 0, "unverified": 88, "discovered_candidates": 1,
                         "screened_candidates": 1,
                         "notes": "Synthetic test has zero publisher checks."},
        }

    def reject(self, change):
        obj=copy.deepcopy(self.base)
        change(obj)
        with self.assertRaises((ValueError, TypeError, KeyError)):
            validate_issue(obj, self.papers, "003.json")

    def test_valid_week_and_historical_compatibility(self):
        self.assertEqual(validate_issue(self.base,self.papers,"003.json"),"v3")
        self.assertEqual(validate_issue({"id":"001"},self.papers,"001.json"),"legacy")
        self.assertEqual(validate_issue({"id":"002"},self.papers,"002.json"),"legacy")

    def test_future_and_partial_weeks_rejected(self):
        self.reject(lambda x:x.update(date="2026-11-08"))
        self.reject(lambda x:x.update(week_start="2026-11-03"))
        self.reject(lambda x:x.update(week_end="2026-11-07"))
        self.reject(lambda x:x["publications"][0].update(first_online_date="2026-10-30"))
        self.reject(lambda x:x["publications"][0].update(first_online_date="2026-11-09"))
        self.reject(lambda x:x["publications"][0].update(first_online_date="2026-11-06"))

    def test_metadata_preprint_and_weak_date_rejected(self):
        for change in (
            {"verification_status":"unverified"}, {"conflicting":True},
            {"authority":"index"}, {"event_type":"preprint"},
            {"event_type":"print_issue"}, {"granularity":"incomplete"},
            {"source_url":"https://github.com/example/paper"},
            {"published_at":"2026-11"}, {"retrieved_at":"2026-11-09"}
        ):
            with self.subTest(change=change):
                self.reject(lambda x:x["publications"][0]["publisher_evidence"].update(change))

    def test_missing_paper_doi_duplicate_and_signal_crossweek(self):
        self.reject(lambda x:x["publications"][0].update(doi="10.9999/unlisted"))
        self.reject(lambda x:x["signals"][0].update(dois=["10.9999/old"]))
        self.reject(lambda x:x["publications"].append(copy.deepcopy(x["publications"][0])))
        self.reject(lambda x:x.update(schema_version=2))
        self.reject(lambda x:x.update(id="002"))

    def test_zero_paper_issue_allowed(self):
        item=copy.deepcopy(self.base)
        item["publications"]=[]
        item["signals"]=[]
        item["coverage"]["discovered_candidates"]=0
        item["coverage"]["screened_candidates"]=0
        self.assertEqual(validate_issue(item,self.papers),"v3")

    def event(self):
        return {
            "event_id": "sample-event-001", "original_doi": "10.1234/old",
            "original_first_online": "2025-06-04", "event_type": "independent_replication",
            "event_date": "2026-11-05",
            "primary_source_url": "https://doi.org/10.5555/new-evidence",
            "primary_source_kind": "peer_reviewed_original_study",
            "primary_source_published_date": "2026-11-05",
            "primary_source_verified": True,
            "source_verified_at": "2026-11-06T09:00:00+08:00",
            "substantive_impact": "Independent new evidence changes confidence in previous findings.",
            "independent_evidence_summary": "A new original study independently replicated the findings.",
            "editor_approved": True,
            "approved_at": "2026-11-06T11:00:00+08:00",
            "approval_record_id": "approved-by-human-001",
        }

    def test_approved_development_and_unapproved_rejections(self):
        item=copy.deepcopy(self.base)
        item["significant_developments"]=[self.event()]
        self.assertEqual(validate_issue(item,self.papers),"v3")
        for change in (
            {"editor_approved":False}, {"primary_source_verified":False},
            {"event_type":"social_media_buzz"}, {"event_date":"2026-10-30"},
            {"primary_source_published_date":"2026-10-30"},
            {"primary_source_url":"https://github.com/public/repo"},
            {"original_first_online":"2026-11-05"},
            {"approved_at":"2026-11-05T01:00:00+08:00"},
            {"substantive_impact":"Popular"},
            {"approval_record_id":""},
        ):
            with self.subTest(change=change):
                self.reject(lambda x: x["significant_developments"].append({**self.event(),**change}))

    def test_coverage_denominator_and_shortfall_rejection(self):
        self.reject(lambda x:x["coverage"].update(checked=2))
        self.reject(lambda x:x["coverage"].update(screened_candidates=2))
        self.reject(lambda x:x["coverage"].update(notes=""))
        self.reject(lambda x:x["coverage"].update(target_journals=True))
        self.reject(lambda x:x["coverage"].update(discovered_candidates=0))


def run_validation_tests():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(WeeklyIssueGateTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError("V3 weekly publication contract tests failed")


if __name__ == "__main__":
    run_validation_tests()
