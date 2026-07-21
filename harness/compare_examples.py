#!/usr/bin/env python3
"""Reproducible public-only versus private-mandate comparison cases.

The public baseline intentionally uses only the discovery fields exposed by
StealthMatch (vertical, stage, and opportunity type). It does not stand in for
every feature of every directory. The point is narrower: the paired founders
have the same public profile, while their confidential mandate changes the
research order without being disclosed to the matching service in plaintext.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import server

OPPORTUNITIES = json.loads((ROOT / "data" / "opportunities.json").read_text())
FIELD_NAMES = tuple(field for field, _ in server.NUMERIC_FIELDS)
DEFAULT_ELIGIBILITY = {
    "team_size_band": "5-19",
    "institutional_ownership_band": "0",
    "institutional_control_band": "0",
}

CASES = (
    {
        "name": "AI investor search: confidential portfolio overlap",
        "filters": {"industry": ["ai"], "stage": "prototype", "support": ["investor"]},
        "left": {"label": "Founder A", "values": (4, 1.2, 12, 1.1, 0.2, 6), "conflicts": ()},
        "right": {"label": "Founder B", "values": (4, 1.2, 12, 1.1, 0.2, 6), "conflicts": ("elevenlabs", "databricks")},
        "expect": {"left": ("eic-accelerator", "a16z", "dcvc"), "right": ("eic-accelerator", "dcvc", "multicoin-capital")},
    },
    {
        "name": "Deep-tech investor search: confidential strategic conflict",
        "filters": {"industry": ["deeptech"], "stage": "prototype", "support": ["investor"]},
        "left": {"label": "Founder A", "values": (12, 5, 25, 0, 0, 1), "conflicts": ()},
        "right": {"label": "Founder B", "values": (12, 5, 25, 0, 0, 1), "conflicts": ("atom-computing", "fervo-energy")},
        "expect": {"left": ("a16z", "dcvc", "multicoin-capital"), "right": ("a16z", "multicoin-capital", "pantera")},
        "must_demote": "dcvc",
    },
    {
        "name": "Deep-tech grant search: confidential operating constraints",
        "filters": {"industry": ["deeptech"], "stage": "prototype", "support": ["grant"]},
        "left": {"label": "Founder A", "values": (2, 0.3, 5, 0.2, 0.1, 3), "conflicts": ()},
        "right": {"label": "Founder B", "values": (14, 4, 20, 4, 3.5, 8), "conflicts": ()},
        "expect": {"left": ("masschallenge-switzerland", "sbir-sttr", "eic-accelerator"), "right": ("eic-accelerator", "masschallenge-switzerland", "sbir-sttr")},
    },
)


def ranked(case: dict, side: str, eligible: list[int]) -> list[str]:
    answer = case[side]
    mandate = dict(DEFAULT_ELIGIBILITY | dict(zip(FIELD_NAMES, answer["values"])))
    mandate["conflicts"] = list(answer["conflicts"])
    fingerprint = server.mandate_from_answers(mandate)
    scores = []
    for index in eligible:
        profile = server.opportunity_profile(OPPORTUNITIES[index])
        score = sum(mask * (left - right) ** 2 for left, right, mask in zip(fingerprint[:6], profile[:6], server.opportunity_masks(OPPORTUNITIES[index])))
        score += 2 * sum(left * right for left, right in zip(fingerprint[6:], profile[6:]))
        scores.append((score, OPPORTUNITIES[index]["id"]))
    return [item_id for _, item_id in sorted(scores, key=lambda pair: (round(pair[0], 6), pair[1]))[:3]]


def encrypted_rank(case: dict, side: str, eligible: list[int]) -> tuple[tuple[str, ...], float]:
    """Run the actual keygen → encrypt → FHE score → decrypt sequence."""
    answer = case[side]
    mandate = dict(DEFAULT_ELIGIBILITY | dict(zip(FIELD_NAMES, answer["values"])))
    mandate["conflicts"] = list(answer["conflicts"])
    fingerprint = server.mandate_from_answers(mandate)
    result = server.encrypted_match(fingerprint, eligible)
    names_to_ids = {item["name"]: item["id"] for item in OPPORTUNITIES}
    return (
        tuple(names_to_ids[match["name"]] for match in result["matches"]),
        result["verification"]["max_error"],
    )


def main() -> None:
    for case in CASES:
        eligible = server.filter_catalog(case["filters"], OPPORTUNITIES)
        public = [OPPORTUNITIES[index]["id"] for index in eligible]
        left = tuple(ranked(case, "left", eligible))
        right = tuple(ranked(case, "right", eligible))
        assert left == case["expect"]["left"], (case["name"], left)
        assert right == case["expect"]["right"], (case["name"], right)
        encrypted_left, left_error = encrypted_rank(case, "left", eligible)
        encrypted_right, right_error = encrypted_rank(case, "right", eligible)
        assert encrypted_left == left, (case["name"], "left encrypted", encrypted_left, left)
        assert encrypted_right == right, (case["name"], "right encrypted", encrypted_right, right)
        assert left_error < 0.01 and right_error < 0.01, (case["name"], left_error, right_error)
        if "must_demote" in case:
            assert case["must_demote"] in left and case["must_demote"] not in right
        print(case["name"])
        print("  same public candidates:", ", ".join(public))
        print("  Founder A:", ", ".join(left))
        print("  Founder B:", ", ".join(right))
        print(f"  encrypted verification: PASS (max errors {left_error:.2e}, {right_error:.2e})")


if __name__ == "__main__":
    main()
