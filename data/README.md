# MMLU history data

Source: the original [MMLU repository](https://github.com/hendrycks/test), which links to [data.tar](https://people.eecs.berkeley.edu/~hendrycks/data.tar).
Retrieved 2026-09-29. The six CSV files here are byte-for-byte copies of the three history subjects' `dev` and `test` files. No questions, option orders, or answer keys were edited. `manifest.json` records the source URL, archive SHA-256, individual file SHA-256 hashes, and row counts. The application verifies file hashes before exposing model comparisons.

| Subject | Test | Development |
| --- | ---: | ---: |
| high_school_us_history | 204 | 5 |
| high_school_european_history | 165 | 5 |
| high_school_world_history | 237 | 5 |

CSV columns (no header): question, A, B, C, D, answer letter. Stable IDs combine subject, split and the one-based row number. Only test rows appear in quizzes and scores; development rows are worked prompting examples.

Citation: Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, and Jacob Steinhardt. *Measuring Massive Multitask Language Understanding*. ICLR 2021. https://arxiv.org/abs/2009.03300

The source repository publishes an MIT license, reproduced in `MMLU-LICENSE` with its copyright notice. Questions include material compiled from educational sources; this attribution does not assert new ownership of underlying excerpts. Preserve upstream notices and the dataset's educational/research provenance when redistributing.
