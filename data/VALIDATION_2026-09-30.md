# MMLU history validation — 2026-09-30

A visitor reported a quiz item pairing a Civil War/Reconstruction quotation with a Federalist question. Investigation found three clear passage/question mismatches in the canonical U.S. history test data.

## Source comparison

Downloaded a fresh archive from https://people.eecs.berkeley.edu/~hendrycks/data.tar, the dataset linked by https://github.com/hendrycks/test. Its SHA-256 matched the recorded archive:

`bec563ba4bac1d6aaf04141cd7d1605d7a5ca833e38f994051e818489592989b`

All six local CSVs were byte-for-byte identical to the corresponding archive members. All 606 test rows and 15 development rows were checked for question, four options in order, answer key, and stable row ID through the application loader. No local alignment differences were found.

Repeat the comparison against a separately downloaded archive with:

```sh
.venv/bin/python validate_mmlu.py /tmp/mmlu-validation-20260930.tar
```

## Confirmed upstream passage mismatches

Each of these items presents Congressional testimony by Samuel Thomas dated 1865 about the treatment of freedpeople, but asks about Alexander Hamilton and Federalist No. 15:

| Stable item ID | Question topic | Upstream key |
| --- | --- | --- |
| high_school_us_history:test:022 | Hamilton's explanation of the problems in Federalist No. 15 | C |
| high_school_us_history:test:044 | Hamilton's proposed remedy | B |
| high_school_us_history:test:130 | Developments contributing to the sentiment in Federalist No. 15 | A |

The excerpt supplied by these items is not the Federalist excerpt their question stems reference. Row 130, whose keyed option concerns British forts in the Great Lakes, is a possible match to the visitor's description; the exact session item was not established. Quiz position 4 is random and is not canonical row 4. No questionnaire session record was saved to disk by the app.

Streamlit AppTest reproduced each of the three affected rows and confirmed that displayed question text, all four options, and scoring match the local source. The existing offline suite passed: 17 tests. These checks do not imply the official keys are independently historically validated.

## Limits and next decisions

This was an exhaustive fidelity/loader comparison, not an expert semantic review of all 621 items. At least three upstream defects are confirmed; their total prevalence remains unknown. No canonical rows, answer keys, sampling rules, or evaluation protocol were changed.

Preserve the canonical files for reproducible MMLU comparisons. A separate issue register can annotate suspect items. A curated visitor quiz could exclude reviewed defective items while recording that it is a filtered selection; any filtered model scores must be labeled separately from canonical scores. Displaying stable question IDs and offering a session download would make future reports easier to trace without collecting visitor answers centrally.
