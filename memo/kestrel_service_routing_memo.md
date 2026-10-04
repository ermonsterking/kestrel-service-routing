# Kestrel Home — Service-Request Routing Decision Memo

## Decision

The recommended routing target is the **team that ultimately resolved the request (`final_team`)**, rather than the historical vendor bot's initial routing label (`team_label`).

The original requirement was to achieve at least 90% agreement with the historical routing bot. A model achieved **96.49%** against that historical label. However, that metric primarily measures how closely the new model reproduces the existing bot rather than whether requests reach the team that ultimately resolves them.

## Why the Target Was Changed

The historical resolution data shows that the initial routing decision was not always the final operational outcome.

Across the 18-month historical dataset:

- **10,822** service requests were analyzed.
- **2,471 requests (22.83%)** ultimately moved from their initial team to a different team.
- The historical routing bot therefore agreed with the eventual resolution team on approximately **77.17%** of requests.

This indicates that optimizing only for `team_label` could reproduce the routing behavior that already resulted in transfers.

For this reason, `final_team` was selected as the operational target and evaluation yardstick.

## Model Result

The final model was evaluated using a chronological holdout period to better reflect how it would perform on future requests.

| Measure | Historical Bot | Final Model |
|---|---:|---:|
| Accuracy against `final_team` | 76.67% | **84.62%** |
| Improvement | — | **+7.95 percentage points** |

The model uses the request text together with information available when the request is created, such as channel, product family, warranty status, source, and additional request-intent signals.

The result shows that the proposed model makes substantially better routing decisions against the operational outcome than the existing historical routing process on the same evaluation period.

## Business Implication

The model provides a stronger basis for improving **first-time routing accuracy** and reducing avoidable misrouting.

Historical data also shows that transfers occurred frequently enough to be operationally important. However, the available cost figures should be treated as **illustrative rather than an audited savings calculation**. Therefore, the current result should not be presented as a guaranteed rupee saving.

## Known Limitations

The remaining errors are concentrated around requests where multiple service intents overlap—for example, requests that combine product issues with warranty, replacement, billing, or consumable-related language.

The model should therefore not be treated as a perfect automated decision-maker from the current evaluation alone.

## Recommendation

Proceed with a **controlled pilot or shadow deployment** rather than immediately retiring the existing routing process.

During the pilot, compare:

1. Model routing against actual final resolution teams.
2. Transfer rate after model routing.
3. Requests requiring manual correction.
4. Performance by channel and product family.
5. Operational impact before considering full replacement.

### Monday Handoff

The recommended next steps are:

- Deploy the model in shadow mode alongside the existing routing process.
- Capture actual routing outcomes and corrections.
- Re-evaluate performance using operational outcomes rather than historical bot agreement.
- Use the resulting transfer/error data to decide whether the model is ready for production replacement.

**Bottom line:** The key finding is not that the new model reproduces the old bot at 96.49%. The more useful finding is that, when evaluated against the team's eventual operational outcome, the new model achieves **84.62% versus 76.67% for the historical routing process**, an improvement of **7.95 percentage points**.