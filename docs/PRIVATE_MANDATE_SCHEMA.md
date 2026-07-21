# StealthMatch private mandate schema

## Product rule

A datum is encrypted only if its **concrete value or identity** would be
uncomfortable to publish and it changes the recommended opportunity. Broad
labels such as “pre-seed”, “needs pilots”, and “privacy-preserving product”
remain ordinary public filters.

## Public filters (not an FHE claim)

- Broad sector and company stage
- Opportunity kind (investor, accelerator, grant, ecosystem program)
- Geography, where the founder elects to disclose it
- Generic support interests

These reduce the public catalog before encrypted scoring. They are not part of
the private mandate and do not need FHE.

## Encrypted founder mandate

### Private numeric values

| Field | Founder value | Why it is private | Matching use |
| --- | --- | --- | --- |
| Available program window | Exact months the founder can commit to a program | Reveals financing and operating urgency | Compare only with a published program-duration fact |
| Raise target | Exact dollar amount | Reveals financing plan | Compare against check-size or funding-fit metadata |
| Dilution ceiling | Maximum acceptable percentage | Reveals negotiating position | Prefer grant / program / capital paths compatible with the constraint |
| Capital raised to date | Exact cumulative financing | Reveals financing history and negotiating position | Compare with published capital-raised eligibility ceilings |
| Trailing 12-month revenue | Exact commercial revenue | Reveals traction and pricing | Compare with published revenue eligibility ceilings |
| Technology readiness (TRL) | Exact readiness level | Reveals technical maturity | Compare with published TRL ranges |

The client normalizes each number locally into a bounded value before
encryption. The scorer never sees the original number.

### Private identities

| Field | Founder value | Why it is private | Matching use |
| --- | --- | --- | --- |
| Conflict set | Named investors, portfolio companies, competitors, or acquirers to avoid | Reveals strategy and active market map | Apply an encrypted overlap penalty against each opportunity's public portfolio / conflict map |
| Target-account set | Named prospective customers or design partners | Reveals pipeline | Reward opportunities with a relevant introduction map, when that data exists |
| Strategic-dependency set | Named cloud, data, channel, or research partners | Reveals roadmap and negotiating position | Reward compatible programs; avoid incompatible strategic relationships |

Identity values come from a versioned local dictionary. The client converts a
selection into a sparse one-hot vector and encrypts it; it does not send the
selected names. The MVP supports conflict-set matching first. Target-account
and dependency matching require a more complete, sourceable opportunity map.

When a typed name is not an exact local alias, the client derives a fixed
character-trigram vector locally, encrypts it, and runs a separate CKKS
similarity lookup against the public entity index. It returns only a possible
canonical candidate for founder confirmation; fuzzy lookup never creates a
conflict automatically.

### Private eligibility ranges

| Field | Founder value | Matching use |
| --- | --- | --- |
| Team size | A coarse employee-count band | Encrypt a risk flag only when the band reaches a published headcount limit. |
| Institutional ownership | A coarse ownership band | Encrypt a risk flag only when a published ownership constraint might apply. |
| Institutional voting control | A coarse voting-control percentage band | Encrypt a risk flag only when a published control restriction might apply. |

The raw range and control answer stay local, and founders provide all three
answers because every shortlist is eligibility-screened. The client removes an
opportunity locally only when a rule is unambiguous and fully represented—for
example, NSF SBIR/STTR when the founder selects 500+ employees. The same public
candidate set is still sent to a hosted scorer; the removal happens after
decryption so it does not reveal a private answer. Ownership/control remains an
encrypted “confirm eligibility” signal because a coarse range cannot determine
the program's legal requirements.

## Score contract

For each opportunity `j`, the blind scorer evaluates a fixed, data-oblivious
arithmetic circuit:

```
total(j) = timing_fit(j) + capital_readiness_fit(j)
           + conflict_penalty(j) + eligibility_penalty(j)
```

`timing_fit` covers the available-program-window input. `capital_readiness_fit`
covers raise target, dilution ceiling, capital raised, revenue, and TRL. Every
numeric comparison has a public binary mask: an opportunity with no published
counterpart contributes exactly zero for that field. `conflict_penalty` is the
dot product between the founder's encrypted sparse conflict vector and the
opportunity's public conflict / portfolio vector, with a fixed penalty. A
nonzero overlap worsens the score without revealing which company created it.

The server returns the total plus these four **encrypted component vectors**.
The founder client decrypts them locally, ranks by the total, and chooses a
deterministic explanation template. It never sends a chosen explanation—or a
component value—back to the scorer. The component split reuses the same
same encrypted score terms as the total. Public masking adds one plaintext
multiply before the squared comparison, making the circuit depth two; it adds
ciphertext output and local decryption work but no data-dependent branching.

The client decrypts scores and produces explanations locally. Public shortlist
reasons are deterministic templates tied to selected public filters and
source-backed catalog facts; they are not AI-generated. The server sees only
ciphertext, public catalog metadata, and normal operational metadata such as
request timing.

## MVP boundary

The first catalog stays public and source-backed. That makes the MVP a proof
that a matching service can rank a founder's actual financial constraints and
conflict set without learning them. It does **not** claim that public
opportunity descriptions are secret.

Two-sided sealed matching is a future protocol: providers would encrypt their
own non-public capacity, thesis, and conflict data. It needs multi-key FHE or
threshold decryption (and likely private-set intersection for exact entities),
which is outside this single-client-key MVP.

## Evaluation requirement

Every counterfactual pair has identical public filters. It differs only in
actual encrypted values or identities, for example:

- Founder A has 4 months runway, a $1.2M bridge target, and a conflict set
  containing specific portfolio companies.
- Founder B has 16 months runway, a $3.5M seed target, and no overlap with
  those companies.

A public-filter baseline returns the same candidate set. The private-mandate
score should produce different, reviewer-justified rankings while encrypted
and plaintext calculations agree.
