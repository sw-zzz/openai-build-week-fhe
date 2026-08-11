#!/usr/bin/env python3
"""Create deterministic plaintext inputs and the ground-truth score report.

This is deliberately outside the encrypted circuit: it turns the guided brief
into a fixed numeric vector, prepares the server catalog, and calculates the
plaintext result used to verify the decrypted FHE output.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {0: ("full", 32768)}
REGISTRY = json.loads((ROOT / "data" / "conflict_registry.json").read_text())
CONFLICT_ENTITIES = tuple(entity["id"] for entity in REGISTRY["entities"])
CONFLICT_RELATIONSHIPS = REGISTRY["relationships"]
SCORING_PROFILES = json.loads((ROOT / "data" / "scoring_profiles.json").read_text())["profiles"]
ELIGIBILITY_RISK_FLAGS = ("team_size_500_or_more", "possible_institutional_control")
ELIGIBILITY_RISK_RULES = {"sbir-sttr": set(ELIGIBILITY_RISK_FLAGS)}

# Private values: 4 months runway, $1.2M target, 4-month deadline, $100K
# pilot target, 12% dilution ceiling, and two evidence points. Those are
# followed by private conflict entities and two eligibility-risk flags. All
# values are normalized locally.
FOUNDER = [4/18, 1.2/5, 12/25, 1.1/5, 0.2/5, 6/9] + [
    1.0 if entity == "fhenix" else 0.0 for entity in CONFLICT_ENTITIES
] + [0.0, 0.0]


def profile_for(item: dict) -> list[float]:
    relationships = set(CONFLICT_RELATIONSHIPS.get(item["id"], []))
    eligibility_rules = ELIGIBILITY_RISK_RULES.get(item["id"], set())
    numeric = [
        mask * value / maximum
        for value, mask, maximum in zip(SCORING_PROFILES[item["id"]]["values"], SCORING_PROFILES[item["id"]]["masks"], (18, 5, 25, 5, 5, 9))
    ]
    return (numeric
            + [1.0 if entity in relationships else 0.0 for entity in CONFLICT_ENTITIES]
            + [1.0 if flag in eligibility_rules else 0.0 for flag in ELIGIBILITY_RISK_FLAGS])


def write_matrix(path: Path, rows: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        for row in rows:
            file.write(struct.pack(f"<{len(row)}d", *row))


def main(profile: int = 0) -> None:
    name, slots = PROFILES[profile]
    opportunities = json.loads((ROOT / "data" / "opportunities.json").read_text())
    vectors = [profile_for(item) for item in opportunities]
    masks = [SCORING_PROFILES[item["id"]]["masks"] for item in opportunities]
    padded = vectors + [[0.0] * len(FOUNDER)] * (slots - len(vectors))
    fingerprint = [FOUNDER] * slots
    output = ROOT / "fhe" / "io" / name
    write_matrix(output / "fingerprint.bin", fingerprint)
    write_matrix(output / "opportunities.bin", padded)
    write_matrix(output / "score_masks.bin", masks + [[0.0] * 6] * (slots - len(masks)))

    scored = []
    component_rows = []
    for item in opportunities:
        profile = profile_for(item)
        mask = SCORING_PROFILES[item["id"]]["masks"]
        timing = sum(mask[feature] * (FOUNDER[feature] - profile[feature]) ** 2 for feature in (0,))
        capital_readiness = sum(mask[feature] * (FOUNDER[feature] - profile[feature]) ** 2 for feature in (1, 2, 3, 4, 5))
        conflict_penalty = 2 * sum(left * right for left, right in zip(FOUNDER[6:-2], profile[6:-2]))
        eligibility_penalty = 2 * sum(left * right for left, right in zip(FOUNDER[-2:], profile[-2:]))
        score = timing + capital_readiness + conflict_penalty + eligibility_penalty
        scored.append({"id": item["id"], "name": item["name"], "score": score})
        component_rows.append({
            "id": item["id"], "timing": timing, "capital_readiness": capital_readiness,
            "conflict_penalty": conflict_penalty, "eligibility_penalty": eligibility_penalty,
        })
    scored.sort(key=lambda item: item["score"])
    (output / "expected.json").write_text(json.dumps(scored, indent=2) + "\n")
    (output / "expected_components.json").write_text(json.dumps(component_rows, indent=2) + "\n")
    print(f"prepared {len(opportunities)} opportunities in {output}")
    print("plaintext top 3:", ", ".join(item["name"] for item in scored[:3]))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=int, choices=PROFILES, nargs="?", default=0)
    main(parser.parse_args().profile)
