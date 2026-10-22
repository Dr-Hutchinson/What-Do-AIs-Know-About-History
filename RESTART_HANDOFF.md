# Restart handoff — 2026-09-30, interactive redesign

## Structural question audit — 2026-10-21

The user requested exclusion of structurally bogus questions from You versus the model and inclusion in Question the benchmark. All 606 test stems/options were screened with source grouping and full-item follow-up of suspects. A fresh upstream archive comparison passed for all six CSVs and 621 loaded test/dev rows. The audit now records 19 excluded items (16 U.S., 1 European, 2 World), including the original 3; visitor counts are 188, 164, and 235 respectively. See `data/STRUCTURAL_AUDIT_2026-10-21.md`, its JSON issue register, and the per-item CSV screening ledger. The exhibit exposes every excluded item, original key, and reason. Existing visitor sessions containing an excluded item restart on the next quiz render. Canonical data, evaluator code/prompts, and all four saved assessments remain unchanged. This structural screen is not certification of all remaining historical answers; borderline historical, attribution, and interpretive concerns remain outside the exclusion policy. Validation: 35 offline tests passed, dependency and whitespace checks passed, and protected data/evaluator/result files retained their original hashes. Older three-item counts below are historical.

## GitHub publication — 2026-10-21

The user authorized committing and pushing the completed local updates to the existing GitHub repository. This authorization supersedes older no-publication stopping points below. Publication includes the redesigned app, canonical data, four complete assessments, tests, archived experiments, and preview controls. Secrets, partial runs, live allowance state, and preview runtime state remain excluded. Public live play remains disabled locally; hosted secrets are managed separately. Browser visual verification remains outstanding. See Git history for the publication commit.

## Preview notebook update — 2026-10-01

At the user's request, `preview_launcher.ipynb` now explicitly exposes Start app and public link, Start Pinggy tunnel only, Check, Refresh public link, Stop Pinggy only, and Stop both. `preview.py` supports `tunnel-start`, `tunnel-refresh`, and `tunnel-stop`; refreshing stops only the verified managed tunnel and preserves the Streamlit process. The generic `/home/user/pingly_streamlit_skill/review_app_launcher.ipynb` tunnel section also uses these controls, replacing its blanket tunnel-killing commands; its separate review-app startup cells remain unchanged. Use the project notebook for the history app.

New code cells compile, `git diff --check` passed, and executing the actual project notebook refresh cell verified that the app PID stayed unchanged. The current temporary link is printed by Start/Check; do not reuse earlier URLs from this handoff. No model assessments or live-mode changes were made in this notebook update.

## Latest status — four full assessments complete, public live disabled

All four authorized assessments are now complete and validated, each containing 606 unchanged canonical questions (2,424 total responses). Copies are in local `results/`; the explorer and recorded-opponent selector discover them automatically. No unresolved API failures. Invalid outputs remain unchanged in the denominator.

Final checks: 32 offline tests passed, compilation and `git diff --check` passed, and real-result Streamlit interaction checks confirmed four recorded opponents, 12 subject rows, and chart rendering. Public live is disabled in both the observed environment and local secrets. Desktop/mobile browser screenshot verification is still outstanding.

Updated source-and-results backup: `/home/user/history-project-backup-2026-09-30-assessments.tar.gz` with adjacent `.sha256`. This backup excludes secrets, runtime ledgers, ignored partial/smoke runs, virtual environments, and Git history. It includes all four complete published-local results and the final review. Earlier backups predate these assessments.

Final preview started successfully and local Streamlit health passed. The launcher reported temporary URL https://fwbpb-35-215-7-200.free.pinggy.net (alternate https://jskpe-35-215-7-200.run.pinggy-free.link), but the subsequent public health check could not resolve the hostname. Do not claim public reachability from the launcher output alone. Free links expire; use `preview.py check` and a public health check before reusing them.

| Model | Correct | Accuracy | Invalid | Estimated saved-response token cost |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-4B-Instruct-2507 | 510/606 | 84.2% | 0 | $0.01273 |
| Qwen3-8B | 499/606 | 82.3% | 52 | $0.16120 |
| Qwen3-14B | 545/606 | 89.9% | 7 | $0.15896 |
| Qwen3-32B | 537/606 | 88.6% | 19 | $0.18811 |

Total estimated token cost for the four saved full runs: **$0.5210**. This is not the account bill; smoke requests, transient retries, and unsaved requests interrupted when switching runners may add small charges. The $10 added credit is a user-provided amount, not a verified remaining balance.

Final review: `data/ASSESSMENT_RESULTS_2026-09-30.md` and `data/ASSESSMENT_REVIEW_2026-09-30.json`, including subject results, pairwise disagreements, token counts, model identity checks, and known defective rows. Validation checked all exact prompts/options/keys/IDs and scores against raw responses. 8B invalid breakdown: 31 non-letter outputs, 19 empty responses, 2 truncated text responses. 14B: 7 empty/truncated responses. 32B: 5 non-letter outputs, 13 empty responses, 1 truncated text response. No letters were extracted from prose.

The 4B release differs in post-training and supports only non-thinking mode. One run per model, provider defaults, and truncation/format failures prevent explaining these differences by size alone. Known canonical defects remain in full runs. Public live remains explicitly disabled (`LIVE_ENABLED=0`); do not re-enable it from earlier historical notes. No Git commit/push/deployment performed.

The in-progress and credit/billing sections below describe earlier stopping points and are superseded by this completed status.

### Credit added; four-model assessments in progress

The user added $10 and authorized proceeding broadly. The 8B checkpoint resumed successfully. Three-item smoke checks also passed for `Qwen/Qwen3-14B:nscale`, `Qwen/Qwen3-32B:nscale`, and `Qwen/Qwen3-4B-Instruct-2507:nscale`. Public live remains disabled.

Full runs now use `evaluate_parallel.py`, which imports the unchanged evaluator configuration and adds separately recorded execution metadata. Three requests per model run concurrently; all completed responses are retained. The whole remaining run is reserved conservatively at freshly fetched nscale rates with up to three attempts per item. Per-run ceilings are $2 for 8B, $2 for 14B, $3 for 32B, and $0.50 for 4B Instruct. Provider errors stop new submissions and drain/save in-flight responses. Source/data/config validation and the shared checkpoint lock remain enforced. Switching from sequential execution interrupted up to three in-flight requests, which may have incurred small unsaved charges.

Check current `runs/*history/run.json` status before resuming anything; processes may still be active and locks will prevent duplicate writers. Completed invalid answers must remain unchanged. Commands:

```sh
.venv/bin/python evaluate_parallel.py --model Qwen/Qwen3-8B:nscale --output runs/qwen3-8b-nscale-history --ceiling-usd 2
.venv/bin/python evaluate_parallel.py --model Qwen/Qwen3-14B:nscale --output runs/qwen3-14b-nscale-history --ceiling-usd 2
.venv/bin/python evaluate_parallel.py --model Qwen/Qwen3-32B:nscale --output runs/qwen3-32b-nscale-history --ceiling-usd 3
.venv/bin/python evaluate_parallel.py --model Qwen/Qwen3-4B-Instruct-2507:nscale --output runs/qwen3-4b-instruct-nscale-history --ceiling-usd 0.5
```

The 4B Instruct run is complete and validated, copied into local `results/`: 510/606 correct (84.2%), no invalid/truncated responses, estimated token cost $0.01272995. Exact metadata for this later non-thinking release is in `models.json`; do not conflate it with original Qwen3-4B or attribute its differences to size alone. Real app interaction/rendering checks confirmed the recorded opponent and four charts.

`review_assessments.py` validates full canonical runs, returned model identities and token usage, generates Markdown/JSON reports under `data/`, and supports `--publish-local`. This is local inclusion only, not external deployment. Partial runs stay under ignored `runs/`. Final review reports should include all four once complete. Regression suite: 32 passed after isolating the empty-results test from actual results. No Git commit/push/deployment authorized or performed.

The remaining older status below is historical and is superseded by this credit-added continuation.

The user's latest direction is **keep public live disabled**. Local `LIVE_ENABLED` has been reset to `0`; the older activation description below is historical.

Authenticated three-item smoke assessments at 2048 tokens succeeded, including the explicit nscale route. The 256-token check produced three empty truncated responses. Actual live-path verification succeeded for all three subjects and repeated calls did not issue another request or alter the isolated ledger. Artifacts are in ignored `runs/`; detailed evidence is in `data/HF_VERIFICATION_2026-09-30.md`.

The full `Qwen/Qwen3-8B:nscale` assessment has **22 completed responses (20 valid, 2 invalid)**. Question 23 failed with **HTTP 402, credit/billing**. The checkpoint is `runs/qwen3-8b-nscale-history/run.json`. The user has been asked to add credits/enable billing. Do not make further requests until billing is ready. The incomplete run is not published. Preserve invalid answers unchanged.

Resume once billing is ready:

```sh
.venv/bin/python evaluate.py --provider huggingface --model Qwen/Qwen3-8B:nscale --output runs/qwen3-8b-nscale-history
```

Completed responses are skipped. Do not edit `evaluate.py` or `history.py` before resuming because checkpoint configuration includes their hashes. Inspect and validate a complete run before copying into `results/`. Multi-model scope has not been selected. Public live must remain disabled. No commit/push/deployment performed. Earlier backup archives may predate these changes.

The live output cap is configurable with `LIVE_MAX_OUTPUT_TOKENS` (default 2048, range 1–4096). Downloaded responses include the cap and response ID. Model metadata recognizes hosting suffixes. `verify_hf_live.py` provides one-time real live verification with a saved report preventing automatic repetition. Regression suite after these changes: 28 passed; browser visual review remains outstanding.

## Previous update — Hugging Face live play enabled

This update supersedes the earlier token/enablement stopping point below. `HF_TOKEN` is now visible. Saved smoke runs completed with valid letters at 2048 output tokens; the earlier 256-token runs truncated. The live backend now defaults to `Qwen/Qwen3-8B:nscale`, with 2048 output tokens. An actual `live.request_once` check returned D, model `Qwen/Qwen3-8B`, finish reason `stop`, in 4.13 seconds.

Live mode is enabled by `LIVE_ENABLED = "1"` in ignored `.streamlit/secrets.toml`; no token was copied into that file. Streamlit alone was restarted, preserving the current Pinggy URL: https://lyhos-35-215-7-200.free.pinggy.net. The visitor opponent defaults to **Live open model**, verified with Streamlit AppTest without submitting an additional API request. Shared allowance remains in `.live/allowance.json`. The source-only backup excludes enablement secrets and runtime counters, so it does not reproduce live activation by itself.

`tests/conftest.py` forces live mode off during offline tests, regardless of configured credentials, unless a test explicitly mocks the live integration. No full benchmark assessment has been published.

## Previous stopping point and authorization

The user approved an interactive redesign: a visitor challenge against an AI, a source-criticism exhibit, a live hosted open-model opponent, and exploratory model comparisons. Hugging Face was selected. The user then explained that adding `HF_TOKEN` requires an environment restart and requested completion of development and a handoff before that interruption.

**Local development and offline verification are complete. The next dependent step is a real Hugging Face smoke request, which requires `HF_TOKEN`.** The token was absent at the last process-level check. Do not display credentials. No environment restart, real model request, full paid assessment, commit, GitHub push, or deployment has been performed. Do not publish or run full model assessments without subsequent direction. Resume from this document rather than the previous three-page plan.

## Project and argument

Repository: `/home/user/What-Do-AIs-Know-About-History`

Article: Daniel Hutchinson, *Benchmarking as Source Criticism: From Recognition to Reasoning in LLM Assessment*, Journal of Open Humanities Data 12 (2026), 43. https://doi.org/10.5334/johd.489

Local article: `/home/user/hutchinson_benchmarking_paper.pdf`.

The visitor flow is: take the challenge → inspect answers → question what the score measures. The article's four dimensions are contamination resistance, content diversity, format diversity, and epistemological sophistication. Model size/training comparisons must not imply that size alone explains results. Different benchmarks and metrics must not be merged into a single interchangeable ranking.

## Implementation present

- `app.py`: four registered pages and wide layout; `.streamlit/config.toml`: light cream/teal theme.
- `views.py`: Start here, You versus the model, Question the benchmark, Explore model performance. Answer locking, source passage panel, human/model/key reveal cards, ten-cell comparison strip, optional reflections, stable question IDs, and downloadable sessions.
- `experience.py`: visitor curation, issue register, source/stem separation, session JSON. Unanswered keys and recorded responses are hidden from downloads.
- `live.py`: Hugging Face/OpenRouter hosted requests; Hugging Face selected. Explicit enable flag, locked persistent shared daily allowance, bounded output/timeout, no retries, retained first response/error/interruption marker, sanitized failure messages. Human choices and test keys are not sent to the provider.
- `explorer.py`: real full-run subject accuracy, selectable question disagreement matrix, documented-size versus performance plots, inference-settings comparison. Empty charts stay empty until real assessments exist. Separate model-card parameter chart is available immediately.
- `models.json`: four Qwen3 model cards, verified against developer disclosures: 4B (4.0B), 8B (8.2B), 14B (14.8B), 32B (32.8B). Apache 2.0 model-weight license. No synthetic scores.
- `history.py`: canonical data, exact five-shot prompts, strict single-letter scoring, publication validation.
- `evaluate.py`: checkpoint/resume evaluator now supports `--provider openai|huggingface|openrouter`, records endpoint/provider, and retains existing OpenAI behavior. Provider configuration changes require new output directories.
- `preview.py` / `preview_launcher.ipynb`: project-specific Start/Check/Stop controls for detached Streamlit and Pinggy processes. PID identity checked before termination; no blanket port/tunnel killing. Logs/state in ignored `.preview/`. Streamlit security defaults retained. Preview subprocesses do not inherit GitHub/OpenAI credentials; Hugging Face live configuration is inherited if configured.
- `validate_mmlu.py`: independent canonical archive comparison tool.
- `data/VALIDATION_2026-09-30.md`: source comparison evidence and confirmed defects.
- `readme.md`: updated operation, live controls, methods, and evaluation instructions.
- `tests/`: 28 offline checks, including mock hosted HTTP requests and Streamlit interactions.
- `archive/`: retired primary-source/BaconBot pages retained, outside active navigation.
- `results/`: no real completed assessments yet.

## Canonical data validation and defects

A fresh archive was downloaded from the link in https://github.com/hendrycks/test:

`https://people.eecs.berkeley.edu/~hendrycks/data.tar`

SHA-256: `bec563ba4bac1d6aaf04141cd7d1605d7a5ca833e38f994051e818489592989b`.

All six local CSVs match byte for byte. All 606 test rows and 15 development rows match through the loader: question, options in order, key, and stable ID. Subject test counts: U.S. 204, European 165, World 237.

**Confirmed upstream defects:** `high_school_us_history:test:022`, `:044`, and `:130` present Samuel Thomas's 1865 testimony about freedpeople with questions referencing Hamilton's Federalist No. 15. Row 130 asks about British forts in the Great Lakes and is a likely match to the visitor's report; exact quiz position 4 was not recoverable because random visitor sessions are not saved centrally.

These three items are excluded from visitor sampling (201 eligible U.S. items), annotated in the model explorer, and demonstrated separately in an unscored exhibit. **Canonical CSVs and full model assessments remain unchanged.** Validation establishes source fidelity, not expert semantic correctness of every item. A broader historical audit is future work.

The fresh archive currently exists at `/tmp/mmlu-validation-20260930.tar`; temporary files may disappear on restart. Re-download if needed to repeat independent validation.

## Verified during this session

- `28 passed` from `.venv/bin/python -m pytest -q` (final run).
- Compilation checks passed for all active Python modules.
- `git diff --check` passed.
- `pip check`: no broken requirements.
- Repeated canonical validation: 621 rows match.
- Actual app-entry navigation regression tested (registered page objects are used for `st.switch_page`).
- Streamlit health and Pinggy public health both returned successful responses.
- Mock live tests cover human-answer locking, no duplicate request on rerun/reflection, interruption retention, shared request/budget limits, corrupt-ledger refusal, provider payload, and failure privacy.
- Chart rendering tested against temporary test-only full-run fixtures, including documented parameter counts. Fixtures are not published.

**Browser screenshot verification could not run:** temporary Playwright/Chromium tools were installed, but Chromium lacks required shared libraries (starting with `libnspr4.so`). Attempted package downloads could not resolve packages from the environment's package index. No system packages were installed. Do not claim desktop/mobile layout or end-to-end browser interactions were verified. User browser review remains appropriate.

## Preview before restart

The preview was still healthy at the final checks:

- https://jvkte-35-215-7-200.free.pinggy.net
- https://sujue-35-215-7-200.run.pinggy-free.link

These are temporary public links. Free Pinggy sessions expire; a platform restart will require new processes and a new URL. Do not treat old logged URLs as proof of reachability.

```sh
cd /home/user/What-Do-AIs-Know-About-History
.venv/bin/python preview.py start
.venv/bin/python preview.py check
.venv/bin/python preview.py stop
```

`preview_launcher.ipynb` offers the same controls without shell commands. If theme changes have not appeared in an existing browser session, refresh/reconnect. If a new environment lacks dependencies, recreate/install the virtual environment from requirements first.

## Source backup and persistence

A reviewed source-only archive is prepared at:

`/home/user/history-project-backup-2026-09-30.tar.gz`

Its checksum is in `/home/user/history-project-backup-2026-09-30.tar.gz.sha256`.

The backup includes the project source, data, archive pages, tests, notebooks, theme, and this handoff. It excludes `.git`, `.venv`, caches, secrets, `.env` files, runtime preview/live state, and ignored assessment runs. Source bytes and archive member presence were checked after creation. Download the archive before a restart that might replace workspace storage; another file inside the same workspace is not an independent external backup. Git history is not in this source archive; the existing checkout's base commit is recorded below.

## Resume after token configuration/restart

1. Read this file and `readme.md`. Confirm repository/source/data still exist and inspect tracked **and untracked** Git status.
2. Recreate/install `.venv` if necessary. Requirements now include `plotly==6.3.0` alongside pinned Streamlit/OpenAI SDK versions. Run offline tests if dependencies/source changed.
3. Check only the presence of `HF_TOKEN`, `GH_TOKEN`, and `OPENAI_API_KEY`. Last checks: GitHub/OpenAI tokens present, HF absent. Do not print their values, place them in URLs, notebooks, or documentation.
4. **Keep `LIVE_ENABLED=0` until verification.** Configure `HF_TOKEN` with inference-provider permission. HF routing/model access requires an actual request to verify; public model metadata listed Qwen3-8B conversational hosting through nscale and featherless-ai during this session, but this is not authenticated inference evidence.
5. When the user resumes live verification, run the three-item smoke assessment (one per subject):

```sh
.venv/bin/python evaluate.py --provider huggingface --model Qwen/Qwen3-8B --output runs/qwen3-8b-smoke --limit 1
```

Inspect all raw responses, returned model IDs, finish reasons, usage, provider defaults, and truncation. The CLI defaults to 2048 output tokens; live play uses 256. Qwen3 can use thinking mode, so verify a **separate** smoke run at the live cap:

```sh
.venv/bin/python evaluate.py --provider huggingface --model Qwen/Qwen3-8B --output runs/qwen3-8b-live-cap-smoke --limit 1 --max-completion-tokens 256
```

If provider/default settings do not produce usable final letters, choose documented supported settings or another hosted model and use a new directory. Do not rewrite prompts/extract letters silently or retry completed invalid answers for better scores. Exact five-shot benchmark prompts are shared by evaluator and live requests. The live path additionally needs its actual `live.request_once` smoke checked using a temporary verification ledger before enablement; mock tests already passed, but there has been no authenticated request.

6. Verify pricing bounds and provider-side spending controls, then set `LIVE_ENABLED=1`. User selected Hugging Face; OpenRouter is an implemented alternate, not the chosen next step. Restart the app process to inherit newly configured environment values. A platform restart is not necessary for an app-only restart once variables are visible.
7. Public live limits default to 30 requests and a conservative $1 reservation allowance per UTC day, 256 output tokens, 35-second timeout, no retries. Pricing upper bounds default to $10/million input and output tokens. These are application reservations, not a provider-enforced billing guarantee. Verify prices before activation. Retain `.live/allowance.json` across app restarts. CLI assessments are separate and do not use this allowance.
8. Start the preview and review the real live reveal in a browser, checking that refresh/reflection does not issue another request for the item. Do not put token values in screenshots/logs.
9. Full 606-item and multiple-model assessments are deferred. Their costs/settings need review before running. Only inspected completed full canonical runs go into `results/`; partial or live-session scores are not published benchmark results.
10. Commit/push/deploy only under later user direction. Authenticate and fetch upstream before integration; do not overwrite remote work or force-push. Pushing the Streamlit-tracked branch may trigger deployment.

## Git state

Base commit: `878124541c224a3d0ed9b821b3aa9cffa26dc303` (2025-09-15, Update benchmark_results_1.py).

All implementation remains local and uncommitted. Tracked modifications include `app.py`, `readme.md`, and `requirements.txt`. Tracked `pages/` and `multipage.py` deletions correspond to retained files under the untracked `archive/` directory. Most new modules, data, tests, theme, notebook, and this handoff are untracked: reviewing only a tracked diff omits the implementation. Remote state has not been authenticated/fetched during this work.
