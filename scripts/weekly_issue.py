"""V3 public weekly Issue contract. No private pipeline imports or external I/O.

An asserted verified publisher source and human approval are prerequisites;
these fields are not independent authentication of the actual source or reviewer.
Actual evidence/approval audit is required before editorial release.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Asia/Shanghai")
DOI_RE = re.compile(r"10\.\d{4,9}/\S+", re.I)
PUBLIC_SOURCE_TYPES = frozenset({"peer_reviewed_original_study", "regulator_primary_record",
                                 "official_guideline", "original_deployment_report"})
EVENT_TYPES = frozenset({"independent_replication", "independent_refutation",
                         "prospective_clinical_outcome", "regulatory_decision",
                         "formal_guideline_change", "substantive_real_world_deployment_result"})
TOP_KEYS = frozenset({"schema_version", "id", "date", "title", "subtitle", "lead",
                      "week_start", "week_end", "publications", "signals", "watchlist",
                      "significant_developments", "coverage", "scope"})
PUB_KEYS = frozenset({"doi", "first_online_date", "publisher_evidence", "contribution",
                      "main_finding", "evidence_boundary"})
EVIDENCE_KEYS = frozenset({"published_at", "granularity", "event_type", "authority",
                          "source_url", "retrieved_at", "verification_status", "conflicting"})
EVENT_KEYS = frozenset({"event_id", "original_doi", "original_first_online",
                       "event_type", "event_date", "primary_source_url",
                       "primary_source_kind", "primary_source_published_date",
                       "primary_source_verified", "source_verified_at",
                       "substantive_impact", "independent_evidence_summary",
                       "editor_approved", "approved_at", "approval_record_id"})
COVERAGE_KEYS = frozenset({"target_journals", "checked", "partial", "failed",
                           "unverified", "discovered_candidates", "screened_candidates",
                           "notes"})


def day(value):
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected exact YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Noncanonical calendar day")
    return parsed


def instant(value):
    if type(value) is not str:
        raise ValueError("Expected offset-aware timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp without timezone")
    return parsed


def source(value):
    if type(value) is not str or value != value.strip():
        return False
    try:
        u = urlsplit(value)
        return (u.scheme == "https" and bool(u.hostname) and not u.username
                and not u.password and u.hostname.lower() not in {"localhost","example.com"}
                and not u.hostname.lower().endswith((".local", ".invalid"))
                and "github" not in u.hostname.lower() and "drive.google.com" != u.hostname.lower())
    except ValueError:
        return False


def nonempty(value):
    return type(value) is str and bool(value.strip())


def _valid_pub(entry, start, end, bydoi):
    if type(entry) is not dict or set(entry) != PUB_KEYS:
        raise ValueError("Weekly publication must have exact v3 fields")
    doi = entry["doi"]
    if type(doi) is not str or not DOI_RE.fullmatch(doi) or doi not in bydoi:
        raise ValueError("Weekly publication DOI absent from public paper catalogue")
    when = day(entry["first_online_date"])
    if not start <= when <= end:
        raise ValueError("Out-of-week publication cannot appear in weekly publications")
    ev = entry["publisher_evidence"]
    if type(ev) is not dict or set(ev) != EVIDENCE_KEYS:
        raise ValueError("Missing exact publisher publication evidence fields")
    if (ev["verification_status"] != "verified" or ev["conflicting"] is not False
        or ev["authority"] != "publisher" or ev["event_type"] != "journal_first_online"
        or ev["granularity"] not in ("day", "timestamp") or not source(ev["source_url"])):
        raise ValueError("Only verified conflict-free first journal publication is eligible")
    if ev["granularity"] == "day":
        effective = day(ev["published_at"])
    else:
        effective = instant(ev["published_at"]).astimezone(TZ).date()
    if effective != when:
        raise ValueError("Publisher first-online date does not match publication date")
    verified_at = instant(ev["retrieved_at"])
    if verified_at.astimezone(TZ).date() < when:
        raise ValueError("Evidence retrieved before journal publication")
    for key in ("contribution","main_finding","evidence_boundary"):
        if not nonempty(entry[key]):
            raise ValueError("Missing research interpretation field " + key)


def _valid_event(entry, start, end, publication_dois):
    if type(entry) is not dict or set(entry) != EVENT_KEYS:
        raise ValueError("Significant development requires exact v3 event fields")
    if type(entry["event_id"]) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{2,127}", entry["event_id"]):
        raise ValueError("Invalid event identifier")
    doi = entry["original_doi"]
    if type(doi) is not str or not DOI_RE.fullmatch(doi) or doi in publication_dois:
        raise ValueError("Old-paper development cannot be an ordinary new publication")
    original, observed, released = (day(entry["original_first_online"]), day(entry["event_date"]),
                                    day(entry["primary_source_published_date"]))
    if not original < start or not start <= observed <= end or released != observed:
        raise ValueError("Material update must report in-week event and in-week primary source")
    if entry["event_type"] not in EVENT_TYPES or entry["primary_source_kind"] not in PUBLIC_SOURCE_TYPES:
        raise ValueError("Invalid material-event category or primary source")
    if not source(entry["primary_source_url"]) or entry["primary_source_verified"] is not True:
        raise ValueError("Material-event primary source is not verified")
    if not nonempty(entry["substantive_impact"]) or len(entry["substantive_impact"].strip()) < 30:
        raise ValueError("Material-event impact requires substantive rationale")
    if not nonempty(entry["independent_evidence_summary"]) or len(entry["independent_evidence_summary"].strip()) < 30:
        raise ValueError("Material-event independent evidence explanation missing")
    if entry["editor_approved"] is not True or not nonempty(entry["approval_record_id"]):
        raise ValueError("Material-event human approval required")
    verified, approved = instant(entry["source_verified_at"]), instant(entry["approved_at"])
    if verified.astimezone(TZ).date() < released or approved.astimezone(TZ).date() < observed or approved < verified:
        raise ValueError("Material-event source and approval chronology invalid")


def validate_issue(issue, bydoi, filename=None):
    """Validate revised Issue 002 and future v3 issues; preserve Issue 001."""
    if type(issue) is not dict:
        raise ValueError("Issue must be an object")
    ident = issue.get("id")
    if type(ident) is not str or not re.fullmatch(r"\d{3}", ident):
        raise ValueError("Issue ID must be 3 digits")
    if filename is not None and filename != ident + ".json":
        raise ValueError("Issue filename and ID mismatch")
    if ident == "001":
        if "schema_version" in issue:
            raise ValueError("Issue 001 must retain its legacy format")
        return "legacy"
    if issue.get("schema_version") != 3 or set(issue) != TOP_KEYS:
        raise ValueError("New weekly issues require exact schema_version 3 fields")
    publication = day(issue["date"])
    start, end = day(issue["week_start"]), day(issue["week_end"])
    if start.weekday() != 0 or end != start + timedelta(days=6):
        raise ValueError("Weekly issue must cover Monday to Sunday")
    if publication <= end:
        raise ValueError("Issue cannot publish before editorial week ends")
    for key in ("title", "subtitle", "lead", "scope"):
        if not nonempty(issue[key]):
            raise ValueError("Incomplete issue descriptive field")
    if type(issue["watchlist"]) is not list or any(not nonempty(x) for x in issue["watchlist"]):
        raise ValueError("Invalid weekly watchlist")
    pubs = issue["publications"]
    if type(pubs) is not list:
        raise ValueError("Weekly publications must be a list")
    seen = set()
    for entry in pubs:
        _valid_pub(entry, start, end, bydoi)
        if entry["doi"] in seen:
            raise ValueError("Duplicate publication DOI in weekly issue")
        seen.add(entry["doi"])
    signals = issue["signals"]
    if type(signals) is not list:
        raise ValueError("Weekly signals must be a list")
    for sig in signals:
        if type(sig) is not dict or set(sig) != {"eyebrow", "title", "body", "takeaway", "dois"}:
            raise ValueError("Invalid weekly signal")
        if any(not nonempty(sig[k]) for k in ("eyebrow", "title", "body", "takeaway")):
            raise ValueError("Incomplete weekly signal")
        if type(sig["dois"]) is not list or not sig["dois"] or any(d not in seen for d in sig["dois"]):
            raise ValueError("Weekly trend signal can cite only this week's publications")
    events = issue["significant_developments"]
    if type(events) is not list:
        raise ValueError("Significant developments must be a list")
    event_ids = set()
    for event in events:
        _valid_event(event, start, end, seen)
        if event["event_id"] in event_ids:
            raise ValueError("Duplicate significant-development ID")
        event_ids.add(event["event_id"])
    coverage = issue["coverage"]
    if type(coverage) is not dict or set(coverage) != COVERAGE_KEYS:
        raise ValueError("Weekly issue requires exact coverage fields")
    nums = [coverage[k] for k in ("target_journals", "checked", "partial", "failed",
                                  "unverified", "discovered_candidates", "screened_candidates")]
    if any(type(n) is not int or n < 0 for n in nums):
        raise ValueError("Coverage counts must be nonnegative integers")
    if sum(nums[1:5]) != nums[0] or nums[6] > nums[5]:
        raise ValueError("Coverage counts inconsistent")
    if type(coverage["notes"]) is not str:
        raise ValueError("Coverage limitations must be text")
    if nums[1] < nums[0] and not coverage["notes"].strip():
        raise ValueError("Coverage shortfalls must be disclosed")
    if len(pubs) > nums[5]:
        raise ValueError("Publication selection exceeds discovered candidates")
    return "v3"


def validate_issues(issues, papers, names=None):
    bydoi = {p["doi"]: p for p in papers}
    if len(bydoi) != len(papers):
        raise ValueError("Duplicate DOI in public catalogue")
    out = []
    for i, issue in enumerate(issues):
        out.append(validate_issue(issue, bydoi, names[i] if names is not None else None))
    return out
