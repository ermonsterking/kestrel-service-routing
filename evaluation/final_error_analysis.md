# Kestrel Home — Final Model Error Analysis

## 1. Validation Result

The final operational model was evaluated on a chronological holdout using
`final_team` as the operational target.

- Validation rows: **2,165**
- Correct predictions: **1,832**
- Incorrect predictions: **333**
- Accuracy: **84.62%**
- Error rate: **15.38%**

The historical routing bot was evaluated on the same validation rows.

- Historical bot correct: **1,660**
- Historical bot incorrect: **505**
- Historical bot accuracy: **76.67%**

## 2. Classification Performance

```text
                       precision    recall  f1-score   support

              Billing     0.8248    0.8726    0.8480       259
Filters & Consumables     0.7885    0.8524    0.8192       210
      Installs & Demo     0.8671    0.8405    0.8536       326
       Product Advice     0.7979    0.8242    0.8108       273
              Repairs     0.9200    0.8688    0.8937       503
Returns & Replacement     0.8495    0.8187    0.8338       331
      Warranty Claims     0.8088    0.8365    0.8224       263

             accuracy                         0.8462      2165
            macro avg     0.8367    0.8448    0.8402      2165
         weighted avg     0.8482    0.8462    0.8467      2165

```

## 3. Confusion Matrix

The complete confusion matrix is available in:

`evaluation/final_model_confusion_matrix.csv`

Detailed confusion-pair analysis is available in:

`evaluation/final_model_confusion_pairs.csv`

## 4. Error Breakdown

Error breakdowns are available in:

- `evaluation/final_model_errors_by_channel.csv`
- `evaluation/final_model_errors_by_product.csv`
- `evaluation/final_model_errors_by_warranty.csv`

## 5. Historical Bot vs Final Model

On the same chronological validation set:

- Old bot wrong → model correct: **243**
- Old bot correct → model wrong: **71**
- Both wrong: **262**
- Both correct: **1,589**

The key business comparison is therefore between the historical bot's
agreement with `final_team` and the new model's agreement with `final_team`.

## 6. Representative Hard Cases

Representative difficult validation cases are saved in:

`evaluation/representative_hard_cases.csv`

These cases prioritize model errors involving transfers and short or vague
request text.

## 7. Leakage Controls

The model uses only information available at request creation time:

- request text
- channel
- product family
- warranty status
- source
- request-text-derived features

The following post-routing fields were not used as model features:

- `final_team`
- `first_team`
- `transfers`
- `resolved_at`

The historical `team_label` is treated as the historical bot decision and
benchmark, not as the operational target.

## 8. Generated Evidence Files

The analysis generated:

- `final_model_confusion_matrix.csv`
- `final_model_confusion_pairs.csv`
- `final_model_errors_by_channel.csv`
- `final_model_errors_by_product.csv`
- `final_model_errors_by_warranty.csv`
- `bot_vs_model_cases.csv`
- `final_model_validation_predictions.csv`
- `representative_hard_cases.csv`
- `final_error_analysis.md`