# Hugging Face authenticated verification — 2026-09-30

## Completed continuation

After the user added $10 and authorized broader work, all four full nscale-routed assessments completed and passed canonical publication validation: Qwen3-4B-Instruct-2507, 8B, 14B, and 32B. Results are included in the local explorer and recorded-opponent selector. Estimated saved-response token costs total $0.5210, excluding smoke requests, transient retries, and unsaved interrupted requests. See `ASSESSMENT_RESULTS_2026-09-30.md` and `ASSESSMENT_REVIEW_2026-09-30.json` for the full review. The earlier billing stopping point below is historical.

Public live play remains disabled. No external deployment or GitHub publication performed.

Authenticated inference is verified. Credentials were read only from the environment and are absent from reports.

| Check | Requests | Result |
| --- | ---: | --- |
| Qwen3-8B automatic route, 2048 output tokens | 3 | Valid and correct D/C/A; `stop`; 341/394/359 completion tokens |
| Same model, 256 output tokens | 3 | Empty responses; `length`; all invalid; preserved unchanged |
| Qwen3-8B explicitly routed to nscale, 2048 tokens | 3 | All valid and correct; `stop` |
| Actual live `ensure_answer` → `request_once`, nscale, 2048 tokens | 3 | All valid; `stop`; repeated calls reused the response and did not change the isolated ledger |

Each check used the first canonical test question in each subject and the unchanged five-shot prompts. Three-item checks establish integration behavior, not historical capability or a publishable benchmark score. All artifacts remain under ignored `runs/`.

The live default is now `Qwen/Qwen3-8B:nscale` with 2048 output tokens. `LIVE_MAX_OUTPUT_TOKENS` allows an explicit 1–4096 budget. The timeout remains 35 seconds and automatic retries remain disabled. Downloadable live responses record the cap and response ID. Model metadata lookup recognizes HF route suffixes while retaining the requested model ID in run records.

The public [HF router model listing](https://router.huggingface.co/v1/models) returned nscale input/output prices of $0.07/$0.18 per million tokens. The conservative full-run estimate, using prompt UTF-8 bytes plus 512 framing units and all 2048 output tokens for each of 606 questions, was $0.6567. This is a token-cost estimate at observed rates, not a guaranteed bill. [HF pricing documentation](https://huggingface.co/docs/inference-providers/pricing) documents organization spending controls; account controls have not been inspected.

Public live play remains disabled at the user's direction. No deployment or GitHub push is authorized. Full-run responses, including invalid outputs and known defective canonical items, must remain unchanged. Incomplete runs cannot enter `results/`.

Offline regression suite after implementation: 28 passed. Browser layout verification remains outstanding.

## Full assessment stopping point

`runs/qwen3-8b-nscale-history/run.json` contains 22 completed responses (20 valid, 2 invalid) plus a failed item at U.S. row 23. The resumed request returned HTTP 402, categorized privately as credit/billing without printing the provider error body. The run is incomplete and was not copied into `results/`. No further requests should run until credits/billing are ready. Resume with the same evaluator command; completed invalid answers are retained.
