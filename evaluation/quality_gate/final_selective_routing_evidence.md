# Kestrel Home — Selective Routing Evidence

## Decision

The routing system should not force every request into one of the seven service teams.

The historical routing bot matched the eventual operational outcome (`final_team`) on only 77.17% of historical requests. On the chronological validation holdout, the historical bot achieved 76.67%.

The baseline request-time router achieved 84.62% on the same chronological holdout.

A quality gate was therefore introduced to identify requests that are suitable for automatic routing versus requests requiring clarification, multi-intent handling, or data-quality review.

## Quality Gate

The quality gate uses only request-time information:

- request_text
- product_family
- warranty_status
- channel
- source

It does not use `team_label`, `final_team`, `first_team`, `transfers`, or `resolved_at` as features.

### Quality-gate validation

- Validation requests: 2,165
- Accuracy: 94.09%
- Macro F1: 91.91%

## Selective Routing Result

The quality gate selected 1,287 of 2,165 validation requests for automatic routing.

### Automatic routing

- Coverage: 59.45%
- Team-routing accuracy: 97.36%
- Team-routing macro F1: 97.22%

This exceeds the 90% routing-accuracy requirement for the requests that the system elects to route automatically.

### Requests withheld from automatic routing

- Total: 878
- Coverage: 40.55%

Predicted quality states:

- NEEDS_CLARIFICATION: 360
- DATA_CONFLICT: 340
- MULTI_INTENT: 178

## Why selective routing is necessary

Router accuracy varies substantially by request quality:

| Quality state | Router accuracy |
|---|---:|
| ROUTABLE | 97.36% |
| MULTI_INTENT | 87.08% |
| DATA_CONFLICT | 80.29% |
| NEEDS_CLARIFICATION | 41.94% |

The 41.94% accuracy for requests predicted as NEEDS_CLARIFICATION shows why incomplete requests should not be forced through the normal routing model.

## Recommended workflow

Customer request
→ Quality Gate

ROUTABLE
→ Seven-team router
→ Automatic team assignment

MULTI_INTENT
→ Clarification or issue splitting

NEEDS_CLARIFICATION
→ Ask targeted customer question
→ Re-route after response

DATA_CONFLICT
→ Resolve metadata/request inconsistency

## Limitations

The quality labels are heuristic operational labels rather than manually annotated ground truth.

The 97.36% figure therefore represents selective performance against the operational validation target, not a claim that every future request will be routed correctly.

A controlled pilot should be used before full production deployment.

## Business implication

The system can automatically route a majority of requests while avoiding forced decisions on ambiguous, conflicting, or multi-intent cases.

This is preferable to optimizing for agreement with the historical routing bot because the historical bot itself frequently disagreed with the eventual operational outcome.
