# Kestrel Home — Model Evidence

## Validation design

A chronological 80/20 validation split was used so that validation requests occur after the training period. This better represents the future test period than a random split.

Training period: 2025-04-01 to 2026-03-30

Validation period: 2026-03-30 to 2026-06-30

## Model comparison

| Experiment | Features | Model | Accuracy |
|---|---|---|---:|
| Baseline | Word TF-IDF | LinearSVC | 94.09% |
| Experiment 2 | Word + character TF-IDF | LinearSVC | 95.66% |
| Experiment 3 | Word + character TF-IDF + structured metadata | LinearSVC | 96.49% |

## Selected model

Experiment 3 was selected because it achieved 96.49% chronological validation accuracy, exceeding the client's 90% target by 6.49 percentage points.

## Remaining errors

The validation set contained 2,165 requests. 2,089 were classified correctly and 76 were incorrect, for an error rate of 3.51%.

The largest confusion pattern was Repairs being predicted as Filters & Consumables (11 cases). Other recurring confusions involved Repairs with Billing or Warranty Claims, and multi-intent requests involving returns, installation, warranty, or consumables.

## Data leakage controls

The model uses request-time fields only: request_text, channel, product_family, warranty_status, and source. Post-routing fields such as final_team, transfers, and resolved_at were excluded from model features.
