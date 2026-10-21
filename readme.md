# What Do AIs Know About History?

A small Streamlit companion to Daniel Hutchinson, [*Benchmarking as Source Criticism: From Recognition to Reasoning in LLM Assessment*](https://doi.org/10.5334/johd.489), *Journal of Open Humanities Data* 12 (2026), 43.

Four pages introduce the article, offer a ten-question history challenge, expose a defective benchmark item, and explore inspectable MMLU history evaluations. The challenge supports solo practice, **recorded** model answers from completed runs, and an explicitly enabled **live hosted open-model** opponent. Visitor answers and optional reflections remain in the Streamlit session and can be downloaded. They are not collected or added to evaluation data. The public pages and recorded/solo challenges need no API credential; live play requires a server-side provider token. No database or Google Sheets account is required.

## Run the app

Use Python 3.11 or newer:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For Streamlit Community Cloud, use `app.py` as the entry point and the repository's `requirements.txt`. Secrets are required only when live play is enabled. Old pages live in `archive/` and are not imported or registered. Their dependencies are intentionally excluded.

## Evaluate a model

The command-line runner uses the OpenAI Chat Completions API. The initial model is **GPT-6 Luna** (`gpt-6-luna`), with reasoning effort explicitly set to `none` for low latency. This choice is supported by the [official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna). Model and reasoning settings can be overridden; prefer a dated snapshot when one is available. Set `OPENAI_API_KEY` in your environment. Do not commit credentials. Live runs incur API charges. The script supports Linux/macOS; its checkpoint lock uses `fcntl`.

Inspect the prompt before making any requests:

```sh
python evaluate.py --output runs/luna-history --dry-run
```

Run a smoke assessment of one question per subject, then use a **new directory** for the full assessment:

```sh
python evaluate.py --output runs/luna-smoke --limit 1
python evaluate.py --output runs/luna-history
```

Repeat the exact command to resume. Completed responses (including invalid answers) are not requested again. Failed items are retried on resume. Model/settings/data/code changes require a new directory. Each response is atomically checkpointed to `run.json`, with a question-level `answers.csv` alongside it. An interruption after an API response but before checkpointing can cause that request to be repeated.

`--temperature` defaults to omission, meaning the provider default. Set `--temperature 0` only for models that support it. `--reasoning-effort` overrides the Luna default of `none`; for other model IDs it is omitted unless explicitly supplied. `--max-completion-tokens` defaults to 2048; this includes reasoning tokens on models that use them. An empty/truncated answer is unsuccessful under this protocol. Settings are recorded, never silently changed after an API rejection. No tools, browsing, or retrieval are supplied. Use the dry run to inspect the exact prompt.

Connection, timeout, rate-limit, and server failures receive up to three attempts. Other errors stop immediately. An unresolved failure is saved as an error and stops the run with a nonzero exit status, preserving completed work. Error types are recorded without potentially sensitive error-message bodies. API errors are not benchmark incorrect answers.

## Publish results

For bounded parallel Hugging Face assessments, use `evaluate_parallel.py`. It accepts an explicit nscale route, checks current route pricing, and reserves the remaining run conservatively including up to three attempts per item. It uses three workers by default (maximum four), records execution code hashes and pricing, validates the existing checkpoint, and saves completed responses in canonical order. A provider error stops new submissions while in-flight responses are drained and saved. Interrupted requests without saved responses can still incur charges.

```sh
.venv/bin/python evaluate_parallel.py --model Qwen/Qwen3-8B:nscale --output runs/qwen3-8b-nscale-history --ceiling-usd 2
```

The ceiling is a conservative reservation check at observed prices, not a provider billing limit. Completed invalid answers are preserved on resume. Keep `evaluate.py` and `history.py` unchanged when resuming an existing checkpoint because their hashes are part of its configuration.

`review_assessments.py --runs NAME ...` validates complete runs, checks returned model identities and token usage, and prepares a Markdown/JSON review under `data/`. Add `--publish-local` to copy those validated results into the local explorer. This command makes no inference requests or external publication.

Inspect `run.json` and `answers.csv`, including raw answers and invalid responses. Copy a completed **full** run into a named folder under `results/`:

```sh
mkdir -p results/luna-history
cp runs/luna-history/run.json results/luna-history/run.json
```

The app discovers it automatically. Commit this file when you are ready to publish. `runs/` is ignored by Git; `results/` is not. There are no fabricated or demonstration scores in the repository. Publication requires all 606 test items, the current dataset and protocol, correct prompt/question matching, and scores consistent with the raw answers. Smoke runs, incomplete runs, duplicates, and mismatched data are excluded. The app generates CSV and JSON downloads from the published record.

## Assessment protocol

- Test split: U.S. history (204), European history (165), World history (237).
- All five development examples for each subject precede every test question, in original order.
- Each test item is a fresh request, with original option order and no test answer in the prompt.
- Ask for a single letter. Strip surrounding whitespace and normalize case; accept only A, B, C, or D. Prose, punctuation, ambiguous letters and empty responses are invalid.
- Accuracy is correct / total for each subject; invalid outputs remain in the denominator. A full run with API failures is incomplete and cannot be published.
- Preserve dataset hash, model ID, returned model ID, dates, SDK version, code hashes, settings, complete prompts, raw responses, finish reasons and token usage.

This is a project-specific five-shot evaluation, **not an exact HELM reproduction**. See [Stanford's methodology](https://crfm.stanford.edu/2024/05/01/helm-mmlu.html) and [live leaderboard](https://crfm.stanford.edu/helm/mmlu/latest/) for wider comparisons. These three subjects are not a full MMLU score. Individual runs do not measure repeat-run stability. Public questions may have been in training data; correct answers cannot distinguish memorization from generalization or establish historical reasoning competence.

## Data and attribution

See [data/README.md](data/README.md) for provenance, attribution, checksums and source notices. The original primary-source and BaconBot experiments are retained in `archive/` for reference only. This edition preserves the project's participatory purpose while focusing on multiple-choice assessment.

## Checks

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use simulated responses in temporary directories; none are published as real model results. They cover the dataset, strict scoring, failure/resume behavior, publication validation and Streamlit quiz interactions.

## Browser preview before publication

Open `preview_launcher.ipynb` and run Start, or run:

```sh
.venv/bin/python preview.py start
.venv/bin/python preview.py check
.venv/bin/python preview.py stop
```

Start runs the local app and a Pinggy SSH tunnel, printing temporary public HTTPS URLs. Free tunnels expire after about 60 minutes; stop and start for a fresh URL. Stop closes both preview processes. The launcher uses the project virtual environment, keeps Streamlit security defaults, and stores ignored process records and logs in `.preview/`. It stops only processes whose saved identity matches. The preview subprocesses do not inherit `GH_TOKEN`, `GITHUB_TOKEN`, or `OPENAI_API_KEY`. It does not publish to GitHub or run model evaluations.

The launcher requires Linux (process identity checks use `/proc`), SSH, and outbound access to Pinggy on port 443. Review the app in your browser after the health check; health alone does not verify all interactions.

The notebook also has explicit **Start Pinggy tunnel only**, **Check app and current public link**, **Refresh public link**, and **Stop Pinggy tunnel only** cells. When Streamlit is already running, launch just the tunnel. When a free link expires, run **Refresh public link** to obtain a fresh URL while keeping the app process running. Equivalent commands are `preview.py tunnel-start`, `preview.py check`, `preview.py tunnel-refresh`, and `preview.py tunnel-stop` using the project virtual environment. Refresh/stop affect only this launcher's verified tunnel process.

## Interactive challenge and source criticism

The visitor challenge randomly selects ten items, excluding the three confirmed U.S. passage/question mismatches documented in `data/VALIDATION_2026-09-30.md` (canonical rows 22, 44, 130). The canonical CSVs and full evaluation protocol remain unchanged. The visitor selection is filtered, not a full benchmark score. Each question exposes its stable ID, locks the human choice before revealing model/key cards, and offers an optional unscored reflection. Session JSON hides unanswered keys and responses. The source-criticism exhibit is separate and unscored.

The model explorer renders subject accuracy, a selectable question disagreement matrix, and size/performance plots only from verified completed runs. It separately shows disclosed parameter counts from developer model cards; those are not fabricated benchmark scores. Undisclosed sizes stay unknown. `models.json` is a curated metadata catalog, not a list of guaranteed hosted models. Its four Qwen3 models provide a potential same-family comparison; hosting and inference settings still require verification. External published scores have not been imported or mixed with project runs.

## Live hosted opponent (Hugging Face selected)

Configure an inference-enabled `HF_TOKEN` in environment settings or Streamlit secrets. Never paste it into a notebook or commit it. The integration defaults to Hugging Face's OpenAI-compatible router and `Qwen/Qwen3-8B:nscale`, explicitly selecting the verified hosting route. It is **disabled by default**, including when a token is present. After inspecting a smoke assessment and configuring billing controls, enable it with `LIVE_ENABLED=1` and restart only the app process as needed. Model availability and authorization are not implied by a token's presence.

Operator settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LIVE_ENABLED` | `0` | Explicitly enable with `1` after smoke verification |
| `LIVE_PROVIDER` | `huggingface` | Selected provider; `openrouter` also supported |
| `LIVE_MODEL` | `Qwen/Qwen3-8B:nscale` | Exact requested model and hosting route; provider-default settings remain in effect |
| `LIVE_MAX_OUTPUT_TOKENS` | `2048` | Output budget including thinking; accepts 1–4096 |
| `LIVE_DAILY_REQUESTS` | `30` | Shared request cap per UTC day |
| `LIVE_DAILY_USD` | `1` | Shared conservative reservation allowance per UTC day |
| `LIVE_INPUT_USD_PER_MILLION` | `10` | Operator-set upper bound for input pricing |
| `LIVE_OUTPUT_USD_PER_MILLION` | `10` | Operator-set upper bound for output pricing |

Live responses have a 2048-token output cap and a 35-second timeout, with no automatic retries. The first response, invalid output, API failure, or interruption marker is retained in session state. Human answers and test keys are not sent to the provider. Exact benchmark prompts, output cap, response metadata, latency, and raw returned content can be downloaded after the human answer is locked. Live encounters remain separate from full assessments. Authenticated verification on 2026-09-30 found that the former 256-token cap produced three empty, truncated responses; 2048 tokens produced usable letters. These smoke checks establish integration behavior, not benchmark performance. Do not silently change model/settings or extract a convenient letter from explanatory text to improve scores.

`.live/allowance.json` is a locked, persistent per-day counter/reservation ledger containing no visitor answers or credentials. Failed attempts still reserve allowance. Dollar reservations use prompt UTF-8 bytes plus framing allowance and the output token cap at the configured upper pricing bounds. This is an application allowance, not a provider-enforced billing guarantee: verify price bounds, set a provider-side limit, and retain the ledger across process restarts. Independent deployments do not share a filesystem ledger. The command-line evaluator has separate behavior and is not governed by the public live allowance.

OpenRouter is optional; select `LIVE_PROVIDER=openrouter`, configure `OPENROUTER_API_KEY`, and use its model ID. The user selected Hugging Face for the next live verification.

## Open-model recorded assessments

Dry runs require no token and make no requests:

```sh
.venv/bin/python evaluate.py --provider huggingface --model Qwen/Qwen3-8B --output runs/qwen3-8b-smoke --limit 1 --dry-run
```

Once `HF_TOKEN` is visible, the next verification is:

```sh
.venv/bin/python evaluate.py --provider huggingface --model Qwen/Qwen3-8B --output runs/qwen3-8b-smoke --limit 1
```

Inspect all three raw answers, token usage, returned model identity, and finish reasons. The evaluator and live challenge both default to 2048 output tokens. To verify the real live request path once, run `.venv/bin/python verify_hf_live.py`; it saves three responses and checks duplicate prevention with an isolated ledger under ignored `runs/hf-live-verification/`. If results truncate or fail, choose and document supported settings before enabling public live play. Completed invalid answers are never replaced by better outputs within the same run.

Authenticated Hugging Face smoke assessments and live-path verification succeeded on 2026-09-30. Full runs use the explicitly priced `Qwen/Qwen3-8B:nscale` route. Use a new directory for every changed configuration. Publish only complete inspected canonical runs. The explorer will populate automatically from `results/*/run.json`. Existing OpenAI evaluator commands remain supported. See `data/HF_VERIFICATION_2026-09-30.md` for integration evidence and limitations.
