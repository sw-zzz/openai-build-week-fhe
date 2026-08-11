#!/usr/bin/env python3
"""Local StealthMatch bridge for encrypted private mandates.

Public filters remain in the browser. This client owns the founder's actual
financial values and conflict selections, converts them to a fixed vector,
encrypts it, and decrypts the scores. The scoring stage receives ciphertext
and a public catalog only.
"""
from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
FHE = ROOT / "fhe"
BIN = FHE / "nb_out" / "build"
# The single Full profile: N=65536, 32768 SIMD slots (one opportunity per slot).
IO = FHE / "io" / "full"
SLOTS = 32768
NUMERIC_FEATURES = 6

# Concrete values are normalized locally into [0, 1]. The scorer never sees
# the original months, dollars, percentages, or selected identities.
NUMERIC_FIELDS = (
    ("program_window_months", 18.0),
    ("raise_millions", 5.0),
    ("dilution_percent", 25.0),
    ("capital_raised_millions", 5.0),
    ("revenue_millions", 5.0),
    ("trl", 9.0),
)
CONFLICT_REGISTRY = json.loads((ROOT / "data" / "conflict_registry.json").read_text())
OPPORTUNITY_FACTS = json.loads((ROOT / "data" / "opportunity_facts.json").read_text())["records"]
SCORING_PROFILES = json.loads((ROOT / "data" / "scoring_profiles.json").read_text())["profiles"]
CONFLICT_ENTITIES = tuple(entity["id"] for entity in CONFLICT_REGISTRY["entities"])
ENTITY_REGISTRY = tuple(
    {"id": entity["id"], "label": entity["label"], "aliases": tuple((entity["label"], *entity["aliases"]))}
    for entity in CONFLICT_REGISTRY["entities"]
)
CONFLICT_RELATIONSHIPS = CONFLICT_REGISTRY["relationships"]
ELIGIBILITY_RISK_FLAGS = (
    "team_size_500_or_more",
    "possible_institutional_control",
)
# The raw bands remain client-side. These narrow flags only screen against
# published opportunity constraints; they are not eligibility decisions.
ELIGIBILITY_RISK_RULES = {
    "sbir-sttr": {"team_size_500_or_more", "possible_institutional_control"},
}
FEATURES = NUMERIC_FEATURES + len(CONFLICT_ENTITIES) + len(ELIGIBILITY_RISK_FLAGS)
ENTITY_FEATURES = 32

# Ordinary, public catalog filters. These are intentionally not part of the
# encrypted mandate; they only narrow the opportunities to be privately ranked.
PUBLIC_CATALOG = {
    "techstars-ai-health": {"industry": {"ai", "digital-health"}, "stage": {"idea", "prototype", "early-revenue"}, "support": {"accelerator"}},
    "techstars-energytech": {"industry": {"climate", "hardware"}, "stage": {"idea", "prototype", "early-revenue"}, "support": {"accelerator"}},
    "cdl-ai": {"industry": {"ai", "deeptech"}, "stage": {"prototype", "early-revenue"}, "support": {"accelerator"}},
    "cdl-computational-health": {"industry": {"ai", "health-it", "digital-health"}, "stage": {"prototype", "early-revenue"}, "support": {"accelerator"}},
    "hax": {"industry": {"hardware", "biotech", "climate", "manufacturing", "robotics"}, "stage": {"idea", "prototype", "early-revenue"}, "support": {"accelerator"}},
    "sbir-sttr": {"industry": {"ai", "biotech", "climate", "hardware", "deeptech"}, "stage": {"idea", "prototype", "early-revenue", "scaling"}, "support": {"grant"}},
    "nvidia-inception": {"industry": {"ai", "cloud", "devtools", "enterprise-infra"}, "stage": {"prototype", "early-revenue", "scaling"}, "support": {"ecosystem"}},
    "techstars-anywhere": {"industry": {"ai", "saas", "marketplaces", "fintech", "food-beverage"}, "stage": {"idea", "prototype", "early-revenue"}, "support": {"accelerator"}},
    "yc": {"industry": {"ai", "analytics", "biotech", "climate", "cloud", "consumer-health", "cybersecurity", "data-services", "deeptech", "devtools", "digital-health", "enterprise-infra", "fintech", "food-beverage", "hardware", "health-it", "manufacturing", "marketplaces", "robotics", "saas", "semiconductors", "web3"}, "stage": {"idea", "prototype", "early-revenue", "scaling"}, "support": {"accelerator", "investor"}},
    "multicoin-capital": {"industry": {"ai", "web3", "deeptech"}, "stage": {"idea", "prototype", "early-revenue"}, "support": {"investor"}},
    "masschallenge-uk": {"industry": {"ai", "cybersecurity", "food-beverage", "biotech", "climate", "robotics", "deeptech"}, "stage": {"idea", "prototype", "early-revenue"}, "support": {"accelerator"}},
    "masschallenge-switzerland": {"industry": {"food-beverage", "biotech", "climate", "manufacturing", "digital-health", "ai", "deeptech"}, "stage": {"idea", "prototype", "early-revenue", "scaling"}, "support": {"accelerator", "grant"}},
    "alchemist-japan": {"industry": {"ai", "analytics", "cloud", "cybersecurity", "data-services", "deeptech", "devtools", "enterprise-infra", "fintech", "health-it", "manufacturing", "saas"}, "stage": {"prototype", "early-revenue", "scaling"}, "support": {"accelerator"}},
    "eic-accelerator": {"industry": {"ai", "biotech", "climate", "cybersecurity", "deeptech", "hardware", "manufacturing", "robotics", "semiconductors"}, "stage": {"prototype", "early-revenue", "scaling", "growth"}, "support": {"grant", "investor"}},
    "aws-activate": {"industry": {"ai", "analytics", "cloud", "cybersecurity", "data-services", "devtools", "digital-health", "enterprise-infra", "fintech", "health-it", "marketplaces", "saas", "web3"}, "stage": {"idea", "prototype", "early-revenue", "scaling", "growth"}, "support": {"ecosystem"}},
    "google-cloud-startups": {"industry": {"ai", "analytics", "cloud", "cybersecurity", "data-services", "devtools", "digital-health", "enterprise-infra", "fintech", "health-it", "marketplaces", "saas", "web3"}, "stage": {"prototype", "early-revenue", "scaling", "growth"}, "support": {"ecosystem"}},
    "microsoft-founders-hub": {"industry": {"ai", "analytics", "cloud", "cybersecurity", "data-services", "devtools", "digital-health", "enterprise-infra", "fintech", "health-it", "marketplaces", "saas"}, "stage": {"idea", "prototype", "early-revenue", "scaling", "growth"}, "support": {"ecosystem"}},
    "a16z": {"industry": {"ai", "analytics", "biotech", "cloud", "consumer-health", "cybersecurity", "data-services", "deeptech", "devtools", "digital-health", "enterprise-infra", "fintech", "health-it", "marketplaces", "saas", "web3"}, "stage": {"idea", "prototype", "early-revenue", "scaling", "growth", "pre-ipo"}, "support": {"investor"}},
    "dcvc": {"industry": {"ai", "biotech", "climate", "cybersecurity", "deeptech", "hardware", "manufacturing", "robotics", "semiconductors"}, "stage": {"prototype", "early-revenue", "scaling", "growth"}, "support": {"investor"}},
    "pantera": {"industry": {"web3", "fintech", "deeptech", "cloud"}, "stage": {"prototype", "early-revenue", "scaling"}, "support": {"investor"}},
}


def write_matrix(path: Path, rows: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        for row in rows:
            file.write(struct.pack(f"<{len(row)}d", *row))


def entity_vector(value: str) -> list[float]:
    text = "".join(character for character in value.lower() if character.isalnum())
    grams = [text[index:index + size] for size in (2, 3) for index in range(max(1, len(text) - size + 1))]
    vector = [0.0] * ENTITY_FEATURES
    # Stable character positions make short prefixes meaningful; hashed n-grams
    # add typo tolerance without exposing the raw text to the scorer.
    for character in text:
        if "a" <= character <= "z":
            vector[ord(character) - ord("a")] += 1.0
    for gram in grams:
        bucket = 26 + sum((index + 1) * ord(character) for index, character in enumerate(gram)) % (ENTITY_FEATURES - 26)
        vector[bucket] += 0.35
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def fuzzy_resolve(value: str) -> dict:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("enter a company name")
    normalized = "".join(character for character in value.lower() if character.isalnum())
    # Exact local aliases are a privacy-preserving fast path. Typos and partial
    # names still use the encrypted similarity stage below.
    exact = [
        entry for entry in ENTITY_REGISTRY
        if normalized in {"".join(character for character in name.lower() if character.isalnum()) for name in entry["aliases"]}
    ]
    if exact:
        return {"candidates": [{"id": entry["id"], "label": entry["label"]} for entry in exact]}
    query = entity_vector(value)
    variants = [
        (entry, name)
        for entry in ENTITY_REGISTRY
        for name in entry["aliases"]
    ]
    index = [entity_vector(name) for _, name in variants]
    index += [[0.0] * ENTITY_FEATURES] * (SLOTS - len(index))
    write_matrix(IO / "entity_query.bin", [query] * SLOTS)
    write_matrix(IO / "entity_index.bin", index)
    for command in ("key_generation", "encrypt_entity_query", "fuzzy_lookup", "decrypt_fuzzy_scores"):
        run(command)
    raw = (IO / "scores.bin").read_bytes()
    scores = struct.unpack(f"<{len(raw) // 8}d", raw)[:len(variants)]
    best_by_entity: dict[str, tuple[dict, float]] = {}
    for (entry, _name), score in zip(variants, scores):
        previous = best_by_entity.get(entry["id"])
        if previous is None or score < previous[1]:
            best_by_entity[entry["id"]] = (entry, score)
    ranked = sorted(best_by_entity.values(), key=lambda item: item[1])
    best_score = ranked[0][1]
    if best_score > 1.35:
        return {"candidates": []}
    candidates = [
        {"id": entry["id"], "label": entry["label"]}
        for entry, score in ranked if score <= min(1.35, best_score + 0.15)
    ]
    return {"candidates": candidates}


def prepare_fingerprint(fingerprint: list[float]) -> None:
    if len(fingerprint) != FEATURES or any(not isinstance(value, (int, float)) for value in fingerprint):
        raise ValueError(f"private mandate must contain exactly {FEATURES} encrypted feature values")
    write_matrix(IO / "fingerprint.bin", [fingerprint] * SLOTS)


def prepare_score_masks(opportunities: list[dict]) -> None:
    masks = [opportunity_masks(item) for item in opportunities]
    write_matrix(IO / "score_masks.bin", masks + [[0.0] * NUMERIC_FEATURES] * (SLOTS - len(masks)))


def opportunity_profile(item: dict) -> list[float]:
    numeric = [
        mask * value / maximum
        for value, mask, (_, maximum) in zip(
            SCORING_PROFILES[item["id"]]["values"],
            SCORING_PROFILES[item["id"]]["masks"],
            NUMERIC_FIELDS,
        )
    ]
    if len(numeric) != NUMERIC_FEATURES:
        raise ValueError(f"{item['id']} must contain at least {NUMERIC_FEATURES} numeric profile values")
    relationships = set(CONFLICT_RELATIONSHIPS.get(item["id"], []))
    eligibility_rules = ELIGIBILITY_RISK_RULES.get(item["id"], set())
    return (
        numeric
        + [1.0 if entity in relationships else 0.0 for entity in CONFLICT_ENTITIES]
        + [1.0 if flag in eligibility_rules else 0.0 for flag in ELIGIBILITY_RISK_FLAGS]
    )


def opportunity_masks(item: dict) -> list[float]:
    masks = SCORING_PROFILES[item["id"]]["masks"]
    if len(masks) != NUMERIC_FEATURES:
        raise ValueError(f"{item['id']} must contain {NUMERIC_FEATURES} score masks")
    return [float(mask) for mask in masks]


def mandate_from_answers(mandate: dict) -> list[float]:
    if not isinstance(mandate, dict):
        raise ValueError("private mandate must be an object")
    fingerprint: list[float] = []
    for field, maximum in NUMERIC_FIELDS:
        try:
            value = float(mandate[field])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{field} must be a number") from error
        if value < 0 or value > maximum:
            raise ValueError(f"{field} must be between 0 and {maximum:g}")
        fingerprint.append(value / maximum)

    selected = set(mandate.get("conflicts", []))
    if not selected.issubset(CONFLICT_ENTITIES):
        raise ValueError("unknown private conflict entity")
    fingerprint.extend(1.0 if entity in selected else 0.0 for entity in CONFLICT_ENTITIES)
    team_size = mandate.get("team_size_band")
    ownership = mandate.get("institutional_ownership_band")
    control = mandate.get("institutional_control_band")
    valid_team_sizes = {"1-4", "5-19", "20-49", "50-249", "250-499", "500-plus"}
    valid_ownership = {"0", "1-24", "25-49", "50-plus"}
    valid_control = {"0", "1-24", "25-49", "50-plus"}
    if team_size not in valid_team_sizes or ownership not in valid_ownership or control not in valid_control:
        raise ValueError("choose a valid private eligibility range")
    fingerprint.extend((
        1.0 if team_size == "500-plus" else 0.0,
        1.0 if ownership == "50-plus" or control == "50-plus" else 0.0,
    ))
    return fingerprint


def hard_eligibility_exclusions(mandate: dict) -> set[str]:
    """Apply only unambiguous, public hard limits on the founder's device."""
    excluded: set[str] = set()
    if mandate.get("team_size_band") == "500-plus":
        # NSF SBIR/STTR's published limit is fewer than 500 employees.
        excluded.add("sbir-sttr")
    return excluded


def filter_catalog(filters: dict, opportunities: list[dict], mandate: dict | None = None) -> list[int]:
    if not isinstance(filters, dict):
        raise ValueError("public filters must be an object")
    required = ("industry", "stage", "support")
    if any(filters.get(field) is None for field in required) or not filters["industry"] or not filters["support"]:
        raise ValueError("choose industry, stage, and support type")
    industries = filters["industry"] if isinstance(filters["industry"], list) else [filters["industry"]]
    supports = filters["support"] if isinstance(filters["support"], list) else [filters["support"]]
    excluded = hard_eligibility_exclusions(mandate or {})
    eligible = [
        index for index, item in enumerate(opportunities)
        if any(industry in PUBLIC_CATALOG[item["id"]]["industry"] for industry in industries)
        and filters["stage"] in PUBLIC_CATALOG[item["id"]]["stage"]
        and any(support in PUBLIC_CATALOG[item["id"]]["support"] for support in supports)
        and item["id"] not in excluded
    ]
    if not eligible:
        raise ValueError("no catalog opportunities match those public filters; try a different support type")
    return eligible


def public_detail(item: dict) -> str | None:
    """Return one short, source-backed public fact—never a generated claim."""
    facts = OPPORTUNITY_FACTS.get(item["id"], {})
    for field in ("funding_type", "delivery", "published_capital", "published_stage_signal"):
        if facts.get(field) and facts[field] not in {
            "Investment firm; public firm information is not an application or an investment offer",
            "Multi-stage technology investment firm; public firm information is not an application or an investment offer",
        }:
            return facts[field].split(";")[0].rstrip(".") + "."
    focus = facts.get("published_focus")
    if not focus:
        return None
    concise_focus = {
        "a16z": "Published focus: technology investing across multiple sectors.",
        "dcvc": "Published focus: deep-tech companies.",
        "multicoin-capital": "Published focus: cryptographic primitives and FHE-related investments.",
    }
    return concise_focus.get(item["id"], focus.split(";")[0].rstrip(".") + ".")


def component_reason(item: dict, components: dict[str, float]) -> str:
    """Explain decrypted component scores locally, without exposing values."""
    masks = opportunity_masks(item)
    numeric = {}
    if masks[0]:
        numeric["timing"] = components["timing"]
    if any(masks[1:NUMERIC_FEATURES]):
        numeric["capital_readiness"] = components["capital_readiness"]
    if not numeric:
        return "Your private conflict and eligibility screens were applied after public discovery filtering."
    strongest = min(numeric, key=numeric.get)
    if strongest == "timing":
        return "Its published program window is more compatible with your private availability."
    return "Its published funding and readiness criteria were a stronger match for your private mandate."


# The @hardware server stages: on their first run they record a FHETCH trace,
# and a subsequent run would replay it (which needs fhetch_sim and the recorded
# inputs). The bridge scores fresh inputs every request, so we clear the
# size-keyed trace cache before these stages to force a fresh recording, i.e.
# real FHE compute on CPU. (Fog runs go through the CLI `make fog`, not here.)
HARDWARE_STAGES = ("score_opportunities", "fuzzy_lookup")


def run(command: str) -> None:
    if command in HARDWARE_STAGES:
        for cache in FHE.glob(f"{command}_workload_*"):
            shutil.rmtree(cache, ignore_errors=True)
    subprocess.run([str(BIN / command), "0"], cwd=FHE, check=True, capture_output=True)


def encrypted_match(fingerprint: list[float], eligible: list[int] | None = None, filters: dict | None = None) -> dict:
    if not (IO / "opportunities.bin").exists():
        raise RuntimeError("run `make prepare` once before starting the local bridge")
    opportunities = json.loads((ROOT / "data" / "opportunities.json").read_text())
    prepare_fingerprint(fingerprint)
    prepare_score_masks(opportunities)
    for command in (
        "key_generation", "encrypt_fingerprint", "score_opportunities", "decrypt_scores",
        "decrypt_timing", "decrypt_capital_readiness", "decrypt_conflict_penalty", "decrypt_eligibility_penalty",
    ):
        run(command)

    def read_component(name: str) -> tuple[float, ...]:
        raw = (IO / f"{name}.bin").read_bytes()
        return struct.unpack(f"<{len(raw) // 8}d", raw)[:len(opportunities)]

    scores = read_component("scores")
    component_scores = {
        "timing": read_component("timing"),
        "capital_readiness": read_component("capital_readiness"),
        "conflict_penalty": read_component("conflict_penalty"),
        "eligibility_penalty": read_component("eligibility_penalty"),
    }
    plaintext = [
        sum(mask * (left - right) ** 2 for left, right, mask in zip(fingerprint[:NUMERIC_FEATURES], opportunity_profile(item)[:NUMERIC_FEATURES], opportunity_masks(item)))
        + 2 * sum(left * right for left, right in zip(fingerprint[NUMERIC_FEATURES:], opportunity_profile(item)[NUMERIC_FEATURES:]))
        for item in opportunities
    ]
    candidate_indices = eligible if eligible is not None else list(range(len(opportunities)))
    # CKKS noise can reorder mathematically tied scores at ~1e-8. Coarsen only
    # for local presentation and use the public ID as a stable tiebreaker.
    ranked = sorted(((index, scores[index]) for index in candidate_indices), key=lambda pair: (round(pair[1], 6), opportunities[pair[0]]["id"]))[:3]
    matches = []
    for index, _score in ranked:
        item = opportunities[index]
        profile = opportunity_profile(item)
        components = {name: values[index] for name, values in component_scores.items()}
        conflict_end = NUMERIC_FEATURES + len(CONFLICT_ENTITIES)
        conflict_overlap = sum(left * right for left, right in zip(fingerprint[NUMERIC_FEATURES:conflict_end], profile[NUMERIC_FEATURES:conflict_end]))
        eligibility_overlap = sum(left * right for left, right in zip(fingerprint[conflict_end:], profile[conflict_end:]))
        notices = []
        if conflict_overlap > 0.5:
            notices.append("A private exclusion may overlap with this opportunity’s public relationship map. Review before applying.")
        if eligibility_overlap > 0.5:
            notices.append("A private eligibility detail needs confirmation before you apply.")
        conflict_status = " ".join(notices) or None
        reason = component_reason(item, components)
        matches.append({
            "name": item["name"], "type": item["type"], "source": item["source"],
            "summary": item["summary"], "watchout": item["watchout"],
            "reason": reason, "public_detail": public_detail(item), "conflict_status": conflict_status,
        })
    return {"matches": matches, "verification": {"max_error": max(abs(score - plain) for score, plain in zip(scores, plaintext))}}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP, **kwargs)

    def do_POST(self):
        if self.path not in {"/api/match", "/api/resolve"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            if self.path == "/api/resolve":
                response = json.dumps(fuzzy_resolve(payload["name"])).encode()
            else:
                opportunities = json.loads((ROOT / "data" / "opportunities.json").read_text())
                fingerprint = mandate_from_answers(payload["mandate"])
                eligible = filter_catalog(payload["filters"], opportunities, payload["mandate"])
                response = json.dumps(encrypted_match(fingerprint, eligible, payload["filters"])).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except Exception as error:
            message = json.dumps({"error": str(error)}).encode()
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)


if __name__ == "__main__":
    print("StealthMatch local client: http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
