Loading older messages…
(.venv) monsterking@Monsterdevice:~/Desktop/kestrel-service-routing$ pytest -q
.....                                             [100%]
=================== warnings summary ====================
.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /home/monsterking/Desktop/kestrel-service-routing/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
5 passed, 1 warning in 2.74s
(.venv) monsterking@Monsterdevice:~/Desktop/kestrel-service-routing$ git diff --check
(.venv) monsterking@Monsterdevice:~/Desktop/kestrel-service-routing$ git status
On branch improve-90pct-routing
Your branch is up to date with 'origin/improve-90pct-routing'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   app/main.py
        modified:   app/ui.py
        modified:   evaluation/model_evidence.md
        modified:   src/create_evidence.py

no changes added to commit (use "git add" and/or "git commit -a")
(.venv) monsterking@Monsterdevice:~/Desktop/kestrel-service-routing$
…

Perfect. We are now in a clean, tested state:

    ✅ pytest: 5 passed
    ✅ git diff --check: no issues
    ✅ API + quality gate tested
    ✅ Streamlit UI tested
    ✅ evidence regenerated
    ✅ only 4 intended files modified

The FastAPI/Starlette warning is a dependency deprecation warning, not a test failure.

Before the final commit, let's do the README + memo alignment, because this is what the evaluator will actually read.
1. First inspect the current README and memo

Run:

sed -n '1,320p' README.md

Then:

sed -n '1,260p' memo/kestrel_service_routing_memo.md

Paste both outputs here.

I'll update them around the final story:

    Historical bot: 76.67%
    All-request router: 84.62%
    Quality gate: 94.09%
    Selective automatic routing: 59.45% coverage at 97.36% accuracy
    Remaining 40.55%: clarification, multi-intent, or data-conflict handling.

And importantly, we'll make it explicit that 97.36% is selective routing accuracy, not overall system accuracy.

After that we'll do the final git diff, commit, push, and prepare your submission-form answers + 3-minute demo script.
Pasted markdown(10).mdDocument
make a update the whole information with the architecture

Done. I updated the README based on your current documentation and incorporated the complete final architecture:

    Quality Gate → 4 states
    ROUTABLE → 7-team router
    NEEDS_CLARIFICATION → targeted question
    MULTI_INTENT → prioritize/split
    DATA_CONFLICT → metadata review
    Offline training/evaluation architecture
    Online FastAPI inference architecture
    Streamlit UI flow
    84.62% all-request router performance
    97.36% selective-routing accuracy at 59.45% coverage
    94.09% quality-gate accuracy
    API response structure
    Updated end-to-end workflow
    Updated final decision and limitations

The existing README's target decision and operational audit are preserved: final_team is the operational target, while team_label is treated as the historical bot benchmark.
Updated README
Final architecture in one view
                    CUSTOMER REQUEST
                           │
                           ▼
              ┌──────────────────────┐
              │     QUALITY GATE     │
              └──────────┬───────────┘
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
   ROUTABLE       NEEDS_CLARIFICATION   MULTI_INTENT
       │                 │                  │
       ▼                 ▼                  ▼
  7-TEAM ROUTER     Ask Question       Prioritize /
       │                                Split Issue
       ▼
  SERVICE TEAM

                    DATA_CONFLICT
                          │
                          ▼
                  Metadata Review

The key story for the evaluator is now very clear: we are not claiming that the entire system is 97.36% accurate. We are claiming that the quality gate enables 97.36% accuracy on the 59.45% of requests it considers safe to auto-route, while the remaining requests are deliberately handled through clarification or review.
README_updated.mdDocument

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
…

Yes. With the quality-gated selective routing architecture, this memo should be updated because the current version stops at the 84.62% all-request model and does not reflect the stronger final result.

Here is the revised version:
Kestrel Home — Service-Request Routing Decision Memo
Decision

The recommended routing target is the team that ultimately resolved the request (final_team), rather than the historical vendor bot's initial routing label (team_label).

The original requirement was to achieve at least 90% agreement with the historical routing bot. A model achieved 96.49% against that historical label. However, that metric primarily measures how closely the new model reproduces the existing bot rather than whether requests reach the team that ultimately resolves them.

The final solution therefore uses a two-stage selective-routing architecture:

    Quality Gate — determines whether a request is suitable for automatic routing.
    Seven-team Router — predicts the operational team only for requests that pass the quality gate.

Requests that are ambiguous, contain multiple intents, or have conflicting metadata are deliberately withheld rather than being forced into an automatic routing decision.
Why the Target Was Changed

The historical resolution data shows that the initial routing decision was not always the final operational outcome.

Across the 18-month historical dataset:

    10,822 service requests were analyzed.
    2,471 requests (22.83%) ultimately moved from their initial team to a different team.
    The historical routing bot agreed with the eventual resolution team on approximately 77.17% of requests.

This indicates that optimizing only for team_label could reproduce the routing behavior that already resulted in transfers.

For this reason, final_team was selected as the operational target and evaluation yardstick.
Model and Quality-Gate Results

The seven-team router was evaluated using a chronological holdout period to better reflect future requests.
Measure	Historical Bot	Final Router
Accuracy against final_team	76.67%	84.62%
Improvement	—	+7.95 pp

The router uses information available when the request is created, including:

    Request text
    Channel
    Product family
    Warranty status
    Source
    Request-intent features

To avoid forcing uncertain cases through the router, a separate quality gate was introduced.
Quality Gate

The quality gate classifies requests into four operational states:
Quality State	Action
ROUTABLE	Allow automatic team prediction
NEEDS_CLARIFICATION	Ask the customer for additional information
DATA_CONFLICT	Flag inconsistent request/metadata information
MULTI_INTENT	Ask which issue should be handled first

The quality gate achieved:

    94.09% accuracy
    91.91% macro F1

On the chronological validation set:

    59.45% of requests were selected for automatic routing.
    Those automatically routed requests achieved 97.36% routing accuracy.
    Routing macro F1 was 97.22%.
    40.55% of requests were deliberately withheld from automatic routing.

The withheld requests consisted of:

    360 predicted NEEDS_CLARIFICATION
    340 predicted DATA_CONFLICT
    178 predicted MULTI_INTENT

Importantly, 97.36% is the accuracy of the automatically routed subset, not the accuracy of all requests. The system trades coverage for higher-confidence automatic routing.
Final Architecture
Customer Service Request
          │
          ▼
┌─────────────────────────────┐
│ Request-Time Inputs         │
│ • Request text              │
│ • Product family            │
│ • Warranty status           │
│ • Channel                   │
│ • Source                    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Quality Gate                │
│                             │
│ ROUTABLE                    │
│ NEEDS_CLARIFICATION         │
│ DATA_CONFLICT               │
│ MULTI_INTENT                │
└───────┬───────────┬─────────┘
        │           │
   ROUTABLE     Non-routable
        │           │
        ▼           ▼
┌──────────────┐  ┌─────────────────────┐
│ Seven-Team   │  │ Clarification /     │
│ Router       │  │ Data-Quality        │
│              │  │ Handling            │
└──────┬───────┘  └─────────────────────┘
       │
       ▼
Predicted Service Team

This architecture is preferable to simply forcing every request into one of the seven teams because it explicitly recognizes that not every customer request contains enough reliable information for immediate routing.
Business Implication

The system provides a stronger basis for improving first-time routing accuracy and reducing avoidable misrouting.

The all-request router improves historical-bot performance from 76.67% to 84.62%, while the quality gate enables 97.36% accuracy for the subset selected for automatic routing.

This creates a practical operating model:

    Route high-confidence requests automatically and send uncertain requests to clarification or data-quality handling.

Historical transfer and misrouting costs indicate that routing errors can have meaningful operational impact. However, the available cost figures should be treated as illustrative rather than an audited savings calculation. Therefore, the current result should not be presented as a guaranteed rupee saving.
Known Limitations

The current system has several limitations:

    The final_team label represents the eventual operational outcome, but it should not be treated as perfect ground truth.
    Quality-gate labels are heuristic operational labels, rather than manually annotated human labels.
    The router still has errors around overlapping intents such as warranty, replacement, billing, repairs, and consumables.
    The selective system currently routes only 59.45% of validation requests automatically.
    The remaining requests require clarification, data-quality handling, or multi-intent resolution.
    Production performance should be validated on newly generated operational data before replacing the existing process.

Recommendation

Proceed with a controlled pilot or shadow deployment rather than immediately retiring the existing routing process.

During the pilot, compare:

    Model routing against actual final resolution teams.
    Automatic-routing coverage.
    Transfer rate after model routing.
    Requests requiring manual correction.
    Clarification and data-conflict rates.
    Performance by channel and product family.
    Operational impact before considering full replacement.

Monday Handoff

The recommended next steps are:

    Deploy the system in shadow mode alongside the existing routing process.
    Capture actual routing outcomes and manual corrections.
    Track the quality-gate states and automatic-routing coverage.
    Re-evaluate performance using operational outcomes rather than historical bot agreement.
    Collect manually reviewed examples for ambiguous and multi-intent requests.
    Improve the quality gate using real production feedback.
    Use the resulting transfer/error data to decide whether the model is ready for production replacement.

Bottom Line

The key finding is not that the new model reproduces the old bot at 96.49%.

The more useful finding is that the historical bot agreed with the eventual resolution team on only 76.67% of requests in the chronological evaluation period, while the new seven-team router achieved 84.62%, an improvement of 7.95 percentage points.

More importantly, adding a quality gate allows the system to avoid forcing uncertain requests into an automatic decision. On the validation set, 59.45% of requests were automatically routed at 97.36% accuracy, while the remaining 40.55% were deliberately withheld for clarification, data conflict, or multi-intent handling.

Recommended decision: proceed with a controlled pilot of the quality-gated selective routing system, rather than immediately replacing the existing routing process.
make the updated file in the same format

Done. I kept the same Markdown format and structure as your original memo and updated it with the final quality-gated selective-routing architecture and results.
Kestrel_Service_Routing_Decision_Memo_Updated.mdDocument
Kestrel Home — Service-Request Routing Decision Memo
Decision

The recommended routing target is the team that ultimately resolved the request (final_team), rather than the historical vendor bot's initial routing label (team_label).

The original requirement was to achieve at least 90% agreement with the historical routing bot. A model achieved 96.49% against that historical label. However, that metric primarily measures how closely the new model reproduces the existing bot rather than whether requests reach the team that ultimately resolves them.

The final solution therefore uses a two-stage selective-routing architecture:

    Quality Gate — determines whether a request is suitable for automatic routing.
    Seven-team Router — predicts the operational team only for requests that pass the quality gate.

Requests that are ambiguous, contain multiple intents, or have conflicting metadata are deliberately withheld rather than being forced into an automatic routing decision.
Why the Target Was Changed

The historical resolution data shows that the initial routing decision was not always the final operational outcome.

Across the 18-month historical dataset:

    10,822 service requests were analyzed.
    2,471 requests (22.83%) ultimately moved from their initial team to a different team.
    The historical routing bot agreed with the eventual resolution team on approximately 77.17% of requests.

This indicates that optimizing only for team_label could reproduce the routing behavior that already resulted in transfers.

For this reason, final_team was selected as the operational target and evaluation yardstick.
Model and Quality-Gate Results

The seven-team router was evaluated using a chronological holdout period to better reflect future requests.
Measure	Historical Bot	Final Router
Accuracy against final_team	76.67%	84.62%
Improvement	—	+7.95 percentage points

The router uses information available when the request is created, including:

    Request text
    Channel
    Product family
    Warranty status
    Source
    Request-intent features

To avoid forcing uncertain cases through the router, a separate quality gate was introduced.
Quality Gate

The quality gate classifies requests into four operational states:
Quality State	Action
ROUTABLE	Allow automatic team prediction
NEEDS_CLARIFICATION	Ask the customer for additional information
DATA_CONFLICT	Flag inconsistent request/metadata information
MULTI_INTENT	Ask which issue should be handled first

The quality gate achieved:

    94.09% accuracy
    91.91% macro F1

On the chronological validation set:

    59.45% of requests were selected for automatic routing.
    Those automatically routed requests achieved 97.36% routing accuracy.
    Routing macro F1 was 97.22%.
    40.55% of requests were deliberately withheld from automatic routing.

The withheld requests consisted of:

    360 predicted NEEDS_CLARIFICATION
    340 predicted DATA_CONFLICT
    178 predicted MULTI_INTENT

Importantly, 97.36% is the accuracy of the automatically routed subset, not the accuracy of all requests. The system trades coverage for higher-confidence automatic routing.
Final Architecture
Customer Service Request
          │
          ▼
┌─────────────────────────────┐
│ Request-Time Inputs         │
│ • Request text              │
│ • Product family            │
│ • Warranty status           │
│ • Channel                   │
│ • Source                    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Quality Gate                │
│                             │
│ ROUTABLE                    │
│ NEEDS_CLARIFICATION         │
│ DATA_CONFLICT               │
│ MULTI_INTENT                │
└───────┬───────────┬─────────┘
        │           │
   ROUTABLE     Non-routable
        │           │
        ▼           ▼
┌──────────────┐  ┌─────────────────────┐
│ Seven-Team   │  │ Clarification /     │
│ Router       │  │ Data-Quality        │
│              │  │ Handling            │
└──────┬───────┘  └─────────────────────┘
       │
       ▼
Predicted Service Team
Business Implication

The system provides a stronger basis for improving first-time routing accuracy and reducing avoidable misrouting.

The all-request router improves historical-bot performance from 76.67% to 84.62%, while the quality gate enables 97.36% accuracy for the subset selected for automatic routing.

This creates a practical operating model:

    Route high-confidence requests automatically and send uncertain requests to clarification or data-quality handling.

Historical transfer and misrouting costs indicate that routing errors can have meaningful operational impact. However, the available cost figures should be treated as illustrative rather than an audited savings calculation. Therefore, the current result should not be presented as a guaranteed rupee saving.
Known Limitations

The current system has several limitations:

    The final_team label represents the eventual operational outcome, but it should not be treated as perfect ground truth.
    Quality-gate labels are heuristic operational labels, rather than manually annotated human labels.
    The router still has errors around overlapping intents such as warranty, replacement, billing, repairs, and consumables.
    The selective system currently routes only 59.45% of validation requests automatically.
    The remaining requests require clarification, data-quality handling, or multi-intent resolution.
    Production performance should be validated on newly generated operational data before replacing the existing process.

Recommendation

Proceed with a controlled pilot or shadow deployment rather than immediately retiring the existing routing process.

During the pilot, compare:

    Model routing against actual final resolution teams.
    Automatic-routing coverage.
    Transfer rate after model routing.
    Requests requiring manual correction.
    Clarification and data-conflict rates.
    Performance by channel and product family.
    Operational impact before considering full replacement.

Monday Handoff

The recommended next steps are:

    Deploy the system in shadow mode alongside the existing routing process.
    Capture actual routing outcomes and manual corrections.
    Track the quality-gate states and automatic-routing coverage.
    Re-evaluate performance using operational outcomes rather than historical bot agreement.
    Collect manually reviewed examples for ambiguous and multi-intent requests.
    Improve the quality gate using real production feedback.
    Use the resulting transfer/error data to decide whether the model is ready for production replacement.

Bottom line: The key finding is not that the new model reproduces the old bot at 96.49%.

The more useful finding is that the historical bot agreed with the eventual resolution team on only 76.67% of requests in the chronological evaluation period, while the new seven-team router achieved 84.62%, an improvement of 7.95 percentage points.

More importantly, adding a quality gate allows the system to avoid forcing uncertain requests into an automatic decision. On the validation set, 59.45% of requests were automatically routed at 97.36% accuracy, while the remaining 40.55% were deliberately withheld for clarification, data conflict, or multi-intent handling.

Recommended decision: proceed with a controlled pilot of the quality-gated selective routing system, rather than immediately replacing the existing routing process.


