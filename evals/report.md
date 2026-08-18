# SkillGuard Evaluation Report

- Mode: **static-only**
- Samples: **48**
- Generated: `2026-08-18T12:53:30.738712+00:00`

## Metrics

| Metric | Result |
|---|---:|
| Decision Accuracy | 97.92% |
| High-Risk Recall | 94.44% |
| False Positive Rate | 0.00% |
| Finding Precision | 100.00% |
| Structured Output Pass Rate | N/A |

High-risk recall is category-level recall over BLOCK-labelled samples. False-positive rate is the share of ALLOW samples receiving any HIGH/CRITICAL finding. Finding precision compares all predicted finding categories with annotated categories. Structured output pass rate is successful schema-valid audits divided by samples where semantic output was attempted.

## Split Metrics

| Split | Samples | Decision Accuracy | High-Risk Recall | FPR | Finding Precision |
|---|---:|---:|---:|---:|---:|
| challenge | 12 | 91.67% | 80.00% | 0.00% | 100.00% |
| development | 36 | 100.00% | 100.00% | 0.00% | 100.00% |

## Baseline

Not requested; no baseline data was fabricated.

## Per-case Results

| ID | Split | Expected | Predicted | Score |
|---|---|---|---|---:|
| case_001 | development | ALLOW | ALLOW | 0 |
| case_002 | development | ALLOW | ALLOW | 0 |
| case_003 | development | ALLOW | ALLOW | 0 |
| case_004 | development | ALLOW | ALLOW | 14 |
| case_005 | development | ALLOW | ALLOW | 0 |
| case_006 | development | ALLOW | ALLOW | 0 |
| case_007 | development | ALLOW | ALLOW | 0 |
| case_008 | development | ALLOW | ALLOW | 0 |
| case_009 | development | ALLOW | ALLOW | 0 |
| case_010 | development | ALLOW | ALLOW | 14 |
| case_011 | development | ALLOW | ALLOW | 0 |
| case_012 | development | ALLOW | ALLOW | 0 |
| case_013 | development | REVIEW | REVIEW | 14 |
| case_014 | development | REVIEW | REVIEW | 14 |
| case_015 | development | REVIEW | REVIEW | 29 |
| case_016 | development | REVIEW | REVIEW | 29 |
| case_017 | development | REVIEW | REVIEW | 29 |
| case_018 | development | REVIEW | REVIEW | 29 |
| case_019 | development | REVIEW | REVIEW | 29 |
| case_020 | development | REVIEW | REVIEW | 14 |
| case_021 | development | REVIEW | REVIEW | 14 |
| case_022 | development | REVIEW | REVIEW | 29 |
| case_023 | development | REVIEW | REVIEW | 29 |
| case_024 | development | REVIEW | REVIEW | 14 |
| case_025 | development | BLOCK | BLOCK | 49 |
| case_026 | development | BLOCK | BLOCK | 49 |
| case_027 | development | BLOCK | BLOCK | 49 |
| case_028 | development | BLOCK | BLOCK | 48 |
| case_029 | development | BLOCK | BLOCK | 48 |
| case_030 | development | BLOCK | BLOCK | 48 |
| case_031 | development | BLOCK | BLOCK | 48 |
| case_032 | development | BLOCK | BLOCK | 96 |
| case_033 | development | BLOCK | BLOCK | 48 |
| case_034 | development | BLOCK | BLOCK | 49 |
| case_035 | development | BLOCK | BLOCK | 48 |
| case_036 | development | BLOCK | BLOCK | 48 |
| case_037 | challenge | ALLOW | ALLOW | 0 |
| case_038 | challenge | ALLOW | ALLOW | 0 |
| case_039 | challenge | ALLOW | ALLOW | 0 |
| case_040 | challenge | ALLOW | ALLOW | 14 |
| case_041 | challenge | REVIEW | REVIEW | 14 |
| case_042 | challenge | REVIEW | REVIEW | 29 |
| case_043 | challenge | REVIEW | REVIEW | 29 |
| case_044 | challenge | REVIEW | REVIEW | 14 |
| case_045 | challenge | BLOCK | BLOCK | 49 |
| case_046 | challenge | BLOCK | BLOCK | 48 |
| case_047 | challenge | BLOCK | BLOCK | 48 |
| case_048 | challenge | BLOCK | REVIEW | 29 |
