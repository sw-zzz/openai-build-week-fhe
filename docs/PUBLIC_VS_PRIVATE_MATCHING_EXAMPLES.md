# Public-only vs. private-mandate matching

## Fair comparison

Existing directories already support useful public filters. For example,
[OpenVC](https://docs.openvc.app/en/articles/13228069-filter-the-right-investors)
supports vertical, stage, geography, round size, check size, and investor-type
filters; [F6S](https://www.f6s.com/) lists accelerators, grants, and funding
opportunities. StealthMatch does **not** claim that those platforms cannot
match on detailed information.

The distinction tested here is privacy: a founder can use exact operating
constraints and concrete entities as match inputs without disclosing them in
plaintext to the matching service. Public fields still do the ordinary
discovery work.

The scenarios below are reproducible with `make compare`. It uses the existing
compiled FHE binaries (and builds them once only if absent). After changing a
`.niob` source file, use `make compare-build` to explicitly rebuild first.
“Public candidates”
is the same discovery set for each founder in a pair. `make compare` runs every
founder mandate through the actual key-generation → encryption → server
evaluation → decryption sequence, and asserts that the decrypted top three
matches its plaintext reference. It is a research-order demonstration, not a
prediction of admission, funding, or conflict status.

## Pair 1 — AI investor search

Both founders disclose exactly the same public profile: **AI · Prototype ·
Investor**. Their public discovery candidates are Y Combinator, EIC
Accelerator, a16z, DCVC, and Multicoin.

| Founder | Confidential difference | Public-only result | Private-mandate research order |
| --- | --- | --- | --- |
| A | No private portfolio exclusions | Same five candidates | Y Combinator → Multicoin → a16z |
| B | Privately excludes ElevenLabs and Databricks | Same five candidates | Y Combinator → Multicoin → DCVC |

Why this matters: revealing the named companies can disclose an unannounced
competitive map, design-partner relationship, or strategic concern. The
founder need not explain the reason for the exclusion. The registry’s a16z
relationships are publicly sourced, but the founder’s selected names are
encrypted.

## Pair 2 — deep-tech investor search

Both founders again disclose **AI · Prototype · Investor**, which produces the
same five public candidates.

| Founder | Confidential difference | Public-only result | Private-mandate effect |
| --- | --- | --- | --- |
| A | No private portfolio exclusions | Same five candidates | DCVC → a16z → EIC |
| B | Privately excludes Atom Computing and Fervo Energy | Same five candidates | a16z → EIC → Multicoin; DCVC is demoted |

This pair deliberately uses quantum and climate/energy companies rather than
FHE companies. It demonstrates why the registry must be cross-vertical: the
useful private signal is a founder’s actual strategic-conflict map, not a
generic sector label.

## Pair 3 — deep-tech grant search

Both founders disclose **Deep Tech · Prototype · Grant**. Their public
discovery candidates are MassChallenge Switzerland, America’s Seed Fund
powered by NSF, and EIC Accelerator.

| Founder | Confidential operating mandate | Public-only result | Private-mandate research order |
| --- | --- | --- | --- |
| A | 2 months runway; $0.3M raise; 1-month deadline; $20k pilot; 5% dilution; 1 evidence point | Same three candidates | MassChallenge Switzerland → NSF → EIC |
| B | 14 months runway; $4M raise; 10-month deadline; $400k pilot; 20% dilution; 8 evidence points | Same three candidates | EIC → NSF → MassChallenge Switzerland |

The exact operating figures are commercially sensitive even though “deep tech,
prototype stage, seeking a grant” is not. For this MVP, the numeric profiles
are deliberately hand-authored demonstration rubric values—not claims about
the programs’ actual terms, preferences, or eligibility. The test demonstrates
the *privacy and ranking mechanism*, not an investment recommendation.

## What the evidence supports

- Public discovery yields the same candidate set for paired founders.
- Concrete confidential inputs can change the research order.
- Source-backed portfolio overlap can remove an otherwise plausible outreach
  target without revealing the founder’s selected entity to the service.
- The FHE pipeline is separately tested for encrypted-versus-plaintext
  numerical agreement.

It does not establish that the current starter catalog predicts funding,
admission, or legal conflicts. A production evaluation would need a larger,
time-versioned opportunity dataset and blinded expert/founder judgments.
