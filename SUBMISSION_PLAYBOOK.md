# OpenAI Build Week — Submission Playbook

## Official baseline

- Build a working project with Codex using GPT-5.6.
- Select one track: Apps for Your Life, Work & Productivity, Developer Tools, or Education.
- Submit a project description, a public YouTube demo under three minutes, a runnable code repository, and the `/feedback` Codex Session ID covering most core functionality.
- The repository must be public with relevant licensing, or private and shared with `testing@devpost.com` and `build-week-event@openai.com`.
- Its README must include setup instructions, any needed sample data, and clear run instructions.
- Explicitly explain where Codex accelerated the build, which key decisions it informed, and how GPT-5.6 and Codex were used.
- A developer tool or plugin additionally needs installation instructions, supported platforms, and a judge-accessible way to test it without rebuilding it.

Current deadline: July 21, 2026, 5:00 PM Pacific.

## Judge-facing rubric

The official criteria are technological implementation, design, potential impact, and quality of the idea. Use this operational version while making decisions.

| Criterion | What a strong FHE submission proves | Evidence to capture |
| --- | --- | --- |
| Technological implementation | A real end-to-end encrypted workflow works. FHE is essential to the solution, not decorative. The project uses Codex and GPT-5.6 thoughtfully. | Reproducible run, plaintext-vs-FHE verification, timings, ciphertext/key sizes, architecture diagram, selected Codex session ID, short decision log. |
| Design | A real person can understand the privacy promise, run the happy path, recover from ordinary failures, and see an intelligible result. | Screen recording, UX screenshots, error/empty states, onboarding notes, demo script tested on a clean machine. |
| Potential impact | A named user has a credible privacy or data-sharing problem that FHE materially unlocks. The output does not silently create a new privacy leak. | User/problem statement, threat model, why existing plaintext/cloud approaches fail, output-leakage mitigations, realistic constraints and limitations. |
| Quality of idea | The concept is specific, memorable, and differentiated; the FHE capability changes what is possible. | One-sentence pitch, alternatives considered, why this workload is FHE-feasible, a clear before/after story. |

### Quality bar / kill tests

- The server must never receive plaintext inputs or a secret key.
- A plaintext reference must exist before claiming encrypted correctness.
- The encrypted path must be shown working in the demo, not simulated by a UI.
- The workload must be a fixed, data-oblivious circuit with a believable depth and performance budget.
- We must say plainly what FHE does not protect: output leakage, metadata/timing, malicious-server integrity, or both.
- The application needs a complete product loop, not only a benchmark or command-line proof of concept.

## Evidence ledger — capture as we build

### Product and judging

- Track choice and one-sentence pitch.
- Target user, concrete private input, decision/output, and why privacy blocks the current workflow.
- Short competitive/differentiation note.
- Screenshots or short clips at each product milestone.
- Demo narrative: problem (0:00–0:20), product use (0:20–1:20), encrypted proof (1:20–2:15), Codex/GPT-5.6 build story and impact (2:15–2:55).

### FHE design and proof

- Parties, assets, adversaries, trust assumptions, key ownership, and output recipient.
- Data flow diagram that labels plaintext, ciphertext, public/evaluation keys, and secret key.
- Why the computation is data-oblivious; chosen scheme and why.
- Circuit/depth estimate; SIMD packing mode and constraints.
- Plaintext fixture(s), expected outputs, and encrypted-vs-plaintext error report.
- Parameter settings, runtime by stage, peak memory, ciphertext/key/file sizes, batch size, and hardware/software environment.
- Output-privacy analysis and mitigations (rate limits, coarsening, DP, etc. if relevant).
- Known limitations and explicitly unsupported threat models.

### Codex and GPT-5.6 provenance

- Preserve the `/feedback` session ID once core functionality is built.
- Record a brief timeline of meaningful Codex contributions: design exploration, scaffold, tests, debugging, UX, documentation.
- Save 2–4 representative prompt/result excerpts or screenshots that show non-trivial collaboration.
- Record major decisions GPT-5.6/Codex helped surface, plus what we independently verified.
- Keep an accurate human-authorship note: do not overclaim autonomous work.

### Repository and delivery readiness

- README: problem, architecture, FHE security statement, quickstart, prerequisites, demo data, test command, limitations, license.
- One-command reproducible demo and one-command verification test.
- No secrets, real private datasets, secret keys, or large generated artifacts committed.
- Public demo URL; code repository URL; category; project description; `/feedback` session ID.
- If this becomes a developer tool: install instructions, supported platforms, and a hosted/demo/sandbox path for judges.

## Source links

- https://openai.com/build-week/
- https://openai.devpost.com/
