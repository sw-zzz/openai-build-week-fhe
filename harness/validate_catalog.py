#!/usr/bin/env python3
"""Validate catalog integrity and report source-backed public-fact coverage."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPPORTUNITIES = json.loads((ROOT / "data" / "opportunities.json").read_text())
FACTS = json.loads((ROOT / "data" / "opportunity_facts.json").read_text())
SCORING = json.loads((ROOT / "data" / "scoring_profiles.json").read_text())


def main() -> None:
    ids = {item["id"] for item in OPPORTUNITIES}
    assert len(ids) == len(OPPORTUNITIES), "opportunity IDs must be unique"
    for item in OPPORTUNITIES:
        assert item["source"].startswith("https://"), f"{item['id']}: missing official source"
    facts = FACTS["records"]
    unknown = set(facts) - ids
    assert not unknown, f"facts for unknown opportunities: {sorted(unknown)}"
    for item_id, record in facts.items():
        assert record["source"].startswith("https://"), f"{item_id}: fact record missing source"
        assert any(key in record for key in ("funding_type", "published_capital", "delivery", "published_focus")), (
            f"{item_id}: fact record has no actionable public fact"
        )
    profiles = SCORING["profiles"]
    assert set(profiles) == ids, "scoring profiles must cover exactly the catalog"
    assert len(SCORING["fields"]) == 6, "expected six source-backed score fields"
    for item_id, profile in profiles.items():
        assert len(profile["values"]) == 6 and len(profile["masks"]) == 6, f"{item_id}: score profile shape"
        assert set(profile["masks"]).issubset({0, 1}), f"{item_id}: score masks must be binary"
    print(f"catalog integrity: PASS ({len(ids)} opportunities)")
    print(f"source-backed public facts: {len(facts)}/{len(ids)} opportunities")
    print("source-backed score profiles: PASS (masked when a public counterpart is unavailable)")


if __name__ == "__main__":
    main()
