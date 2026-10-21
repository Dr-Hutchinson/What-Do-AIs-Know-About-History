# Project direction and live-model usage notes

Prepared 2026-09-30 for user review and future sessions.

This document consolidates the decisions, findings, and recommendations already discussed in this session. It is not a fresh article review, repository audit, or provider authentication check. The user clarified that an older prompt had been loaded accidentally; the current request is to preserve the discussion in readable Markdown and plain text. No application behavior or quota settings were changed while preparing these documents.

## Purpose and connection to the article

What Do AIs Know About History? began as a participatory digital history project inviting historians and the public to investigate generative AI. The user identifies this project as the original setting from which the later article emerged:

Daniel Hutchinson, *Benchmarking as Source Criticism: From Recognition to Reasoning in LLM Assessment*, Journal of Open Humanities Data 12 (2026), 43.

Article: https://doi.org/10.5334/johd.489

Local reference: /home/user/hutchinson_benchmarking_paper.pdf

The revised project returns to its original invitation: test your historical knowledge against a language model. The quiz should draw visitors into the article's argument about what benchmarks measure. A model's agreement with a multiple-choice key is evidence of success on that assessment; it does not by itself establish historical expertise, original synthesis, or critical engagement with evidence.

The article's four dimensions provide the interpretive framework:

- Contamination resistance: public benchmark questions may have been encountered during training. Correct answers alone cannot distinguish memorization from generalization.
- Content diversity: MMLU's history subjects represent particular curricula and uneven distributions of historical knowledge. World History does not guarantee balanced global coverage.
- Format diversity: selecting among four supplied answers differs from constructing an explanation or synthesizing evidence.
- Epistemological sophistication: historical practice involves questioning sources, weighing evidence, and judging interpretations. The benchmark itself also deserves source criticism.

The desired visitor progression is: take the challenge, inspect the answers, then question what the score means.

## Agreed project scope

The active project should focus strictly on MMLU history assessment and interpretation.

- Retire primary-source analysis and BaconBot from the public application. Preserve their code in archive/ for project history and reference.
- Use the canonical MMLU U.S., European, and World history test subjects: 204, 165, and 237 questions respectively, totaling 606 test items.
- Offer a ten-question visitor challenge, including a live hosted model opponent when configured and available.
- Support recorded opponents drawn from completed, inspected model assessments.
- Provide a reproducible command-line method for assessing model performance across the full canonical history dataset.
- Make prompts, raw responses, settings, answer keys, scoring, and provenance inspectable.
- Explain what these scores can and cannot establish.

Separate source-criticism exhibits interpret the MMLU assessment; they do not restore the retired general-purpose primary-source analyzer. Other benchmarks, new language-specific datasets, and open-ended assessment would require a later scope decision. Comparing Chinese-developed and European-developed models on the same MMLU questions is within scope; asserting their historical specialization from their origin is not justified.

## Visitor experience developed in this session

The interface has four destinations:

1. Start here: introduce the challenge and the article's central questions.
2. You versus the model: select a subject and opponent, answer ten questions, and compare outcomes.
3. Question the benchmark: investigate a defective canonical item in a separate, unscored exhibit.
4. Explore model performance: inspect recorded assessments, model metadata, and comparisons.

The challenge locks the visitor's answer before requesting the live model's choice. It then reveals cards for the visitor, model, and official benchmark key. A ten-cell outcome strip shows where both matched the key, neither matched, or only one matched. An optional reflection asks whether the visitor relied on the passage, prior knowledge, answer choices, or guessing. These reflections are unscored.

Stable item IDs make observations traceable. Visitors can download their session, including completed answers and available model responses. Unanswered keys and recorded model answers are withheld from the download. Visitor answers are not collected centrally or incorporated into benchmark scores.

A live API failure is separate from an incorrect or invalid benchmark answer. A short live encounter is also separate from a full published model assessment.

## Dataset validation and the defective-question finding

The visitor reported a Civil War/Reconstruction passage paired with a Federalist question. Investigation found three canonical U.S. history items with the same mismatch:

- high_school_us_history:test:022
- high_school_us_history:test:044
- high_school_us_history:test:130

These pair Samuel Thomas's 1865 testimony about freedpeople with questions referring to Hamilton's Federalist No. 15. Row 130 concerns British forts in the Great Lakes and is a possible match to the report. The exact random quiz position 4 was not established.

A fresh download of the original MMLU archive matched all six local CSVs byte for byte. All 606 test rows and 15 development examples matched through the application loader, including questions, option order, answer keys, and stable IDs. The mismatch originated upstream; the application was not swapping passages or options between rows.

The three reviewed defective items are excluded from the visitor quiz, leaving 201 eligible U.S. items. They remain in the unchanged canonical dataset and full model evaluations for reproducibility. The exhibit makes the defect available for discussion without scoring it against the visitor. Fidelity to MMLU does not establish that every MMLU item is historically sound; a broader semantic audit remains future work.

Detailed findings: data/VALIDATION_2026-09-30.md

Reusable comparison tool: validate_mmlu.py

Canonical source: https://github.com/hendrycks/test

## Model assessment method

Each canonical test question is a fresh request with all five development examples for its subject. Original question text and option order are retained. The test key and visitor answer are not supplied to the model. No browsing, retrieval, or conversational history across test items is provided.

The model is asked for one letter. Scoring strips surrounding whitespace and normalizes case, then accepts only A, B, C, or D. Explanations, punctuation, ambiguous answers, and empty responses are invalid and remain in the accuracy denominator. Completed invalid responses are not requested again to improve the score.

API failures leave a full assessment incomplete. Only inspected complete 606-item runs matching the dataset and protocol qualify for publication. Smoke runs, visitor encounters, and mixed-model sessions do not qualify.

The evaluator records exact prompts, raw responses, requested and returned model identities, settings, token usage, dates, and code/data provenance. It supports checkpoints and resume. Configuration changes require a new output directory.

HELM is useful methodological context, but our protocol is not an exact HELM reproduction and these three subjects are not a full 57-subject MMLU score.

HELM methodology: https://crfm.stanford.edu/2024/05/01/helm-mmlu.html

## Current live integration as established in the discussion

The chosen provider is Hugging Face. Its router serves a hosted open model; the model does not run inside the Streamlit workspace.

The configured default is Qwen/Qwen3-8B:nscale, with a 2048-token output cap, a 35-second timeout, and no automatic retries. Earlier 256-token smoke runs truncated before returning final answers. Saved 2048-token smoke runs and an actual live-backend request returned usable letters. The returned model identity was Qwen/Qwen3-8B.

HF_TOKEN became visible after environment configuration. Live play was enabled through LIVE_ENABLED in the ignored Streamlit secrets file; the token itself was not copied into that file. The actual app was checked to expose Live open model as its default opponent.

The first response, invalid output, API failure, or interruption marker is retained for the item in session state. Reruns and reflections do not automatically issue another inference request. A shared persistent allowance ledger lives in .live/allowance.json. Offline tests explicitly disable live play so configured credentials cannot cause accidental paid test traffic.

The most recent reported verification was 28 passing offline tests. This document does not represent a new test run. Browser screenshot verification previously failed because Chromium's required shared libraries were absent; no desktop/mobile screenshot verification should be claimed.

## Why the quiz stopped near question seven

The evidence points to the application's daily reservation guard, rather than a demonstrated Hugging Face rate-limit event.

At the latest quota inspection, .live/allowance.json recorded seven total requests and $0.91835 reserved against a $1 daily allowance. Total requests include verification traffic and are not necessarily identical to the visitor's count of quiz questions. Only about $0.08165 of reservation allowance remained, so a subsequent question's conservative reservation could exceed it.

This is not a record of $0.91835 actually billed by Hugging Face. The implementation reserves estimated prompt tokens plus the maximum allowed output, using configured upper pricing bounds, and does not reconcile the reservation after completion. Failed attempts also retain their reservation.

The default upper bounds are $10 per million input tokens and $10 per million output tokens. The application also has a separate 30-request daily cap shared across visitors. Its ledger resets by UTC date. These settings were not changed during the quota investigation.

The current public catalog listed the actual Qwen3 8B/nscale route at $0.07 per million input tokens and $0.18 per million output tokens. The default reservation rates are therefore much more conservative than this route's listed rates.

Illustration, not an account bill: 2500 input tokens and 500 output tokens at those listed prices cost approximately $0.000265 per question, or $0.00265 for ten questions. Actual usage, provider pricing, and account balance vary. The visible response can be one letter while reported generated-token usage is much larger.

Recommended accounting improvement: use verified route-specific prices, reserve before requests, and reconcile completed reservations against actual token usage while retaining a margin and handling failed/uncertain requests conservatively. Preserve separate request limits and provider-side controls. Make the interface distinguish local allowance exhaustion, provider credit exhaustion, temporary throttling, and provider failure.

Public pricing/model catalog: https://router.huggingface.co/v1/models

## Free usage and routing

Hugging Face's pricing documentation currently lists $0.10 monthly inference credits for free accounts, subject to change. These are shared across routed inference, not a new free allocation per model. The account's remaining provider credits were not inspected during this discussion.

Switching to a cheaper model stretches the same credits. Switching eligible hosting routes may help with provider capacity. Neither action replenishes the application's shared cap or an exhausted Hugging Face credit pool.

OpenRouter offers explicit free model variants and a free router. Account-level minute/day limits still apply across free models. Its automatic free router selects among available models, so it is a poor default for a fixed, identifiable benchmark opponent. A current public catalog check found qwen/qwen3.8-27b:free; availability and license suitability still require verification before integration.

Independent services such as Groq may offer separate free allowances, but require their own credentials and impose request/token limits. Multiple keys for one account do not create independent quotas. Published Groq limits apply at the organization level.

A practical routing strategy should use legitimate available service allowances, explicit model identities, and a reviewed license allowlist. It should never silently substitute a paid route when free access is exhausted.

Hugging Face pricing: https://huggingface.co/docs/inference-providers/pricing

Hugging Face routing: https://huggingface.co/docs/inference-providers/index

OpenRouter limits: https://openrouter.ai/docs/api_reference/limits

OpenRouter free router: https://openrouter.ai/openrouter/free

Groq limits: https://console.groq.com/docs/rate-limits

## Candidate model roster

These are options for review, not a claim that each has already been integrated or tested. Listed prices were obtained from public metadata during the discussion and may change. Prices below are input/output dollars per million tokens.

- Small economical default: Qwen3-4B-Instruct-2507. Four billion parameters, Apache 2.0 model-weight license, explicitly non-thinking. HF/nscale listed $0.01/$0.03. A promising answer-letter opponent with a small output requirement; its lower cost must still be verified in smoke tests.
- Existing small opponent: Qwen3-8B. Developer-disclosed size is 8.2 billion parameters. HF/nscale listed $0.07/$0.18. Already verified through our live integration.
- Larger same-family comparison: Qwen3-32B. Developer-disclosed size is 32.8 billion parameters. HF/nscale listed $0.08/$0.25. Listed hosting is not proof of successful inference with our settings.
- Medium reasoning contrast: DeepSeek-R1-Distill-Qwen-14B. HF/nscale listed $0.20/$0.20. Reasoning may increase generated-token usage and latency. Record its model lineage and applicable licenses, not just the DeepSeek name.
- Alternative family across sizes: Ministral 3 at 3B, 8B, and 14B. The cited releases use Apache 2.0 licenses. Hosting needs verification; the inspected HF model mapping did not provide a live route for the selected 8B model.
- Medium-to-large general-purpose alternative: Mistral Small 3 at 24B, an Apache 2.0 release. Hosting needs verification. The inspected mapping for a related Small 3.2 release supplied no live HF route.
- Training-provenance emphasis: OLMo 3 at 7B and 32B. Ai2 releases weights, development tools, and training artifacts. This offers a stronger source-criticism connection than parameter counts alone. Hosted access remains unresolved; the inspected 7B HF mapping reported a provider error.

Prefer instruct/chat variants for the visitor opponent. A base model is a different experimental object and should not be substituted casually for an instruction-tuned model.

Qwen 4B card: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507

Qwen 8B card: https://huggingface.co/Qwen/Qwen3-8B

Qwen 32B card: https://huggingface.co/Qwen/Qwen3-32B

DeepSeek licensing and model lineage: https://huggingface.co/deepseek-ai/DeepSeek-R1

Mistral 3 releases: https://mistral.ai/news/mistral-3/

Mistral Small 3: https://mistral.ai/news/mistral-small-3/

OLMo model family and artifacts: https://allenai.org/olmo

## Openness, specialization, and interpretation

Open weights, permissively licensed weights, accessible training code, and accessible training data are distinct properties. A permissive weight license does not prove a fully documented training pipeline. Open-source availability also does not imply free hosted inference.

OLMo is particularly relevant when training provenance is the question. Qwen, DeepSeek, and Mistral provide useful contrasts in model family, development context, architecture, and post-training. Model cards should identify the exact release and its disclosures.

Chinese-developed models are not automatically Chinese-history specialists, and French-developed Mistral models are not automatically European-history specialists. Compare actual results and documented training information. The existing English-language MMLU history sets alone cannot establish language- or curriculum-specific specialization.

Keep model size separate from architecture and inference effort. For mixture-of-experts models, distinguish total and active parameters. Do not infer undisclosed parameter counts. Performance differences are associations; a comparison of unrelated models does not isolate size or training as the sole cause.

## Recommended next update

1. Correct the overly conservative reservation accounting without simply removing limits or erasing usage history.
2. Expose clear allowance status and error categories before a visitor reaches an unexpected stop.
3. Add a reviewed opponent selector, initially considering Qwen 4B, the existing Qwen 8B, Qwen 32B, and a verified Mistral route. Pursue OLMo when hosted access is established.
4. Keep one chosen model fixed for a normal ten-question challenge.
5. If a model becomes unavailable, offer a clearly labeled recorded fallback or a visitor-selected change of opponent.
6. A separate optional model-relay mode may show a different model per question, but must display provenance and separate scores by model. Never publish its mixed score as one model's MMLU performance.
7. Prefer explicit free routes when free-only play is selected; do not rely on an opaque automatic router that can choose models outside the openness criteria.
8. Populate performance charts from inspected full canonical assessments. Continue excluding smoke and visitor-session results from publication.

Recorded full-run answers are an important way to keep the project usable when live allowances run out. They preserve an inspectable opponent while making the live-versus-recorded distinction visible.

No new models, routing policies, quota adjustments, or full assessments have been implemented by this document-writing task. These recommendations await the user's next implementation instruction.

## Notes for future sessions

Read this document alongside RESTART_HANDOFF.md and readme.md. Some earlier handoff sections describe pre-token or pre-activation states; later updates supersede them. Verify current settings rather than assuming every historical statement remains current.

Do not print credentials, copy them into these documents, or ask the user to paste them into chat. Check variable presence only, and use the configured secret mechanism for API requests.

The preview is a local Streamlit app exposed through a temporary Pinggy tunnel. It is not a GitHub deployment. Free tunnel URLs expire and change on restart, so use the launcher's current output rather than a saved historical link:

    cd /home/user/What-Do-AIs-Know-About-History
    .venv/bin/python preview.py start
    .venv/bin/python preview.py check
    .venv/bin/python preview.py stop

Use the printed HTTPS URL in the user's own browser. The launcher runs headlessly and should not attempt to launch a browser inside the sandbox.

The implementation remains local and uncommitted as last established in the discussion. No commit, push, deployment, full paid evaluation, or environment restart is authorized by creating these review documents. Fetch and review remote state before any subsequently authorized publication.
