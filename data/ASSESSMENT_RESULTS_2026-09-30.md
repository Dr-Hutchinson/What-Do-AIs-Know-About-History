# Qwen3 history assessments

Reviewed: 2026-09-30T12:10:24.562727+00:00

All listed runs contain the unchanged 606 canonical test questions and exact five-shot prompts.

| Model / route | U.S. | European | World | Overall | Invalid | Truncated | Estimated token cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen/Qwen3-4B-Instruct-2507:nscale | 85.3% | 81.8% | 84.8% | 84.2% | 0 | 0 | $0.0127 |
| Qwen/Qwen3-8B:nscale | 80.9% | 82.4% | 83.5% | 82.3% | 52 | 21 | $0.1612 |
| Qwen/Qwen3-14B:nscale | 91.7% | 86.7% | 90.7% | 89.9% | 7 | 7 | $0.1590 |
| Qwen/Qwen3-32B:nscale | 90.2% | 84.2% | 90.3% | 88.6% | 19 | 14 | $0.1881 |

One run per model; provider-default sampling. 4B Instruct 2507 has different post-training and supports only non-thinking mode. Known canonical defects retained. Invalid outputs count as unsuccessful. Token-cost estimates exclude unsaved interrupted requests and are not account billing records.

Raw answers, prompts, keys, usage, and response identities remain inspectable in each `run.json`. The explorer shows per-subject results and question disagreements. These are three-subject history results, not full MMLU scores or isolated measurements of model size.

The three known U.S. passage/question defects remain in full assessments and are excluded only from visitor sampling. See `VALIDATION_2026-09-30.md`.

## Output validity

- Qwen/Qwen3-4B-Instruct-2507:nscale: No invalid outputs.
- Qwen/Qwen3-8B:nscale: 31 non-letter output, 19 empty response, 2 truncated text.
- Qwen/Qwen3-14B:nscale: 7 empty response.
- Qwen/Qwen3-32B:nscale: 5 non-letter output, 13 empty response, 1 truncated text.

A normally finished response such as `Answer: B` or a letter followed by an explanation is invalid under the unchanged single-letter rule. No letter is extracted from prose and no completed response is retried to improve its score.
