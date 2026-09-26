Absolutely. Below is the **complete consolidated `README.md`**. You can **replace your current README.md entirely** with this content.

````markdown
# Kestrel Home — Service Request Routing

> An end-to-end machine learning system for automatically routing Kestrel Home customer service requests to the appropriate service team.

---

## Introduction

Kestrel Home Appliances receives customer service requests across multiple channels, including chat, WhatsApp, IVR, and email.

Each request needs to be routed to one of seven service teams:

- Billing
- Filters & Consumables
- Installs & Demo
- Product Advice
- Repairs
- Returns & Replacement
- Warranty Claims

The existing routing process uses a vendor routing bot. The objective of this project is to build a reproducible machine learning system that learns from historical routing decisions and predicts the appropriate service team for new customer requests.

The solution uses a lightweight local NLP classification pipeline instead of a paid LLM or external AI API. This makes the system reproducible, inexpensive to run, and suitable for deployment as an internal service.

The complete workflow is:

```text
Historical Data
      ↓
Data Understanding & EDA
      ↓
Data Cleaning & Team Normalization
      ↓
Chronological Validation
      ↓
NLP Feature Engineering
      ↓
Model Experiments
      ↓
Error Analysis
      ↓
Final Model
      ↓
Prediction Generation
      ↓
FastAPI Service
      ↓
Streamlit UI
      ↓
Automated Testing
````

---

# Objective

The primary objective is to build a machine learning classifier that reproduces the historical routing decision (`team_label`) with at least **90% validation accuracy**.

The system is designed to:

1. Predict the appropriate service team for a new customer request.
2. Use only information available when the request is created.
3. Avoid data leakage from post-routing information.
4. Handle both customer text and structured request metadata.
5. Provide a reproducible prediction pipeline.
6. Expose the model through a JSON API.
7. Provide a simple interface for testing the routing system.
8. Generate predictions for the supplied unlabelled test dataset.
9. Provide evidence of model performance and failure modes.
10. Document operational and deployment considerations.

### Target

The client's stated target is:

> **90%+ accuracy against the historical routing labels.**

The final model achieved **96.49% chronological validation accuracy**.

---

# Tools & Technologies

## Programming Language

* Python 3.12+

## Machine Learning

* scikit-learn
* LinearSVC
* TF-IDF
* OneHotEncoder

## Data Processing

* pandas
* NumPy

## Model Persistence

* joblib

## Backend

* FastAPI
* Uvicorn
* Pydantic

## Frontend / Demo

* Streamlit

## Testing

* pytest
* FastAPI TestClient
* HTTPX

## Development

* VS Code
* Python virtual environment
* Ubuntu/Linux

---

# Libraries Used

| Library        | Purpose                                               |
| -------------- | ----------------------------------------------------- |
| `pandas`       | Data loading, transformation and analysis             |
| `numpy`        | Numerical operations                                  |
| `scikit-learn` | Feature engineering, preprocessing and classification |
| `scipy`        | Scientific computing dependency                       |
| `joblib`       | Model serialization and loading                       |
| `fastapi`      | REST API implementation                               |
| `uvicorn`      | ASGI server for the API                               |
| `streamlit`    | Interactive demonstration UI                          |
| `pydantic`     | API input validation                                  |
| `requests`     | UI-to-API HTTP communication                          |
| `pytest`       | Automated testing                                     |
| `httpx`        | API test client support                               |

---

# Dataset

The project uses approximately 18 months of labelled historical service requests.

## Training Dataset

The labelled training dataset contains:

**10,822 requests**

Schema:

```text
request_id
created_at_ist
channel
product_family
warranty_status
request_text
source
team_label
```

## Test Dataset

The unlabelled test dataset contains:

**2,178 requests**

It contains the same request-time fields as the training data except for `team_label`.

## Resolution Data

A separate resolution log contains:

```text
request_id
first_team
final_team
transfers
resolved_at
```

This data is used for operational analysis and error investigation.

Post-routing information from the resolution log is deliberately excluded from the model's feature set.

## Data Period

Training data:

```text
2025-04-01 → 2026-06-30
```

Test data:

```text
2026-07-01 → 2026-09-30
```

## Data Sources

Requests originate from:

* CRM
* Legacy Zoho system

The system migration occurred during the historical period, so `source` is also included as a request-time feature.

---

# Service Teams

The current routing system contains seven service teams:

| Team                  | Primary responsibility                                                               |
| --------------------- | ------------------------------------------------------------------------------------ |
| Billing               | Invoices, GST, payment issues, refunds, EMI and coupons                              |
| Filters & Consumables | Filters, candles, membranes, jars, brushes, blades, AMC kits and spares              |
| Installs & Demo       | Product installation, demonstrations and wall mounting                               |
| Product Advice        | Product usage and pre/post-purchase questions without a fault                        |
| Repairs               | Product faults, breakdowns, error codes, leaks, noise and technician-required issues |
| Returns & Replacement | Damaged, wrong or incomplete deliveries, returns and exchanges                       |
| Warranty Claims       | Warranty registration, coverage and warranty claim requests                          |

## Historical Team Name Normalization

Two historical team names were renamed during the data period:

```text
Installations
      ↓
Installs & Demo

Consumables
      ↓
Filters & Consumables
```

These historical labels were normalized before training and evaluation so that the final classifier predicts the current seven-team structure.

---

# Data Understanding & EDA

Initial analysis was performed before model development to understand:

* Dataset size and schema
* Missing values
* Duplicate records
* Class distribution
* Channel distribution
* Product distribution
* Warranty distribution
* Historical data sources
* Request-text characteristics
* Transfer patterns
* First-team versus final-team routing
* Legacy data quality issues

## Dataset Summary

| Dataset        |   Rows |
| -------------- | -----: |
| Training       | 10,822 |
| Test           |  2,178 |
| Resolution Log | 10,822 |
| Service Teams  |      7 |

No missing values or duplicate rows were found in the main training, test, and resolution datasets.

## Historical Routing Analysis

The resolution data contained:

* **3,902 total transfers**
* **2,696 requests with at least one transfer**
* **2,471 first-team/final-team mismatches** after normalizing historical team names

These metrics were used for operational analysis only and were not used as model features.

## Data Quality Observation

Some older legacy Zoho requests contain text encoding artifacts. These were retained rather than manually rewriting customer messages so that the model evaluation remains representative of the supplied historical data.

---

# Modeling Approach

The routing problem is treated as a **multi-class text classification problem**.

The target variable is:

```text
team_label
```

which represents the service queue assigned to the customer request by the historical routing system.

The final classifier predicts one of the seven normalized service teams.

---

# Feature Engineering

The final model uses two types of features:

1. Customer request text features
2. Structured request metadata

## 1. Word-Level TF-IDF

The `request_text` field is converted into TF-IDF features using:

```text
ngram_range = (1, 2)
min_df = 2
sublinear_tf = True
```

This captures:

* Individual words
* Two-word phrases
* Important routing terminology
* Domain-specific expressions

For example:

```text
"water purifier leaking"
```

can produce features such as:

```text
water
purifier
leaking
water purifier
purifier leaking
```

TF-IDF gives higher importance to terms that are informative for a particular request while reducing the influence of very common terms.

---

# 2. Character-Level TF-IDF

Character-level TF-IDF features are also extracted from `request_text`.

Configuration:

```text
analyzer = char_wb
ngram_range = (3, 5)
min_df = 2
sublinear_tf = True
```

Character features are useful for customer-service text because requests may contain:

* Spelling variations
* Abbreviations
* Informal language
* Typographical errors
* Partial words
* Product-specific terminology
* Legacy encoding artifacts

---

# 3. Structured Metadata

The model also uses request metadata that would be available when the customer request is created.

The categorical fields are:

```text
channel
product_family
warranty_status
source
```

These features are encoded using:

```python
OneHotEncoder(handle_unknown="ignore")
```

### Why metadata is useful

Two requests with similar wording may require different routing depending on their context.

For example:

* Product family can distinguish appliance-specific requests.
* Warranty status can provide useful context for warranty-related requests.
* Channel can capture differences in request language across chat, IVR, email and WhatsApp.
* Source identifies whether the request originated from CRM or the legacy system.

---

# Model Architecture

The final feature pipeline combines all feature groups using a `ColumnTransformer`.

```text
                         Request
                            │
              ┌─────────────┴─────────────┐
              │                           │
        Request Text                Structured Data
              │                           │
       ┌──────┴──────┐          ┌─────────┴─────────┐
       │             │          │         │         │
      Word          Char      Channel  Product   Warranty
     TF-IDF        TF-IDF              Family    Status
       │             │          │         │         │
       └──────┬──────┘          └─────────┬─────────┘
              │                           │
              └─────────────┬─────────────┘
                            │
                     Combined Features
                            │
                            ▼
                       LinearSVC
                            │
                            ▼
                    Service Team Label
```

---

# Classifier

The final classifier is:

```python
LinearSVC(
    C=1.0,
    class_weight="balanced"
)
```

### Why LinearSVC?

LinearSVC is suitable for this problem because:

* TF-IDF produces a high-dimensional sparse feature matrix.
* Linear models work efficiently with sparse text features.
* Training and inference are fast.
* The model is lightweight enough for a local service.
* It does not require a GPU.
* It does not require an external API.
* Its behavior is reproducible.

`class_weight="balanced"` is used to account for differences in class frequency across the seven service teams.

---

# Model Experiments

Three model configurations were evaluated.

## Experiment 1 — Baseline

```text
Word TF-IDF
     ↓
LinearSVC
```

Features:

* Word unigrams
* Word bigrams

Validation accuracy:

**94.09%**

---

## Experiment 2 — Character Features

```text
Word TF-IDF
      +
Character TF-IDF
      ↓
LinearSVC
```

Validation accuracy:

**95.66%**

Adding character-level features improved validation accuracy by:

**1.57 percentage points**

compared with the baseline.

---

## Experiment 3 — Structured Metadata

The final experiment added request metadata:

```text
Word TF-IDF
      +
Character TF-IDF
      +
Channel
      +
Product Family
      +
Warranty Status
      +
Source
      ↓
LinearSVC
```

Validation accuracy:

**96.49%**

This improved performance by:

**2.40 percentage points**

compared with the baseline.

The final model uses this configuration.

---

# Final Feature Set

The final model uses:

```text
request_text
channel
product_family
warranty_status
source
```

The following fields are intentionally excluded:

```text
final_team
transfers
resolved_at
```

These fields contain information that becomes available after the original routing decision and therefore would not be available when making a new routing prediction.

---

# Validation Strategy

Because the supplied test data represents a future time period, the project uses a **chronological validation split** rather than a random train/test split.

The complete labelled dataset was sorted by `created_at_ist`.

The earliest 80% of requests were used for training and the latest 20% were used for validation.

## Split

| Dataset    | Requests | Period                  |
| ---------- | -------: | ----------------------- |
| Training   |    8,657 | 2025-04-01 → 2026-03-30 |
| Validation |    2,165 | 2026-03-30 → 2026-06-30 |

This approach better approximates the real deployment scenario because the model is evaluated on requests that occur later in time than the requests used for training.

### Why not random split?

A random split could place very similar requests from the same historical period into both training and validation.

That can produce an overly optimistic estimate of how the model will perform on future requests.

A chronological split provides a more realistic estimate of temporal generalization.

---

# Results

The final model achieved **96.49% accuracy** on the chronological validation set.

This exceeds the client's target of **90% accuracy** by **6.49 percentage points**.

## Validation Performance

| Metric                |       Result |
| --------------------- | -----------: |
| Validation requests   |        2,165 |
| Correct predictions   |        2,089 |
| Incorrect predictions |           76 |
| Accuracy              |   **96.49%** |
| Error rate            |    **3.51%** |
| Client target         |       90.00% |
| Margin above target   | **+6.49 pp** |

The final model was then retrained on the complete set of **10,822 labelled requests** before generating predictions for the 2,178 unlabelled test requests.

---

# Model Comparison

Three model configurations were evaluated during development.

| Experiment   | Features                                      | Model     | Validation Accuracy |
| ------------ | --------------------------------------------- | --------- | ------------------: |
| Baseline     | Word TF-IDF                                   | LinearSVC |              94.09% |
| Experiment 2 | Word + Character TF-IDF                       | LinearSVC |              95.66% |
| Experiment 3 | Word + Character TF-IDF + Structured Metadata | LinearSVC |          **96.49%** |

## Improvement over baseline

The progression was:

```text
Word TF-IDF
    │
    │ +1.57 pp
    ▼
Word + Character TF-IDF
    │
    │ +0.83 pp
    ▼
Word + Character TF-IDF + Metadata
    │
    ▼
96.49%
```

The final model was selected because it produced the highest chronological validation accuracy while remaining lightweight, reproducible, and suitable for local deployment.

---

# Leakage Controls

Preventing data leakage was an important part of the modeling process.

The model only uses information that would be available when a customer request is created.

## Features Used

```text
request_text
channel
product_family
warranty_status
source
```

## Features Excluded

```text
final_team
transfers
resolved_at
```

### Why were these fields excluded?

`final_team` represents the team that eventually closed the request.

`transfers` represents routing activity that occurred after the initial assignment.

`resolved_at` represents information generated during or after resolution.

Using these fields would allow the model to learn from information that would not be available at prediction time.

Therefore, these fields were used only for:

* Operational analysis
* Error investigation
* Understanding historical routing behavior

They were never provided to the classifier.

---

# Error Analysis

The final validation set contained:

```text
2,165 requests
2,089 correct
76 incorrect
```

This corresponds to an error rate of:

**3.51%**

The complete validation errors are stored in:

```text
evaluation/validation_errors.csv
```

The confusion-pair analysis is stored in:

```text
evaluation/confusion_pairs.csv
```

## Top Confusion Patterns

| Actual Team           | Predicted Team        | Cases |
| --------------------- | --------------------- | ----: |
| Repairs               | Filters & Consumables |    11 |
| Repairs               | Billing               |     7 |
| Repairs               | Warranty Claims       |     6 |
| Repairs               | Product Advice        |     3 |
| Filters & Consumables | Warranty Claims       |     3 |
| Returns & Replacement | Installs & Demo       |     3 |
| Returns & Replacement | Warranty Claims       |     3 |
| Returns & Replacement | Filters & Consumables |     3 |

The largest recurring confusion was **Repairs → Filters & Consumables**.

---

# Multi-Intent Requests

A significant portion of the remaining errors comes from requests containing multiple intents.

For example:

```text
"purifier showing error code E3 purifier not working"
```

The operational meaning is a product fault and therefore belongs to Repairs, but the request also contains purifier/consumable-related vocabulary.

Another example:

```text
"installer did not turn up for ceiling fan,
ceiling fan making loud noise"
```

contains both installation and repair-related information.

These examples show that some customer requests are ambiguous or contain multiple service intents.

The model was not manually overridden for these cases because doing so would introduce undocumented business rules and could distort the historical-label objective.

---

# Error Analysis by Channel

| Channel  | Validation Requests | Errors | Error Rate |
| -------- | ------------------: | -----: | ---------: |
| Chat     |                 682 |     21 |      3.08% |
| Email    |                 230 |     12 |      5.22% |
| IVR      |                 586 |     22 |      3.75% |
| WhatsApp |                 667 |     21 |      3.15% |

Email had the highest observed validation error rate at **5.22%**, although its validation sample is smaller than the other channels.

---

# Error Analysis by Product

| Product Family    | Validation Requests | Errors | Error Rate |
| ----------------- | ------------------: | -----: | ---------: |
| Water Purifier    |                 444 |     26 |  **5.86%** |
| Room Heater       |                 251 |     10 |      3.98% |
| Induction Cooktop |                 269 |      9 |      3.35% |
| Ceiling Fan       |                 255 |      8 |      3.14% |
| Air Fryer         |                 389 |     11 |      2.83% |
| Robot Vacuum      |                 220 |      5 |      2.27% |
| Mixer Grinder     |                 337 |      7 |      2.08% |

Water Purifier requests had the highest validation error rate at **5.86%**.

This is consistent with the qualitative error analysis, where purifier requests frequently combine:

* Product faults
* Filters and consumables
* Warranty
* Installation
* Payment-related language

This category should therefore receive additional monitoring during a production rollout.

---

# Error Analysis by Warranty Status

| Warranty Status | Validation Requests | Errors | Error Rate |
| --------------- | ------------------: | -----: | ---------: |
| In Warranty     |               1,167 |     47 |      4.03% |
| Out of Warranty |                 541 |     14 |      2.59% |
| Shield          |                 457 |     15 |      3.28% |

The majority of validation requests were in warranty, and this category also contained the largest number of errors.

---

# Interpretation of Remaining Errors

The remaining errors should not automatically be treated as model defects.

Many involve requests where the customer's opening message contains multiple service intents.

Examples include:

```text
Fault + Consumables
Fault + Warranty
Fault + Payment
Return + Installation
Return + Warranty
Installation + Fault
```

These cases are useful candidates for future improvements such as:

* Intent prioritization
* Human review for ambiguous requests
* Multi-intent detection
* Business-rule assistance
* Confidence-based escalation

The current implementation deliberately keeps the model simple and reproducible rather than adding undocumented post-processing rules.

---

# Prediction Generation

After model selection, the final model is retrained on all **10,822 labelled training requests**.

Run:

```bash
python src/train_final.py
```

This creates:

```text
models/kestrel_router.joblib
```

The trained model is then used to generate predictions for the **2,178 unlabelled test requests**.

Run:

```bash
python src/predict.py
```

Output:

```text
outputs/predictions.csv
```

The output format is:

```csv
request_id,team
SR510822,Repairs
SR510823,Filters & Consumables
...
```

The generated file was validated against the provided sample submission.

Validation checks include:

* Correct number of rows
* Correct columns
* No duplicate request IDs
* No missing request IDs
* No missing team predictions
* Exact request ID ordering
* Only valid service-team labels

---

# API

The trained model is exposed through a FastAPI service.

## Start the API

```bash
uvicorn app.main:app --reload
```

The service runs at:

```text
http://127.0.0.1:8000
```

---

## Health Endpoint

```http
GET /health
```

Example:

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{
  "status": "ok",
  "model": "kestrel_router"
}
```

---

## Routing Endpoint

```http
POST /route
```

Example request:

```json
{
  "request_text": "my water purifier is leaking water",
  "product_family": "Water Purifier",
  "warranty_status": "in_warranty",
  "channel": "whatsapp",
  "source": "crm"
}
```

Example response:

```json
{
  "predicted_team": "Repairs",
  "reason": "The request contains product-fault or service-problem language, so it is routed to Repairs."
}
```

The API returns a human-readable explanation alongside the prediction.

The system does not report an artificial probability because `LinearSVC` does not produce calibrated probabilities.

---

# User Interface

A lightweight Streamlit interface is provided for demonstration.

Start the API first:

```bash
uvicorn app.main:app --reload
```

Then open another terminal:

```bash
streamlit run app/ui.py
```

The UI allows the user to enter:

* Customer request
* Product family
* Warranty status
* Channel
* Source

The interface then sends the request to the FastAPI service and displays:

```text
Predicted Team
+
Human-readable routing explanation
```

---

# Testing

Automated tests are provided using pytest.

Run:

```bash
pytest -q
```

The test suite checks:

* Model availability
* API health endpoint
* Routing endpoint
* Request validation
* Prediction file structure
* Valid service-team labels
* Duplicate request IDs
* Missing predictions

Current test result:

```text
5 passed
```

A deprecation warning may appear from the installed FastAPI/Starlette testing stack, but it does not affect the passing test suite.

---

# Repository Structure

```text
kestrel-service-routing/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── ui.py
│
├── data/
│   ├── train.csv
│   ├── test_unlabelled.csv
│   ├── resolution_log.csv
│   ├── teams.csv
│   ├── sample_submission.csv
│   └── README.txt
│
├── evaluation/
│   ├── confusion_pairs.csv
│   ├── validation_errors.csv
│   ├── model_comparison.csv
│   └── model_evidence.md
│
├── memo/
│   └── ritu_memo.md
│
├── models/
│   └── kestrel_router.joblib
│
├── outputs/
│   └── predictions.csv
│
├── reference/
│   ├── email-thread.txt
│   └── ops-policy.pdf
│
├── src/
│   ├── eda.py
│   ├── split_data.py
│   ├── baseline.py
│   ├── model_experiment_2.py
│   ├── model_experiment_3.py
│   ├── error_analysis.py
│   ├── train_final.py
│   ├── predict.py
│   └── create_evidence.py
│
├── tests/
│   ├── __init__.py
│   └── test_router.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

> Confidential client data, reference documents, trained model artifacts and generated prediction files should not be committed to a public repository.

---

# Setup

## 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd kestrel-service-routing
```

## 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

## 3. Activate the Environment

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Add Client Data Locally

Place the confidential project data inside:

```text
data/
```

Expected files:

```text
train.csv
test_unlabelled.csv
resolution_log.csv
teams.csv
sample_submission.csv
```

The client reference documents should be kept locally under:

```text
reference/
```

These files are intentionally excluded from public version control.

---

# Complete Workflow

## Step 1 — Train the Final Model

```bash
python src/train_final.py
```

Creates:

```text
models/kestrel_router.joblib
```

---

## Step 2 — Generate Predictions

```bash
python src/predict.py
```

Creates:

```text
outputs/predictions.csv
```

---

## Step 3 — Run Tests

```bash
pytest -q
```

Expected:

```text
5 passed
```

---

## Step 4 — Start the API

```bash
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

---

## Step 5 — Start the UI

In another terminal:

```bash
streamlit run app/ui.py
```

The Streamlit interface will open locally in the browser.

---

# Business Considerations

The existing vendor routing bot has a stated annual license cost of:

**₹3.2 lakh/year**

Historical operational records contain:

* **3,902 transfers**
* **2,696 requests with at least one transfer**
* **2,471 first-team/final-team mismatches** after normalizing historical team names

The operational policy provides the following cost assumptions:

```text
₹305 per transfer
₹260 additional customer contact for a misdirected request
```

Applying these assumptions to the historical records gives an illustrative operational cost estimate of approximately:

**₹18.3 lakh over the 18-month training period**

This figure is an estimate based on the supplied policy assumptions and should not be interpreted as audited cost or guaranteed future savings.

The replacement model itself is lightweight and does not require a paid LLM API.

Actual production cost should be measured based on:

* Hosting
* API infrastructure
* Monitoring
* Logging
* Retraining
* Operational support

---

# Deployment Considerations

The **96.49% validation accuracy** demonstrates strong historical-label matching, but offline accuracy alone does not guarantee identical production performance.

A controlled rollout should monitor:

1. Routing accuracy
2. Transfer rate
3. Customer re-contact rate
4. Manual overrides
5. Error rate by service team
6. Error rate by product family
7. Ambiguous or multi-intent requests
8. Changes in request distribution

Special attention should be given to:

```text
Water Purifier
Repairs
Filters & Consumables
Warranty Claims
```

because several remaining validation errors involve overlapping intents between these categories.

---

# Monday Handoff

The following artifacts should be handed over to the next team:

1. Final model training code
2. Model evaluation results
3. Validation error analysis
4. FastAPI service
5. Streamlit demonstration UI
6. Automated tests
7. Prediction generation script
8. Business memo
9. Setup and deployment instructions

The incoming team should be able to reproduce the model and predictions using the documented workflow.

The model should be retrained or reviewed if:

* Service teams change
* Routing policy changes
* New product categories are introduced
* Customer request patterns change materially
* Production transfer rates increase
* Manual routing overrides become frequent

---

# Confidentiality

The Kestrel Home dataset and operational documents are confidential.

The following files must **not** be uploaded to a public GitHub repository:

```text
data/train.csv
data/test_unlabelled.csv
data/resolution_log.csv
data/teams.csv
data/sample_submission.csv
data/README.txt

reference/email-thread.txt
reference/ops-policy.pdf
```

These files should be excluded through `.gitignore`.

The public repository should contain only:

* Source code
* Tests
* Documentation
* Sanitized evaluation summaries
* Model methodology
* Non-confidential project artifacts

No customer request text or other client-sensitive records should be exposed publicly.

---

# AI Usage

AI assistance was used during development for:

* Code scaffolding
* Debugging
* Experiment planning
* Documentation
* Error-analysis interpretation

The final routing model itself is a local, reproducible scikit-learn pipeline and does not require an external paid AI API.

---

# Key Takeaways

This project demonstrates an end-to-end machine learning workflow for service-request routing:

```text
Raw Historical Requests
          ↓
Data Understanding & EDA
          ↓
Team Name Normalization
          ↓
Chronological Validation
          ↓
Word TF-IDF
          ↓
Character TF-IDF
          ↓
Structured Metadata
          ↓
LinearSVC
          ↓
96.49% Validation Accuracy
          ↓
Final Model
          ↓
2,178 Test Predictions
          ↓
FastAPI Service
          ↓
Streamlit UI
          ↓
Automated Tests
          ↓
Operational Error Analysis
```

### Final Project Metrics

| Metric                           |       Result |
| -------------------------------- | -----------: |
| Historical labelled requests     |       10,822 |
| Test requests                    |        2,178 |
| Service teams                    |            7 |
| Validation requests              |        2,165 |
| Validation accuracy              |   **96.49%** |
| Client target                    |      **90%** |
| Validation error rate            |    **3.51%** |
| Correct validation predictions   |    **2,089** |
| Incorrect validation predictions |       **76** |
| Automated tests                  | **5 passed** |

The resulting system provides a lightweight and reproducible approach to service-request routing while explicitly addressing temporal validation, data leakage, historical team renaming, ambiguous requests, operational analysis, API deployment, and confidentiality.

```
```
