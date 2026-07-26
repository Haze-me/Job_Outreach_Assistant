"""Automatic contact classification.

The category is inferred from the local part of the address -- the piece before
the ``@``. That is the only signal a bare email carries, and in practice it is
a good one: organisations publish ``careers@``, ``recruitment@``, ``support@``
and so on precisely so that mail routes itself.

Rules are ordered from most to least specific, and the first match wins. An
address that matches nothing is ``UNKNOWN``, as the specification requires.
"""

from __future__ import annotations

import re

from apps.contacts.models import ContactClassification

# (classification, keywords). Matched against the local part with separators
# normalised away, so "human.resources", "human-resources", "human_resources"
# and "humanresources" all behave identically.
CLASSIFICATION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        ContactClassification.RECRUITMENT,
        ("recruitment", "recruiting", "recruiter", "recruiters", "recruit"),
    ),
    (
        ContactClassification.TALENT,
        ("talentacquisition", "talentteam", "talent"),
    ),
    (
        ContactClassification.CAREERS,
        ("careers", "career", "workwithus", "workforus", "joinus", "jointheteam"),
    ),
    (
        ContactClassification.HR,
        ("humanresources", "hr", "peopleops", "peopleteam", "people", "personnel"),
    ),
    (
        ContactClassification.JOBS,
        ("jobs", "job", "vacancy", "vacancies", "apply", "applications", "application", "hiring"),
    ),
    (
        ContactClassification.SUPPORT,
        ("support", "helpdesk", "servicedesk", "customerservice", "customercare", "help", "care"),
    ),
    (
        ContactClassification.SALES,
        ("sales", "salesteam", "partnerships", "partners", "business", "bizdev", "bd", "orders"),
    ),
    (
        ContactClassification.MEDIA,
        ("media", "press", "pressoffice", "publicrelations", "pr", "marketing",
         "communications", "comms", "newsroom"),
    ),
    (
        ContactClassification.GENERAL,
        ("info", "information", "hello", "hi", "contact", "contactus", "enquiries", "enquiry",
         "inquiries", "inquiry", "admin", "office", "mail", "email", "general", "reception"),
    ),
)

_SEPARATORS = re.compile(r"[._\-+]")


def _normalise_local_part(email: str) -> str:
    local = email.split("@", 1)[0].lower()
    # "careers+uk@" is still a careers address.
    local = local.split("+", 1)[0]
    return _SEPARATORS.sub("", local)


def _tokens(email: str) -> list[str]:
    """Splits the local part on its separators, e.g. 'jobs.uk' -> ['jobs', 'uk']."""
    local = email.split("@", 1)[0].lower().split("+", 1)[0]
    return [token for token in _SEPARATORS.split(local) if token]


def classify_email(email: str) -> str:
    """Returns the ``ContactClassification`` value for an address."""
    if not email or "@" not in email:
        return ContactClassification.UNKNOWN

    collapsed = _normalise_local_part(email)
    tokens = set(_tokens(email))

    for classification, keywords in CLASSIFICATION_RULES:
        for keyword in keywords:
            # An exact token match ("hr" in "hr.ireland") is decisive. A
            # substring match on the collapsed form catches "hrteam", but only
            # for keywords long enough that it cannot fire by accident --
            # otherwise "hr" would match "chris@".
            if keyword in tokens:
                return classification
            if len(keyword) >= 4 and keyword in collapsed:
                return classification

    return ContactClassification.UNKNOWN
