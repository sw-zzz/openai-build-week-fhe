# Match-quality protocol

## What must be true before a score becomes a product claim

The encrypted score can be numerically correct and still be a poor match. We
therefore separate four layers of evidence:

1. **Public discovery facts** — published sector, stage, geography, program
   structure, funding type, and eligibility. Each fact needs a direct official
   source and a check date.
2. **Private founder facts** — exact runway, raise target, timing, pilot value,
   dilution boundary, evidence, and conflict identities. These remain encrypted.
3. **Matching rules** — a documented reason why one public fact should be
   compared to one encrypted founder fact.
4. **Outcome evidence** — paired cases with the same public discovery set,
   reviewer-justified expected ranking changes, and encrypted-versus-plaintext
   agreement.

The current catalog has source URLs for every opportunity. The audited
public-facts layer is [opportunity_facts.json](../data/opportunity_facts.json).
It now covers all catalog entries and captures only bounded facts each source
actually states. The catalog validator reports coverage instead of implying
that every possible scoring dimension is sourced.

## Benchmark rules

The benchmark in [PUBLIC_VS_PRIVATE_MATCHING_EXAMPLES.md](PUBLIC_VS_PRIVATE_MATCHING_EXAMPLES.md)
has three counterfactual pairs. Each pair:

- fixes vertical, stage, and opportunity type;
- changes only concrete private values or private conflict identities;
- requires a reviewer-readable explanation for the changed research order; and
- runs the actual FHE key generation, encryption, server score, and decryption
  path through `make compare`.

## Current honest boundary

The numeric score now uses [`scoring_profiles.json`](../data/scoring_profiles.json):
published program windows, capital amounts, funding structures, capital/revenue
ceilings, and TRL ranges are mapped to explicit public targets. A binary public
mask removes a field where no source-backed counterpart exists; no missing value
is guessed. These are matching rules, not provider promises, decision-time
guarantees, or admission/funding predictions. Conflicts remain separately
source-backed through the versioned registry.
