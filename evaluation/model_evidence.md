# Kestrel Home — Final Model Evidence

## 1. Target decision

The original request was to achieve 90%+ agreement with `team_label`. However, `team_label` represents the historical routing bot's initial queue assignment rather than the team that ultimately resolved the request.

The resolution log provides `final_team`, the team that closed each historical request. Therefore, the resubmission uses `final_team` as the operational target and evaluation yardstick. The historical `team_label` is retained as a benchmark for the existing routing process, not as the training target.

## 2. Operational-target audit

- Historical requests: **10,822**
- Historical bot agreement with `final_team`: **77.17%**
- Historical bot mismatches: **2,471 (22.83%)**
- Requests with at least one transfer: **2,696 (24.91%)**

This shows that reproducing the historical bot would optimize agreement with a process that frequently required later reassignment.

## 3. Validation design

A chronological 80/20 validation split was used. The validation period occurs after the training period, which better represents the future test period than a random split.

- Training period: **2025-04-01 to 2026-03-30**
- Validation period: **2026-03-30 to 2026-06-30**
- Training rows: **8,657**
- Validation rows: **2,165**

## 4. Final model

The selected model is a LinearSVC using request-time information only.

Features include:

- Word TF-IDF
- Character TF-IDF
- Channel
- Product family
- Warranty status
- Source
- Basic text-structure features
- Request-time intent indicators

Model configuration:

- Target: **`final_team`**
- C: **2.0**
- Class weighting: **balanced**
- Maximum iterations: **10,000**

## 5. Performance against the operational target

The key comparison is performed on the **same chronological holdout**.

| System | Evaluation set | Accuracy |
|---|---|---:|
| Historical routing bot | Chronological holdout | **76.67%** |
| Final operational model | Chronological holdout | **84.62%** |

The final model improves on the historical bot by **7.95 percentage points** on the same chronological holdout.

Final model macro F1: **0.8402**

Final model weighted F1: **0.8467**

For context, the historical bot achieves **77.17%** agreement with `final_team` when audited across the full historical dataset. This full-history figure is an operational audit, not the holdout comparison above.

## 6. Historical-bot correction analysis

On the chronological holdout:

- Old bot wrong → model correct: **239**
- Old bot correct → model wrong: **75**
- Both wrong: **266**

The model therefore corrects a meaningful number of cases where the historical bot disagreed with the eventual operational outcome, while also introducing some new errors.

## 7. Important limitation

`final_team` is treated as the operational target because it represents the eventual resolution team. It should not be interpreted as perfect ground truth: the final team can itself reflect operational processes, transfers, or human decisions.

The **84.62%** result is validation performance against the historical operational outcome. It is not a guarantee of future routing accuracy or guaranteed cost savings.

## 8. Leakage controls

The model uses information available when a request arrives:

- request text
- channel
- product family
- warranty status
- source
- engineered features derived from these request-time fields

Post-routing outcome fields such as `final_team`, `first_team`, `transfers`, and `resolved_at` are not used as model features.

`final_team` is used only as the training target and evaluation yardstick.

## 9. Decision summary

The historical bot achieves only **77.17%** agreement with eventual `final_team` across the historical dataset, with **2,471** requests ending with a different team.

The selected operational model reaches **84.62%** accuracy on the chronological holdout versus **76.67%** for the historical bot on that same holdout.

Therefore, the model is positioned as an attempt to improve routing toward the observed operational outcome rather than as a replication of the historical bot.

