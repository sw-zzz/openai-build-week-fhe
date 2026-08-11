#!/usr/bin/env python3
"""Compare decrypted CKKS scores with the plaintext ground truth."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {0: "full"}


def main(profile: int = 0) -> int:
    root = ROOT / "fhe" / "io" / PROFILES[profile]
    expected = json.loads((root / "expected.json").read_text())
    data = (root / "scores.bin").read_bytes()
    scores = struct.unpack(f"<{len(data) // 8}d", data)
    expected_components = {row["id"]: row for row in json.loads((root / "expected_components.json").read_text())}

    catalog = json.loads((ROOT / "data" / "opportunities.json").read_text())
    actual = sorted(
        ({"id": item["id"], "name": item["name"], "score": scores[index]}
         for index, item in enumerate(catalog)),
        key=lambda item: item["score"],
    )
    expected_ids = [item["id"] for item in expected]
    actual_ids = [item["id"] for item in actual]
    # expected.json is sorted; compare by ID rather than catalog position.
    expected_by_id = {item["id"]: item["score"] for item in expected}
    max_error = max(abs(expected_by_id[item["id"]] - item["score"]) for item in actual)
    component_errors = {}
    for name in ("timing", "capital_readiness", "conflict_penalty", "eligibility_penalty"):
        component_data = (root / f"{name}.bin").read_bytes()
        component_scores = struct.unpack(f"<{len(component_data) // 8}d", component_data)
        component_errors[name] = max(abs(expected_components[item["id"]][name] - component_scores[index]) for index, item in enumerate(catalog))
    print("plaintext top 3:", ", ".join(expected_ids[:3]))
    print("encrypted top 3:", ", ".join(actual_ids[:3]))
    print(f"max CKKS absolute error: {max_error:.6g}")
    print("component errors:", ", ".join(f"{name}={error:.2e}" for name, error in component_errors.items()))
    # Lower-ranked ties may be ordered differently by tiny CKKS noise; the
    # product claim is that the displayed top three and numeric scores agree.
    if set(expected_ids[:3]) != set(actual_ids[:3]) or max_error > 0.01 or max(component_errors.values()) > 0.01:
        print("FAIL: encrypted ranking diverged from plaintext reference", file=sys.stderr)
        return 1
    print("PASS: encrypted scores match plaintext reference")
    return 0


if __name__ == "__main__":
    profile = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    raise SystemExit(main(profile))
