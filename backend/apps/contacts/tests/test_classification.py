"""Automatic contact classification."""

import pytest

from apps.contacts.classification import classify_email
from apps.contacts.models import ContactClassification as C


class TestClassification:
    @pytest.mark.parametrize(
        ("email", "expected"),
        [
            # Recruitment
            ("recruitment@acme.example", C.RECRUITMENT),
            ("recruiting@acme.example", C.RECRUITMENT),
            ("recruiter@acme.example", C.RECRUITMENT),
            # Talent
            ("talent@acme.example", C.TALENT),
            ("talent.acquisition@acme.example", C.TALENT),
            # Careers
            ("careers@acme.example", C.CAREERS),
            ("career@acme.example", C.CAREERS),
            ("join-us@acme.example", C.CAREERS),
            # HR
            ("hr@acme.example", C.HR),
            ("human.resources@acme.example", C.HR),
            ("humanresources@acme.example", C.HR),
            ("people@acme.example", C.HR),
            ("peopleops@acme.example", C.HR),
            # Jobs
            ("jobs@acme.example", C.JOBS),
            ("vacancies@acme.example", C.JOBS),
            ("apply@acme.example", C.JOBS),
            ("hiring@acme.example", C.JOBS),
            # Support
            ("support@acme.example", C.SUPPORT),
            ("helpdesk@acme.example", C.SUPPORT),
            ("customerservice@acme.example", C.SUPPORT),
            # Sales
            ("sales@acme.example", C.SALES),
            ("partnerships@acme.example", C.SALES),
            # Media
            ("press@acme.example", C.MEDIA),
            ("media@acme.example", C.MEDIA),
            ("marketing@acme.example", C.MEDIA),
            ("comms@acme.example", C.MEDIA),
            # General
            ("info@acme.example", C.GENERAL),
            ("hello@acme.example", C.GENERAL),
            ("contact@acme.example", C.GENERAL),
            ("enquiries@acme.example", C.GENERAL),
            ("office@acme.example", C.GENERAL),
        ],
    )
    def test_classifies_known_patterns(self, email, expected):
        assert classify_email(email) == expected

    @pytest.mark.parametrize(
        "email",
        [
            "chris@acme.example",
            "j.smith@acme.example",
            "accounts@acme.example",
            "legal@acme.example",
            "invoices@acme.example",
        ],
    )
    def test_unrecognised_addresses_are_unknown(self, email):
        assert classify_email(email) == C.UNKNOWN

    def test_separators_do_not_matter(self):
        for variant in ("human-resources", "human_resources", "human.resources"):
            assert classify_email(f"{variant}@acme.example") == C.HR

    def test_suffixes_are_ignored(self):
        assert classify_email("careers+uk@acme.example") == C.CAREERS

    def test_regional_suffixes_still_classify(self):
        assert classify_email("jobs.ireland@acme.example") == C.JOBS
        assert classify_email("hr.dublin@acme.example") == C.HR

    def test_short_keywords_do_not_match_inside_names(self):
        # "hr" must not fire on "chris", "pr" must not fire on "priya".
        assert classify_email("chris@acme.example") == C.UNKNOWN
        assert classify_email("priya@acme.example") == C.UNKNOWN

    def test_more_specific_rule_wins(self):
        # Contains both "recruitment" and "jobs"; recruitment is more specific.
        assert classify_email("recruitment.jobs@acme.example") == C.RECRUITMENT

    @pytest.mark.parametrize("value", ["", "not-an-email", "@acme.example", None])
    def test_invalid_input_is_unknown(self, value):
        assert classify_email(value) == C.UNKNOWN

    def test_domain_does_not_influence_classification(self):
        # Only the local part is meaningful; a jobs board domain must not
        # reclassify a personal address.
        assert classify_email("chris@jobs.example") == C.UNKNOWN
