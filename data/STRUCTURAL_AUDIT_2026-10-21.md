# MMLU history structural audit — 2026-10-21

All 606 test items were screened for mismatched passages, stems and answer choices, absent required source material, and direct contradictions between a supplied source and its keyed answer. Repeated source passages were grouped for comparison; suspected defects were checked against the full original item. A quoted-referent check also identified absent source text. This is a conservative structural screen, not certification of all remaining answers or a full historical/bibliographic audit.

## Outcome

19 items are excluded from visitor sampling and available as unscored exhibits: 16 U.S., 1 European, and 2 World history items. This includes the 3 previously known U.S. mismatches and 16 additional exclusions. Eligible counts: U.S. 188/204, European 164/165, World 235/237; total 587/606.

| Subject | Canonical test rows (one-based) | Defect |
| --- | --- | --- |
| U.S. History | 18 | The third excerpt is missing |
| U.S. History | 22, 44, 130 | Hamilton questions with a freedpeople passage |
| U.S. History | 33, 71, 105, 117 | Anthony questions with a King passage |
| U.S. History | 49, 119, 171 | Industrialist questions with an Anthony passage |
| U.S. History | 97, 127 | Jackson policy questions with a Franklin passage |
| U.S. History | 176, 195 | King questions with a Jackson passage |
| U.S. History | 188 | The quoted religious-belief phrase is absent |
| European History | 153 | West in the treaty, east in the key |
| World History | 37 | Power-sharing denied in the passage, selected by the key |
| World History | 62 | “The phrase below” is not supplied |

## Evidence and exclusion decisions

### U.S. History: 18 — The third excerpt is missing

The stem asks what Representative Conyers means by “Wounded Knee” in a third excerpt. Only the Clinton and McVeigh passages are supplied; the Conyers citation has no accompanying excerpt, and “Wounded Knee” never appears in the source.

### U.S. History: 22, 44, 130 — Hamilton questions with a freedpeople passage

The supplied passage is Samuel Thomas’s 1865 testimony about freedpeople. The stem and choices concern Hamilton’s Federalist No. 15 and the Confederation period; the Federalist passage is absent.

### U.S. History: 33, 71, 105, 117 — Anthony questions with a King passage

The supplied source is Martin Luther King Jr.’s 1963 Letter from a Birmingham Jail, but this question belongs to a group about Susan B. Anthony and women’s suffrage. Rows 71, 105, and 117 explicitly ask about Anthony’s supplied words or appeal, which are absent. Row 33 is excluded with the same demonstrably mispaired source group even though its standalone factual question is answerable.

### U.S. History: 49, 119, 171 — Industrialist questions with an Anthony passage

The supplied passage is Susan B. Anthony’s 1873 speech about women’s rights. The question group concerns industrialists and Andrew Carnegie; row 119 explicitly asks about “this cartoon”, but no cartoon or textual description of it is supplied. Rows 49 and 171 are excluded with this corrupted source group even though they can be attempted as standalone factual questions.

### U.S. History: 97, 127 — Jackson policy questions with a Franklin passage

The supplied source is Benjamin Franklin’s 1766 testimony about parliamentary taxation and the Stamp Act. The stem and options instead refer to Jackson’s Native American removal policy, the Cherokee, and the Dawes Act; that policy is not described by the supplied source.

### U.S. History: 176, 195 — King questions with a Jackson passage

The supplied source is Andrew Jackson’s 1829 proposal concerning Native American removal. The stem and options instead concern Martin Luther King Jr. and twentieth-century segregation. Row 176 explicitly requires an inference “Based on this quotation”; row 195 shares the unrelated source even though its standalone factual question is answerable.

### U.S. History: 188 — The quoted religious-belief phrase is absent

The stem asks about “the sanctions of a more erroneous religious belief” in the excerpt above. Those words do not occur in the supplied South Carolina secession excerpt, which begins with the incoming Republican administration. The question’s required textual referent has been omitted.

### European History: 153 — West in the treaty, east in the key

Article III explicitly removes Russian sovereignty over territories lying “to the west” of the agreed line. Option C describes the western part of the Russian Empire; the supplied key instead selects D, the eastern part. This direction reversal is directly checkable against the supplied text. The original key is displayed for inspection, not silently corrected.

### World History: 37 — Power-sharing denied in the passage, selected by the key

The source explicitly says Peter did not return determined to share power and would personally direct or force reform. The key selects C, “Development of a constitutional monarchy”, contradicting that description. World row 163 uses the identical passage and keys his ruling style as “Absolutist”. No replacement key is assigned.

### World History: 62 — “The phrase below” is not supplied

The stem asks what “the phrase below” tells us about the ruler, but no target phrase follows it. The source discusses multiple rulers and both receiving and losing Heaven’s favor; no wording or highlighting identifies the intended phrase. The key cannot restore the missing question component.

## Scope and limits

A source can be background context rather than the sole basis of an answer. Such items were not excluded just for requiring outside knowledge. A clearly swapped source group is excluded even when one stem can be answered as standalone trivia; otherwise the visitor would still be shown the demonstrably incorrect pairing. Missing material is flagged when the question requires that material; another question sharing a partially preserved source can remain eligible if it does not require the omitted portion.

The two key contradictions are based on the actual supplied text, rather than a proposed alternative historical interpretation. No answer keys are repaired. Debatable comparisons, broad generalizations, minor typography/encoding artifacts, and suspected historical or attribution mistakes alone do not qualify for this exclusion register. Other scoring or source-attribution problems may remain.

For example, European rows 91, 98, 113, and 122 label an industrialization speech as Lenin’s and date it 1928. That attribution deserves a separate bibliographic check; it was not treated here as proof of swapped answer options. World rows 105, 189, and 214 and European rows 17, 18, 50, 51, 73, 75, and 159 merit separate historical/key review rather than unsupported claims of ingestion corruption. These remain in the visitor pool under this narrowly structural policy.

## Source fidelity and preservation

A fresh copy of the archive linked by the original MMLU project was downloaded on 2026-10-21 from https://people.eecs.berkeley.edu/~hendrycks/data.tar. `validate_mmlu.py` confirmed that all six local CSVs match it byte for byte, and all 606 test plus 15 development rows match through the loader: source/stem, four options in order, key, and stable ID. Archive SHA-256: `bec563ba4bac1d6aaf04141cd7d1605d7a5ca833e38f994051e818489592989b`. Thus the defects identified here are present in the recorded upstream dataset, not introduced by this app. The archive comparison cannot establish how those defects originated.

Canonical CSVs, evaluator prompts, and all four saved 606-item assessments remain unchanged. Their original scores retain the original denominator and keys. The filtered visitor quiz is not a replacement canonical score. The JSON issue register drives both quiz exclusions and exhibit choices; the CSV records a screening disposition for every test ID. “No confirmed structural defect” does not mean “historically validated”.
