# StealthMatch MVP

## Promise

StealthMatch lets a founder discover suitable startup-support opportunities without sending their unannounced thesis, strategic needs, or conflict concerns to the matching service in plaintext.

The server receives an FHE-encrypted 62-value private mandate and returns an encrypted total plus four encrypted score components: timing, capital/readiness, private-conflict penalty, and eligibility penalty. It never receives the founder's actual values, conflict selections, component values, or secret key.

## Private mandate, not generic private labels

The product must not encrypt generic labels that a founder would readily publish.
Sector, broad stage, and generic support interests are public filters. The
encrypted mandate contains concrete financial values, deadlines, evidence
counts, and named conflict / target-account / dependency sets. These are the
facts that change a match and that a founder should not need to disclose to the
matching service.

The detailed schema and fixed score contract are in
[PRIVATE_MANDATE_SCHEMA.md](PRIVATE_MANDATE_SCHEMA.md). Founders will never
see a binary vector, an approximate-arithmetic error, or a raw distance. Those
are implementation diagnostics. The result is a ranked research shortlist
with local explanations, eligibility caveats, and official links; it does not
promise funding, admission, or absence of conflicts.

## Quality claim we can support

We will not claim to predict investment. We claim that concrete confidential values and identities can change *opportunity fit* beyond public filters. The evaluation harness compares:

- a public baseline using sector, stage, and geography; and
- the full mandate, including actual financial/timing values and conflict overlap.

It reports top-3 precision against hand-authored reviewer labels, paired-scenario separation, and encrypted-versus-plaintext numerical agreement.

## Privacy boundary

The client owns the FHE secret key. The server owns the opportunity profile database. Setup transmits only public/evaluation keys. Per request, the client sends only ciphertexts; the server returns only ciphertexts. The user decrypts and ranks locally.

Not protected: request timing, request count, and whatever the user chooses to disclose after receiving results. The MVP does not collect pitch decks, source code, customer lists, names, exact revenue, or cap tables.
