# StealthMatch on Niobium hardware (Fog)

StealthMatch's blind-scoring stage runs on Niobium FPGA hardware through Fog, and
on a local functional simulator that stands in for the hardware offline. The two
paths use the **same binaries** and the **same recorded trace**; only the replay
target differs.

## What runs where

The founder client owns the FHE secret key and never sends it anywhere. Of the
pipeline, only the **key-free** scoring compute goes to Fog:

| Stage | Binary | Where it runs |
|---|---|---|
| Key generation | `key_generation` | client (holds the secret key) |
| Encrypt the mandate | `encrypt_fingerprint` | client |
| **Blind scoring** | `score_opportunities` | **CPU, local sim, or Fog FPGA** |
| Decrypt total + components | `decrypt_*` | client |

The scoring stage receives ciphertext and the public catalog only. This is exactly
what the FHETCH record-and-replay model captures: keygen, encryption, and decryption
stay on the client; only the encrypted compute is recorded and replayed on the device.

The entity-resolution stage (`fuzzy_lookup`) is annotated the same way and follows
the same flow (`encrypt_entity_query` -> `fuzzy_lookup` -> `decrypt_fuzzy_scores`).

## How it works: `@hardware` record and replay

`fhe/server.niob` annotates the scoring stage:

```
@server @stage("score_opportunities")
@hardware(cache_key: ["workload_size"])
```

`nbc` then generates a stage binary that, on its **first** run, executes the real
FHE math and writes a FHETCH trace (a `*_workload_size_<n>/` directory holding the
`.fhetch` trace plus tagged inputs and keys). On a **subsequent** run it finds the
cached trace and replays it instead of recomputing:

- **Local simulator** (`fhetch_sim`): replays the trace with deterministic OpenFHE
  math, offline. This is what `make sim` uses.
- **Fog** (`fog submit ... --target=FOG`): replays the trace on the FPGA and returns
  the encrypted result, which `decrypt_*` reads directly.

The cache is keyed by **workload size, not by input values**. The circuit shape is
fixed per instance size, so one recording per size is reused for any founder input
at replay time. Before recording a different size (or forcing a fresh record), clear
the trace: `make clean-trace`.

## Prerequisites

1. A built [niobium-client](https://github.com/NiobiumInc/niobium-client) checkout
   (its own `make release`). Point `NIOBIUM_CLIENT_ROOT` at it. This provides `nbc`,
   the instrumented OpenFHE, the FHETCH runtime, and the `fhetch_sim` binary that
   `make sim` puts on `PATH` automatically.
2. For Fog only: the `fog` CLI on `PATH` with credentials configured (`fog login`),
   installed from niobium-client (its `make install-cli`).

On macOS / Apple Silicon, pass Homebrew's toolchain (`CMAKE=/opt/homebrew/bin/cmake
PYTHON=/opt/homebrew/bin/python3`); the system cmake/python may be x86_64.

## Run on the local simulator (offline)

```bash
make sim NIOBIUM_CLIENT_ROOT=/path/to/niobium-client
```

This prepares the demo catalog, generates keys, encrypts the mandate, records the
scoring trace (real FHE), replays it on `fhetch_sim`, decrypts, and checks the result
against the plaintext reference. A passing run prints `PASS: encrypted scores match
plaintext reference`.

## Run on Niobium hardware (Fog)

```bash
make fog NIOBIUM_CLIENT_ROOT=/path/to/niobium-client
```

Identical to `make sim`, except the recorded trace is submitted to the device:
`fog submit ./nb_out/build/score_opportunities 0 --target=FOG`. The first local run
records the trace; `fog submit` replays it on the FPGA. It decrypts to the same result
as the simulator and the plaintext reference.

## Manual pipeline

`make sim` / `make fog` wrap this sequence (run from `fhe/`, with the SDK's
`build/vendor/niobium-fhetch` on `PATH` so the replay can find `fhetch_sim`):

```bash
./nb_out/build/key_generation 0
./nb_out/build/encrypt_fingerprint 0
./nb_out/build/score_opportunities 0                 # record (real FHE)
./nb_out/build/score_opportunities 0                 # replay on the local sim
#   or: fog submit ./nb_out/build/score_opportunities 0 --target=FOG   # replay on the FPGA
./nb_out/build/decrypt_scores 0
./nb_out/build/decrypt_timing 0
./nb_out/build/decrypt_capital_readiness 0
./nb_out/build/decrypt_conflict_penalty 0
./nb_out/build/decrypt_eligibility_penalty 0
```

## Parameters and memory

Full profile: CKKS, `HEStd_128_classic`, ring dimension N=65536, multiplicative
depth 2. The scoring trace is about 4.5k instructions over 6 moduli.

Observed on a laptop at N=65536 (full profile): record peak resident set about
0.8 GB; local-sim replay peak working set about 0.3 GB. Keys total about 15 MB
(`keygen.cpp` generates only the relinearization key; the circuit uses no rotations
or sums, so there are no rotation keys). The dominant upload cost is the 62 encrypted
feature ciphertexts (about 190 MB); the submitted trace payload is about 310 MB.
`fhetch_sim` holds the whole trace in memory, so very large or deep traces can exceed
a small-RAM host; a shallow depth-2 circuit like this one stays well within budget.

## Status

- **Local simulator: validated.** Record then replay at N=65536 executes with 0
  errors and decrypts to the plaintext reference (both scoring and entity lookup).
- **Fog FPGA: validated.** `make fog` records the trace, `fog submit` replays it on
  the device (`--target=FOG`), and the decrypted result matches the plaintext
  reference within CKKS approximation error (about 310 MB submitted per run).

## Keep out of git

FHETCH traces and Fog run artifacts (the `*_workload_*/` dirs), Fog run logs, internal
service URLs, job IDs, and absolute local paths must never be committed. The trace and
`io/` artifacts are gitignored and are recreated by `make sim` / `make fog`.
