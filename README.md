# StealthMatch

StealthMatch is a privacy-preserving startup-support discovery prototype. It helps founders research investors, accelerators, grants, and ecosystem programs without submitting confidential operating constraints or conflict concerns to a matching service in plaintext.

Public discovery filters—such as vertical, company stage, and opportunity type—narrow the catalog. The encrypted mandate then refines the shortlist using details that can genuinely be sensitive before an NDA: fundraising constraints, operating runway, timing, readiness, ownership/control ranges, and names of companies, investors, or strategic buyers to avoid.

## How it works

1. The browser collects public filters and a private mandate.
2. A local bridge encodes and encrypts the mandate with CKKS FHE.
3. The scoring service evaluates the ciphertext across the public opportunity catalog, using one opportunity per SIMD slot. It has no secret key.
4. The client decrypts the returned total and component scores, ranks results locally, and presents concise explanations.

The encrypted feature vector has 62 values:

- six numeric mandate fields: availability window, raise target, maximum dilution, capital raised, revenue, and technology readiness;
- 54 private conflict flags resolved against a public registry; and
- two eligibility review flags for institutional ownership and voting control.

The server returns only encrypted totals and four encrypted components: timing, capital/readiness, conflict penalty, and eligibility penalty. Raw vectors, CKKS precision errors, and distance values remain diagnostics rather than user-facing product output.

## Privacy boundary

The founder holds the FHE secret key. The scoring side receives ciphertexts and public/evaluation keys only; it does not receive the founder's plaintext mandate, conflict names, or decrypted component values.

This MVP does not conceal metadata such as request timing or count, nor does it guarantee investment, admission, or complete conflict coverage. The opportunity catalog is intentionally public in the first version. See the [product specification](docs/PRODUCT_SPEC.md) and [private-mandate schema](docs/PRIVATE_MANDATE_SCHEMA.md) for the full boundary.

## Run locally

Clone with submodules, then run the bootstrap script. It initializes the pinned Niobium client SDK, builds its pinned OpenFHE dependency, and runs the complete local test flow. You need a C++17 compiler, CMake 3.16 or later, and Python 3.

```bash
git clone --recurse-submodules https://github.com/sw-zzz/openai-build-week-fhe.git
cd openai-build-week-fhe
./scripts/bootstrap.sh
```

The bundled SDK is at `third_party/niobium-client`. To use a separate compatible checkout, set `NIOBIUM_CLIENT_ROOT`; to use a different Python executable, set `PYTHON`:

```bash
NIOBIUM_CLIENT_ROOT=/path/to/niobium-client PYTHON=python3 make test
```

### Verify encrypted scoring

```bash
make test
```

Runs the encrypted scoring example and confirms its decrypted results match the plaintext reference.

It prepares the demo catalog, generates keys, encrypts a private mandate, performs blind scoring, decrypts the total and component scores, and checks the ranking and numeric error against the plaintext calculation.

### See the value of private inputs

```bash
make compare
```

Runs three paired-founder scenarios: each pair has the same public filters but different private mandates. It shows how confidential conflicts or operating constraints change the locally ranked opportunities, then confirms that the encrypted and plaintext rankings agree.

To use the UI:

```bash
make prepare
python3 app/server.py
```

Open the local URL printed by the server. The browser communicates only with the `127.0.0.1` bridge in this prototype.

## Data and evaluation

The initial catalog is curated from public provider pages. Its sources and limitations are documented in [data/SOURCES.md](data/SOURCES.md). When a public source does not support a numeric scoring input, the corresponding public mask is zeroed rather than guessed.

## Built with Codex and GPT-5.6

This project was built during OpenAI Build Week with Codex running GPT-5.6. The split of work below is deliberate: product judgment and final verification stayed human; design reasoning and implementation speed came from the collaboration.

### Human-led decisions

The founder problem, the privacy boundary, and the evaluation standard were set before any code: public discovery facts (vertical, stage, opportunity type) stay public; concrete operating constraints and conflict names remain a founder-local, encrypted mandate; the secret key and raw values never leave the device; and the output had to be an actionable research shortlist with reasons and cautions — not a cryptography dashboard. "Working" was defined up front as paired scenarios in which identical public filters produce different research orders from private inputs alone.

### Key decisions GPT-5.6 informed

GPT-5.6 was used to reason through design choices before implementation: how to lay out the 62-value encrypted feature vector and pack one opportunity per CKKS SIMD slot; how to decompose scoring into an encrypted total plus four encrypted components (timing, capital/readiness, conflict penalty, eligibility penalty) so explanations stay useful without leaking diagnostics; where the privacy boundary should sit for the fuzzy conflict lookup; and how to construct the paired-founder evaluation cases that `make compare` now runs.

### Where Codex accelerated the build

- **FHE pipeline** — the Niobium DSL programs (`fhe/*.niob`) and the supported DSL → generated CMake → client/server/decrypt workflow, replacing an earlier hand-rolled path.
- **Local bridge and UI** — the founder-side bridge (`app/server.py`) that encodes, encrypts, and decrypts locally, and the founder-facing app (`app/`).
- **Portability** — pinning the Niobium client as a submodule, removing machine-specific paths and fixed ARM compiler settings, and `scripts/bootstrap.sh` for a fresh-clone setup.
- **Verification harness and docs** — the plaintext reference and comparison harness (`harness/verify_scores.py`, `harness/compare_examples.py`, `harness/validate_catalog.py`) and iteration on tests and documentation.

### Independently verified

The final claims were checked without relying on the assistant: encrypted-versus-plaintext ranking agreement within CKKS's expected approximation (`make test`), three fixed-public paired scenarios (`make compare`), and a fresh-clone bootstrap run on a clean machine. The Codex `/feedback` session ID covering core functionality is included in the Devpost submission.

### Developer options

```bash
make validate-data  # validate catalog records and source-backed scoring inputs
make evaluate       # run data validation and the paired-founder comparison
make compare-build  # rebuild generated FHE binaries, then run the comparison
```

The score profiles are a transparent demonstration rubric, not provider endorsements or eligibility decisions. [The match-quality protocol](docs/MATCH_QUALITY_PROTOCOL.md) and [comparison examples](docs/PUBLIC_VS_PRIVATE_MATCHING_EXAMPLES.md) explain the claims the prototype can support.
