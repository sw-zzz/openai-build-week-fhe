# StealthMatch build.
#
# niobium-client is an external prerequisite: point NIOBIUM_CLIENT_ROOT at your
# built niobium-client checkout. It provides the `nbc` DSL compiler, the
# instrumented OpenFHE, and the FHETCH record/replay runtime that lets the
# @hardware scoring stage run on the local functional simulator or, via
# `fog submit`, on Niobium FPGA hardware. Build the client once beforehand
# (its `make release`).
#
# Override the toolchain when the defaults are wrong for your platform, e.g. on
# macOS/Apple Silicon:
#   make sim NIOBIUM_CLIENT_ROOT=/path/to/niobium-client \
#            CMAKE=/opt/homebrew/bin/cmake PYTHON=/opt/homebrew/bin/python3
PYTHON := $(or $(PYTHON),python3)
CMAKE  := $(or $(CMAKE),cmake)
NIOBIUM_CLIENT_ROOT := $(or $(NIOBIUM_CLIENT_ROOT),$(CURDIR)/third_party/niobium-client)

XCOMP := $(NIOBIUM_CLIENT_ROOT)/dsl_fhe/xcomp
BUILD := fhe/nb_out/build
SBIN  := ./nb_out/build
# fhetch_sim (the local functional simulator the replay pass spawns) ships in
# the built niobium-client tree; put it on PATH for `make sim`.
NB_FHETCH_BIN := $(NIOBIUM_CLIENT_ROOT)/build/vendor/niobium-fhetch

# Instance size selector. There is a single profile, Full (index 0): N=65536,
# HEStd_128_classic, the parameters Niobium hardware requires.
SIZE   ?= 0

# The client-side decrypt stages for the scoring pipeline.
SCORE_DECRYPTS := decrypt_scores decrypt_timing decrypt_capital_readiness \
                  decrypt_conflict_penalty decrypt_eligibility_penalty

.PHONY: prepare check compile build test sim fog clean-trace \
        evaluate compare compare-build validate-data require-sdk

require-sdk:
	@test -f "$(XCOMP)/nbc.py" || { \
	  echo "niobium-client not found at NIOBIUM_CLIENT_ROOT=$(NIOBIUM_CLIENT_ROOT)"; \
	  echo "Set NIOBIUM_CLIENT_ROOT to your niobium-client checkout (see README)."; \
	  exit 1; }
	@test -f "$(NIOBIUM_CLIENT_ROOT)/vendor/lib/openfhe/include/openfhe/pke/openfhe.h" || { \
	  echo "niobium-client at $(NIOBIUM_CLIENT_ROOT) is not built"; \
	  echo "Build it once in that checkout (its 'make release'), then re-run."; \
	  exit 1; }

prepare:
	$(PYTHON) harness/prepare_demo.py $(SIZE)

# nbc is a package (xcomp); run it via -m with dsl_fhe on PYTHONPATH.
NBC := PYTHONPATH=$(NIOBIUM_CLIENT_ROOT)/dsl_fhe $(PYTHON) -m xcomp.nbc

check: require-sdk
	cd fhe && $(NBC) check shared.niob client.niob server.niob

compile: require-sdk
	mkdir -p fhe/nb_out
	cd fhe && $(NBC) compile shared.niob client.niob server.niob --outdir nb_out

build: compile
	@grep -q 'add_executable(key_generation' fhe/nb_out/CMakeLists.txt \
	  || cat scripts/keygen_target.cmake >> fhe/nb_out/CMakeLists.txt
	$(CMAKE) -S fhe/nb_out -B $(BUILD) -DNIOBIUM_CLIENT_ROOT=$(NIOBIUM_CLIENT_ROOT) -DLOCAL_SRC_DIR=$(CURDIR)/fhe
	$(CMAKE) --build $(BUILD) --target key_generation encrypt_fingerprint encrypt_entity_query score_opportunities fuzzy_lookup decrypt_scores decrypt_timing decrypt_capital_readiness decrypt_conflict_penalty decrypt_eligibility_penalty decrypt_fuzzy_scores -j2

# The FHETCH trace cache is keyed by workload size, not by input values, so a
# stale trace would be replayed for new inputs. Clear it before a fresh record.
clean-trace:
	rm -rf fhe/score_opportunities_workload_* fhe/fuzzy_lookup_workload_* \
	       fhe/global_key_cache_* fhe/_workload_size_*

# CPU correctness gate: records the scoring trace once (real FHE) at the full
# hardware profile and checks the decrypted result against the plaintext
# reference. No simulator replay (see `sim` for that).
test: prepare build clean-trace
	cd fhe && $(SBIN)/key_generation $(SIZE) && $(SBIN)/encrypt_fingerprint $(SIZE) && $(SBIN)/score_opportunities $(SIZE) \
	  && $(foreach d,$(SCORE_DECRYPTS),$(SBIN)/$(d) $(SIZE) &&) true
	$(PYTHON) harness/verify_scores.py $(SIZE)

# SIM: full pipeline at $(SIZE) with the scoring stage replayed on the local
# FHETCH functional simulator, then verified against the plaintext reference.
# The first `score_opportunities` run records the trace (real FHE); the second
# finds the cached trace and replays it on fhetch_sim — the same trace Fog runs
# on the FPGA. This is the offline stand-in for a Fog run.
sim: build clean-trace
	$(PYTHON) harness/prepare_demo.py $(SIZE)
	cd fhe && export PATH="$(NB_FHETCH_BIN):$$PATH" \
	  && $(SBIN)/key_generation $(SIZE) && $(SBIN)/encrypt_fingerprint $(SIZE) \
	  && echo "== record ==" && $(SBIN)/score_opportunities $(SIZE) \
	  && echo "== replay (local sim) ==" && $(SBIN)/score_opportunities $(SIZE) \
	  && $(foreach d,$(SCORE_DECRYPTS),$(SBIN)/$(d) $(SIZE) &&) true
	$(PYTHON) harness/verify_scores.py $(SIZE)

# Fog: same pipeline, but the scoring trace is replayed on Niobium hardware via
# `fog submit`. Requires the `fog` CLI on PATH and credentials (`fog login`);
# see FOG.md. The first local `score_opportunities` run records the trace, then
# `fog submit` replays it on the device and returns the encrypted result.
fog: build clean-trace
	$(PYTHON) harness/prepare_demo.py $(SIZE)
	cd fhe && $(SBIN)/key_generation $(SIZE) && $(SBIN)/encrypt_fingerprint $(SIZE) \
	  && echo "== record ==" && $(SBIN)/score_opportunities $(SIZE) \
	  && echo "== fog submit (FPGA replay) ==" && fog submit $(SBIN)/score_opportunities $(SIZE) --target=FOG \
	  && $(foreach d,$(SCORE_DECRYPTS),$(SBIN)/$(d) $(SIZE) &&) true
	$(PYTHON) harness/verify_scores.py $(SIZE)

evaluate: validate-data compare

validate-data:
	PYTHONPYCACHEPREFIX=/tmp/stealthmatch-pycache $(PYTHON) harness/validate_catalog.py

compare: prepare $(BUILD)/key_generation
	PYTHONPYCACHEPREFIX=/tmp/stealthmatch-pycache $(PYTHON) harness/compare_examples.py

# Bootstraps the binary once if it is absent. It intentionally has no source
# prerequisites: use `make compare-build` after changing any .niob source.
$(BUILD)/key_generation:
	$(MAKE) build

compare-build: build compare
