# Kestrel Home — Service Request Routing

An end-to-end machine learning system for automatically routing Kestrel Home customer service requests to the appropriate service team.

**Validation accuracy: 96.49%** (client target: 90%)

---

## Table of Contents

- [Introduction](#introduction)
- [Objective](#objective)
- [Tools & Technologies](#tools--technologies)
- [Submission_Artifacts]
 (# Submission Artifacts)
- [Dataset](#dataset)
- [Service Teams](#service-teams)
- [Data Understanding & EDA](#data-understanding--eda)
- [Modeling Approach](#modeling-approach)
- [Feature Engineering](#feature-engineering)
- [Model Architecture](#model-architecture)
- [Classifier](#classifier)
- [Model Experiments](#model-experiments)
- [Validation Strategy](#validation-strategy)
- [Results](#results)
- [Leakage Controls](#leakage-controls)
- [Error Analysis](#error-analysis)
- [Prediction Generation](#prediction-generation)
- [API](#api)
- [User Interface](#user-interface)
- [Testing](#testing)
- [Repository Structure](#repository-structure)
- [Setup](#setup)
- [Complete Workflow](#complete-workflow)
- [Business Considerations](#business-considerations)
- [Deployment Considerations](#deployment-considerations)
- [Monday Handoff](#monday-handoff)
- [Confidentiality](#confidentiality)
- [AI Usage](#ai-usage)
- [Key Takeaways](#key-takeaways)




---

## Introduction

Kestrel Home Appliances receives customer service requests across multiple channels, including chat, WhatsApp, IVR, and email. Each request needs to be routed to one of seven service teams:

- Billing
- Filters & Consumables
- Installs & Demo
- Product Advice
- Repairs
- Returns & Replacement
- Warranty Claims

The existing routing process uses a vendor routing bot. The objective of this project is to build a reproducible machine learning system that learns from historical routing decisions and predicts the appropriate service team for new customer requests.

The solution uses a lightweight local NLP classification pipeline instead of a paid LLM or external AI API, making the system reproducible, inexpensive to run, and suitable for deployment as an internal service.

**Workflow:**

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
```

---

## Objective

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

> **90%+ accuracy against the historical routing labels.**

The final model achieved **96.49% chronological validation accuracy**.

---

## Tools & Technologies

**Programming Language**
- Python 3.12+

**Machine Learning**
- scikit-learn, LinearSVC, TF-IDF, OneHotEncoder

**Data Processing**
- pandas, NumPy

**Model Persistence**
- joblib

**Backend**
- FastAPI, Uvicorn, Pydantic

**Frontend / Demo**
- Streamlit

**Testing**
- pytest, FastAPI TestClient, HTTPX

**Development**
- VS Code, Python virtual environment, Ubuntu/Linux

## Submission Artifacts

The repository contains the complete reproducible routing solution, including:

- Source code for EDA, preprocessing, model experiments, final training, and prediction
- FastAPI routing service
- Streamlit demonstration UI
- Automated tests
- Aggregate model evaluation and error analysis
- Business memo
- `outputs/predictions.csv` containing predictions for all 2,178 test requests

Client-provided training/test data, reference documents, trained model artifacts, and customer-level validation error records are intentionally excluded from version control for confidentiality.


### Libraries Used

| Library        | Purpose                                               |
| -------------- | ------------------------------------------------------ |
| `pandas`       | Data loading, transformation and analysis              |
| `numpy`        | Numerical operations                                    |
| `scikit-learn` | Feature engineering, preprocessing and classification   |
| `scipy`        | Scientific computing dependency                          |
| `joblib`       | Model serialization and loading                          |
| `fastapi`      | REST API implementation                                  |
| `uvicorn`      | ASGI server for the API                                   |
| `streamlit`    | Interactive demonstration UI                               |
| `pydantic`     | API input validation                                        |
| `requests`     | UI-to-API HTTP communication                                 |
| `pytest`       | Automated testing                                              |
| `httpx`        | API test client support                                          |

---

## Dataset

The project uses approximately 18 months of labelled historical service requests.

### Training Dataset

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

### Test Dataset

**2,178 requests** — same request-time fields as training data, excluding `team_label`.

### Resolution Data

A separate resolution log contains:

```text
request_id
first_team
final_team
transfers
resolved_at
```

Used for operational analysis and error investigation only. Post-routing information from the resolution log is deliberately excluded from the model's feature set.

### Data Period

| Dataset | Period |
|---|---|
| Training | 2025-04-01 → 2026-06-30 |
| Test | 2026-07-01 → 2026-09-30 |

### Data Sources

Requests originate from **CRM** and the **legacy Zoho system**. The system migration occurred during the historical period, so `source` is included as a request-time feature.

---

## Service Teams

| Team                  | Primary Responsibility                                                               |
| ---------------------- | -------------------------------------------------------------------------------------- |
| Billing               | Invoices, GST, payment issues, refunds, EMI and coupons                                 |
| Filters & Consumables | Filters, candles, membranes, jars, brushes, blades, AMC kits and spares                  |
| Installs & Demo       | Product installation, demonstrations and wall mounting                                    |
| Product Advice        | Product usage and pre/post-purchase questions without a fault                              |
| Repairs               | Product faults, breakdowns, error codes, leaks, noise and technician-required issues         |
| Returns & Replacement | Damaged, wrong or incomplete deliveries, returns and exchanges                                 |
| Warranty Claims       | Warranty registration, coverage and warranty claim requests                                     |

### Historical Team Name Normalization

Two historical team names were renamed during the data period:

```text
Installations       →   Installs & Demo
Consumables          →   Filters & Consumables
```

These historical labels were normalized before training and evaluation so the final classifier predicts the current seven-team structure.

---

## Data Understanding & EDA

Initial analysis covered dataset size and schema, missing values, duplicate records, class/channel/product/warranty distribution, historical data sources, request-text characteristics, transfer patterns, first-team vs. final-team routing, and legacy data quality issues.

### Dataset Summary

| Dataset        |   Rows |
| -------------- | -----: |
| Training       | 10,822 |
| Test           |  2,178 |
| Resolution Log | 10,822 |
| Service Teams  |      7 |

No missing values or duplicate rows were found in the main training, test, and resolution datasets.

### Historical Routing Analysis

- **3,902** total transfers
- **2,696** requests with at least one transfer
- **2,471** first-team/final-team mismatches after normalizing historical team names

These metrics were used for operational analysis only and were not used as model features.

### Data Quality Observation

Some older legacy Zoho requests contain text encoding artifacts. These were retained rather than manually rewritten so that model evaluation remains representative of the supplied historical data.

---

## Modeling Approach

The routing problem is treated as a **multi-class text classification problem**. The target variable, `team_label`, represents the service queue assigned to the customer request by the historical routing system. The final classifier predicts one of the seven normalized service teams.

---

## Feature Engineering

The final model uses two types of features: customer request text and structured request metadata.

### 1. Word-Level TF-IDF

```text
ngram_range = (1, 2)
min_df = 2
sublinear_tf = True
```

Captures individual words, two-word phrases, routing terminology, and domain-specific expressions. For example, `"water purifier leaking"` produces features such as `water`, `purifier`, `leaking`, `water purifier`, `purifier leaking`.

### 2. Character-Level TF-IDF

```text
analyzer = char_wb
ngram_range = (3, 5)
min_df = 2
sublinear_tf = True
```

Useful for customer-service text containing spelling variations, abbreviations, informal language, typos, partial words, product-specific terminology, and legacy encoding artifacts.

### 3. Structured Metadata

Categorical fields available at request-creation time:

```text
channel
product_family
warranty_status
source
```

Encoded using `OneHotEncoder(handle_unknown="ignore")`.

**Why metadata is useful:** two requests with similar wording may require different routing depending on context — product family distinguishes appliance-specific requests, warranty status contextualizes warranty-related requests, channel captures language differences across chat/IVR/email/WhatsApp, and source identifies CRM vs. legacy origin.

---

## Model Architecture

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

Features are combined using a `ColumnTransformer`.

---

## Classifier

```python
LinearSVC(
    C=1.0,
    class_weight="balanced"
)
```

**Why LinearSVC?**

- TF-IDF produces a high-dimensional sparse feature matrix.
- Linear models work efficiently with sparse text features.
- Training and inference are fast.
- Lightweight enough for a local service.
- No GPU required.
- No external API required.
- Reproducible behavior.

`class_weight="balanced"` accounts for class-frequency differences across the seven service teams.

---

## Model Experiments

| Experiment   | Features                                      | Model     | Validation Accuracy |
| ------------ | ---------------------------------------------- | --------- | -------------------: |
| Baseline     | Word TF-IDF                                    | LinearSVC |               94.09% |
| Experiment 2 | Word + Character TF-IDF                        | LinearSVC |               95.66% |
| Experiment 3 | Word + Character TF-IDF + Structured Metadata  | LinearSVC |           **96.49%** |

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

The final model (Experiment 3) was selected for producing the highest chronological validation accuracy while remaining lightweight, reproducible, and suitable for local deployment.

---

## Validation Strategy

Because the supplied test data represents a future time period, the project uses a **chronological validation split** rather than a random train/test split. The complete labelled dataset was sorted by `created_at_ist`; the earliest 80% was used for training and the latest 20% for validation.

| Dataset    | Requests | Period                  |
| ---------- | -------: | ------------------------ |
| Training   |    8,657 | 2025-04-01 → 2026-03-30 |
| Validation |    2,165 | 2026-03-30 → 2026-06-30 |

**Why not random split?** A random split could place very similar requests from the same historical period into both training and validation, producing an overly optimistic performance estimate. A chronological split provides a more realistic estimate of temporal generalization.

---

## Results

| Metric                |       Result |
| ---------------------- | ------------: |
| Validation requests   |         2,165 |
| Correct predictions   |         2,089 |
| Incorrect predictions |            76 |
| Accuracy              |    **96.49%** |
| Error rate            |     **3.51%** |
| Client target         |        90.00% |
| Margin above target   |  **+6.49 pp** |

The final model was retrained on the complete set of **10,822 labelled requests** before generating predictions for the **2,178** unlabelled test requests.

---

## Leakage Controls

The model only uses information available when a customer request is created.

**Features used:**
```text
request_text
channel
product_family
warranty_status
source
```

**Features excluded:**
```text
final_team
transfers
resolved_at
```

`final_team` represents the team that eventually closed the request. `transfers` represents routing activity after the initial assignment. `resolved_at` is generated during or after resolution. Using these fields would allow the model to learn from information unavailable at prediction time — they were used only for operational analysis, error investigation, and understanding historical routing behavior, never as classifier inputs.

---

## Error Analysis

Validation set: **2,165** requests, **2,089** correct, **76** incorrect (**3.51%** error rate).

Full artifacts:
```text
evaluation/validation_errors.csv
evaluation/confusion_pairs.csv
```

### Top Confusion Patterns

| Actual Team           | Predicted Team        | Cases |
| ---------------------- | ----------------------- | ----: |
| Repairs               | Filters & Consumables  |    11 |
| Repairs               | Billing                |     7 |
| Repairs               | Warranty Claims        |     6 |
| Repairs               | Product Advice         |     3 |
| Filters & Consumables | Warranty Claims        |     3 |
| Returns & Replacement | Installs & Demo        |     3 |
| Returns & Replacement | Warranty Claims        |     3 |
| Returns & Replacement | Filters & Consumables  |     3 |

The largest recurring confusion is **Repairs → Filters & Consumables**.

### Multi-Intent Requests

A significant portion of remaining errors comes from requests containing multiple intents, e.g.:

```text
"purifier showing error code E3 purifier not working"
"installer did not turn up for ceiling fan, ceiling fan making loud noise"
```

The model was not manually overridden for these cases, since doing so would introduce undocumented business rules and distort the historical-label objective.

### Error Analysis by Channel

| Channel  | Validation Requests | Errors | Error Rate |
| -------- | -------------------: | -----: | ----------: |
| Chat     |                  682 |     21 |       3.08% |
| Email    |                  230 |     12 |       5.22% |
| IVR      |                  586 |     22 |       3.75% |
| WhatsApp |                  667 |     21 |       3.15% |

### Error Analysis by Product

| Product Family    | Validation Requests | Errors | Error Rate |
| ------------------ | -------------------: | -----: | ----------: |
| Water Purifier     |                  444 |     26 |   **5.86%** |
| Room Heater        |                  251 |     10 |       3.98% |
| Induction Cooktop  |                  269 |      9 |       3.35% |
| Ceiling Fan        |                  255 |      8 |       3.14% |
| Air Fryer          |                  389 |     11 |       2.83% |
| Robot Vacuum       |                  220 |      5 |       2.27% |
| Mixer Grinder      |                  337 |      7 |       2.08% |

Water Purifier requests have the highest error rate, consistent with frequent overlap between product faults, filters/consumables, warranty, installation, and payment-related language. This category should receive additional production monitoring.

### Error Analysis by Warranty Status

| Warranty Status  | Validation Requests | Errors | Error Rate |
| ----------------- | -------------------: | -----: | ----------: |
| In Warranty       |                1,167 |     47 |       4.03% |
| Out of Warranty   |                  541 |     14 |       2.59% |
| Shield            |                  457 |     15 |       3.28% |

### Interpretation of Remaining Errors

Remaining errors should not automatically be treated as model defects — many involve multi-intent opening messages (e.g., Fault + Consumables, Fault + Warranty, Return + Installation). These are candidates for future work such as intent prioritization, human review for ambiguous requests, multi-intent detection, business-rule assistance, and confidence-based escalation. The current implementation deliberately keeps the model simple and reproducible rather than adding undocumented post-processing rules.

---

## Prediction Generation

After model selection, the final model is retrained on all **10,822** labelled requests:

```bash
python src/train_final.py
```

Creates `models/kestrel_router.joblib`.

Predictions for the **2,178** unlabelled test requests:

```bash
python src/predict.py
```

Creates `outputs/predictions.csv`:

```csv
request_id,team
SR510822,Repairs
SR510823,Filters & Consumables
...
```

Validated against the provided sample submission for: correct row count, correct columns, no duplicate/missing request IDs, no missing predictions, exact request ID ordering, and only valid service-team labels.

---

## API

The trained model is exposed through a FastAPI service.

**Start the API:**

```bash
uvicorn app.main:app --reload
```

Runs at `http://127.0.0.1:8000`.

### Health Endpoint

```http
GET /health
```

```bash
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "model": "kestrel_router"
}
```

### Routing Endpoint

```http
POST /route
```

**Example request:**

```json
{
  "request_text": "my water purifier is leaking water",
  "product_family": "Water Purifier",
  "warranty_status": "in_warranty",
  "channel": "whatsapp",
  "source": "crm"
}
```

**Example response:**

```json
{
  "predicted_team": "Repairs",
  "reason": "The request contains product-fault or service-problem language, so it is routed to Repairs."
}
```

The API returns a human-readable explanation alongside the prediction. No artificial probability score is reported, since `LinearSVC` does not produce calibrated probabilities.

---

## User Interface

A lightweight Streamlit interface is provided for demonstration.

```bash
uvicorn app.main:app --reload      # terminal 1 — start the API first
streamlit run app/ui.py            # terminal 2
```

The UI accepts customer request text, product family, warranty status, channel, and source, sends the request to the FastAPI service, and displays the predicted team with a human-readable routing explanation.

---

## Testing

```bash
pytest -q
```

The test suite checks: model availability, API health endpoint, routing endpoint, request validation, prediction file structure, valid service-team labels, duplicate request IDs, and missing predictions.

```text
5 passed
```

> A deprecation warning may appear from the installed FastAPI/Starlette testing stack; it does not affect the passing test suite.

---

## Repository Structure

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

> Confidential client data, reference documents, trained model artifacts, and generated prediction files should not be committed to a public repository.

---

## Setup

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd kestrel-service-routing
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

### 3. Activate the Environment

**Linux / macOS**
```bash
source .venv/bin/activate
```

**Windows**
```powershell
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Add Client Data Locally

Place the confidential project data inside `data/`:

```text
train.csv
test_unlabelled.csv
resolution_log.csv
teams.csv
sample_submission.csv
```

Client reference documents should be kept locally under `reference/`. These files are intentionally excluded from public version control.

---

## Complete Workflow

| Step | Command | Output |
|---|---|---|
| 1. Train the final model | `python src/train_final.py` | `models/kestrel_router.joblib` |
| 2. Generate predictions | `python src/predict.py` | `outputs/predictions.csv` |
| 3. Run tests | `pytest -q` | `5 passed` |
| 4. Start the API | `uvicorn app.main:app --reload` | `http://127.0.0.1:8000` |
| 5. Start the UI (separate terminal) | `streamlit run app/ui.py` | Local browser interface |

---

## Business Considerations

The existing vendor routing bot has a stated annual license cost of **₹3.2 lakh/year**.

Historical operational records contain:

- **3,902** transfers
- **2,696** requests with at least one transfer
- **2,471** first-team/final-team mismatches after normalizing historical team names

Operational policy cost assumptions:

```text
₹305 per transfer
₹260 additional customer contact for a misdirected request
```

Applying these assumptions to historical records gives an illustrative operational cost estimate of approximately **₹18.3 lakh over the 18-month training period**. This figure is an estimate based on the supplied policy assumptions and should not be interpreted as audited cost or guaranteed future savings.

The replacement model itself is lightweight and does not require a paid LLM API. Actual production cost should be measured based on hosting, API infrastructure, monitoring, logging, retraining, and operational support.

---

## Deployment Considerations

96.49% validation accuracy demonstrates strong historical-label matching, but offline accuracy alone does not guarantee identical production performance. A controlled rollout should monitor:

1. Routing accuracy
2. Transfer rate
3. Customer re-contact rate
4. Manual overrides
5. Error rate by service team
6. Error rate by product family
7. Ambiguous or multi-intent requests
8. Changes in request distribution

Special attention should be given to **Water Purifier**, **Repairs**, **Filters & Consumables**, and **Warranty Claims**, since several remaining validation errors involve overlapping intents between these categories.

---

## Monday Handoff

Artifacts handed over to the next team:

1. Final model training code
2. Model evaluation results
3. Validation error analysis
4. FastAPI service
5. Streamlit demonstration UI
6. Automated tests
7. Prediction generation script
8. Business memo
9. Setup and deployment instructions

The model should be retrained or reviewed if:

- Service teams change
- Routing policy changes
- New product categories are introduced
- Customer request patterns change materially
- Production transfer rates increase
- Manual routing overrides become frequent

---

## Confidentiality

The Kestrel Home dataset and operational documents are confidential. The following files must **not** be uploaded to a public GitHub repository:

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

These files should be excluded through `.gitignore`. The public repository should contain only source code, tests, documentation, sanitized evaluation summaries, model methodology, and non-confidential project artifacts. No customer request text or other client-sensitive records should be exposed publicly.

---

## AI Usage

AI assistance was used during development for code scaffolding, debugging, experiment planning, documentation, and error-analysis interpretation. The final routing model itself is a local, reproducible scikit-learn pipeline and does not require an external paid AI API.

---

## Key Takeaways

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

| Metric                           |        Result |
| --------------------------------- | -------------: |
| Historical labelled requests     |         10,822 |
| Test requests                    |          2,178 |
| Service teams                    |              7 |
| Validation requests              |          2,165 |
| Validation accuracy              |     **96.49%** |
| Client target                    |          **90%** |
| Validation error rate            |      **3.51%** |
| Correct validation predictions   |      **2,089** |
| Incorrect validation predictions |         **76** |
| Automated tests                  |  **5 passed** |

The resulting system provides a lightweight and reproducible approach to service-request routing while explicitly addressing temporal validation, data leakage, historical team renaming, ambiguous requests, operational analysis, API deployment, and confidentiality.