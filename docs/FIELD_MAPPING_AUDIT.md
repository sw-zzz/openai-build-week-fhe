# Private-field mapping audit

This audit asks two questions for every potential encrypted field:

1. Would a founder reasonably prefer not to disclose its concrete value to a
   matching service?
2. Does the public catalog contain a source-backed counterpart that can change
   the shortlist?

Only fields that pass both tests belong in the FHE score.

## Existing private fields

| Founder field | Public counterpart found? | Recommendation |
| --- | --- | --- |
| Available program window | Published program durations exist for selected catalog records, but not decision-time guarantees. | Implemented with a public mask and described as program availability, never a decision prediction. |
| Exact raise target | Yes for programs with published investment or grant amounts; unknown for many investor firms. | Implemented with a public mask. |
| Maximum dilution | Yes. Public funding type distinguishes non-dilutive, equity, and blended routes. | Implemented as a documented route mapping with a public mask. |
| Capital raised to date | MassChallenge UK and Switzerland publish capital-raised eligibility ceilings. | Implemented with a public mask. |
| Trailing-12-month revenue | MassChallenge UK and Switzerland publish sales ceilings. | Implemented with a public mask. |
| Technology readiness level | EIC Accelerator publishes TRL 6–8 activities. | Implemented with a public mask. |

## Newly justified private fields

| Candidate field | Why it can be private | Public counterpart | Recommendation |
| --- | --- | --- | --- |
| **Exact capital raised to date** | Reveals financing history and negotiating position. | MassChallenge UK lists less than £3M capital raised; MassChallenge Switzerland lists less than CHF 2M. | Implemented. |
| **Exact trailing-12-month revenue** | Reveals commercial traction and pricing. | MassChallenge UK lists less than £3M sales; MassChallenge Switzerland lists less than CHF 2M sales. | Implemented. |
| **Technology readiness level (TRL)** | Can reveal how far an unannounced technical product has progressed. | EIC Accelerator publishes support for TRL 6–8 activities. | Implemented. |
| **Employee count** | Can reveal operating scale. | NSF requires fewer than 500 employees, including affiliates; EIC has SME/small-mid-cap eligibility rules. | Implemented as an encrypted band. Only the 500+ risk flag is compared with NSF’s published constraint. |
| **Ownership / VC-control status** | Sensitive cap-table information. | NSF specifies U.S. ownership and has restrictions around majority ownership by VC, PE, or hedge-fund firms. | Implemented as a coarse ownership band plus control attestation. It yields only a “confirm eligibility” flag, never an eligibility verdict. |

## Public fields that should remain public

- Industry, broad company stage, opportunity type, and generic support need.
- Incorporation geography and willingness to travel, because they are ordinary
  directory filters and often determine hard eligibility.
- Whether a founder wants equity, grants, or ecosystem support, unless the
  concrete financing mix itself is sensitive.

## Source-backed examples

- Techstars publishes a three-month accelerator structure and a $220,000
  investment offer for future accelerator programs; this can inform a bounded
  program-time/capital fact, not a funding prediction.
- NSF’s current eligibility material states fewer than 500 employees and U.S.
  ownership requirements, while its program page states Phase I/II funding.
- MassChallenge UK and Switzerland publish capital-raised and sales thresholds.
- EIC publishes grant/equity support, eligibility geography, and TRL 6–8
  innovation activities.

Direct sources are retained with the relevant catalog records in
`opportunity_facts.json`. These facts are versioned public metadata; founders'
concrete values remain encrypted.

## Implemented score contract

The next version should use only these grounded comparisons:

```text
score = program_window_fit(available_program_window)
      + published_capital_fit(exact_raise_target)
      + funding_structure_fit(max_dilution)
      + eligibility_cap_fit(exact_capital_raised, exact_revenue)
      + readiness_fit(exact_trl)
      + encrypted_conflict_penalty
```

Each source-backed term carries a public binary mask. If a record lacks a
counterpart, its encrypted difference is zeroed before squaring, so it
contributes neither a reward nor a penalty.
