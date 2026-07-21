PYTHON := $(or $(PYTHON),python3)
NIOBIUM_CLIENT_ROOT := $(or $(NIOBIUM_CLIENT_ROOT),$(CURDIR)/third_party/niobium-client)

XCOMP := $(NIOBIUM_CLIENT_ROOT)/dsl_fhe/xcomp
BUILD := fhe/nb_out/build

.PHONY: prepare check compile build test evaluate compare compare-build validate-data

prepare:
	$(PYTHON) harness/prepare_demo.py

check:
	cd $(XCOMP) && $(PYTHON) nbc.py check $(CURDIR)/fhe/shared.niob $(CURDIR)/fhe/client.niob $(CURDIR)/fhe/server.niob

compile:
	mkdir -p fhe/nb_out
	cd $(XCOMP) && $(PYTHON) nbc.py compile $(CURDIR)/fhe/shared.niob $(CURDIR)/fhe/client.niob $(CURDIR)/fhe/server.niob --outdir $(CURDIR)/fhe/nb_out

build: compile
	cmake -S fhe/nb_out -B $(BUILD) -DNIOBIUM_CLIENT_ROOT=$(NIOBIUM_CLIENT_ROOT)
	cmake --build $(BUILD) --target key_generation encrypt_fingerprint encrypt_entity_query score_opportunities fuzzy_lookup decrypt_scores decrypt_timing decrypt_capital_readiness decrypt_conflict_penalty decrypt_eligibility_penalty decrypt_fuzzy_scores -j2

test: prepare build
	cd fhe && ./nb_out/build/key_generation 0 && ./nb_out/build/encrypt_fingerprint 0 && ./nb_out/build/score_opportunities 0 && ./nb_out/build/decrypt_scores 0 && ./nb_out/build/decrypt_timing 0 && ./nb_out/build/decrypt_capital_readiness 0 && ./nb_out/build/decrypt_conflict_penalty 0 && ./nb_out/build/decrypt_eligibility_penalty 0
	$(PYTHON) harness/verify_scores.py

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
