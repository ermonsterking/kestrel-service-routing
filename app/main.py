import os
import re

import joblib
import numpy as np
import pandas as pd

from scipy.sparse import hstack, csr_matrix
from fastapi import FastAPI
from pydantic import BaseModel, Field


# =============================================================================
# PATHS
# =============================================================================

MODEL_PATH = "models/kestrel_router.joblib"
QUALITY_GATE_PATH = "evaluation/quality_gate/quality_gate_model.joblib"


# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="Kestrel Home Service Request Router",
    version="2.1.0",
)


# =============================================================================
# LOAD FINAL ROUTER
# =============================================================================

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(
        f"Model not found at {MODEL_PATH}. "
        "Run src/train_final.py first."
    )

artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
word = artifact["word_vectorizer"]
char = artifact["char_vectorizer"]
encoder = artifact["categorical_encoder"]
scaler = artifact["numeric_scaler"]


# =============================================================================
# LOAD QUALITY GATE
# =============================================================================

if not os.path.exists(QUALITY_GATE_PATH):
    raise RuntimeError(
        f"Quality gate model not found at {QUALITY_GATE_PATH}. "
        "Run src/quality_gate_experiment.py first."
    )

quality_gate_model = joblib.load(QUALITY_GATE_PATH)


# =============================================================================
# REQUEST SCHEMA
# =============================================================================

class RoutingRequest(BaseModel):
    request_text: str = Field(..., min_length=1)
    product_family: str
    warranty_status: str
    channel: str
    source: str


# =============================================================================
# EXACT SAME INTENT PATTERNS AS FINAL ROUTER TRAINING
# =============================================================================

INTENT_PATTERNS = {
    "repair": [
        r"\bnot working\b",
        r"\bdoesn't work\b",
        r"\bdoesnt work\b",
        r"\bnot turn(?:ing)? on\b",
        r"\bbroken\b",
        r"\bfault\b",
        r"\bfaulty\b",
        r"\brepair\b",
        r"\bissue\b",
        r"\bproblem\b",
        r"\bleak(?:ing)?\b",
        r"\bnoise\b",
        r"\berror\b",
        r"\bbreakdown\b",
        r"\btechnician\b",
        r"\bservice\b",
    ],
    "installation": [
        r"\binstall(?:ation)?\b",
        r"\binstalled\b",
        r"\binstall\b",
        r"\bdemo\b",
        r"\bwall mount\b",
        r"\bwall mounting\b",
        r"\bnot installed\b",
    ],
    "billing": [
        r"\bpayment\b",
        r"\bpaid\b",
        r"\bupi\b",
        r"\binvoice\b",
        r"\bgst\b",
        r"\brefund\b",
        r"\bemi\b",
        r"\bcoupon\b",
        r"\bcharge\b",
        r"\bcharged\b",
        r"\bdouble charge\b",
    ],
    "warranty": [
        r"\bwarranty\b",
        r"\bwarranty claim\b",
        r"\bshield\b",
        r"\bcoverage\b",
        r"\bclaim\b",
        r"\bwarranty certificate\b",
    ],
    "return_replacement": [
        r"\breturn\b",
        r"\breplacement\b",
        r"\breplace\b",
        r"\bexchange\b",
        r"\bdamaged\b",
        r"\bscratch(?:ed)?\b",
        r"\bwrong product\b",
        r"\bwrong item\b",
        r"\bmissing\b",
        r"\bincomplete\b",
        r"\bused\b",
        r"\brefund\b",
    ],
    "consumables": [
        r"\bfilter\b",
        r"\bfilters\b",
        r"\bcandle\b",
        r"\bmembrane\b",
        r"\bjar\b",
        r"\bbrush\b",
        r"\bblade\b",
        r"\bamc\b",
        r"\bspare\b",
        r"\bspares\b",
        r"\bconsumable\b",
        r"\bconsumables\b",
    ],
    "product_advice": [
        r"\bhow to\b",
        r"\bhow do i\b",
        r"\bhow can i\b",
        r"\brecipe\b",
        r"\bmanual\b",
        r"\busage\b",
        r"\buse\b",
        r"\bdifference\b",
        r"\bguide\b",
        r"\bquery\b",
        r"\bhelp\b",
        r"\badvice\b",
    ],
}


# =============================================================================
# EXACT SAME ENGINEERED FEATURES AS FINAL ROUTER TRAINING
# =============================================================================

def engineered_features(df):
    texts = (
        df["request_text"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    features = []

    for text in texts:
        row = []

        # Basic text structure
        row.append(len(text))
        row.append(len(text.split()))
        row.append(text.count("?"))
        row.append(text.count("!"))
        row.append(sum(ch.isdigit() for ch in text))
        row.append(text.count("₹"))
        row.append(int(bool(re.search(r"\bko\d+\b", text))))

        # Intent keyword indicators / counts
        for patterns in INTENT_PATTERNS.values():
            count = 0

            for pattern in patterns:
                count += len(re.findall(pattern, text))

            row.append(count)

        features.append(row)

    return np.asarray(features, dtype=float)


# =============================================================================
# BUILD FINAL ROUTER FEATURES
# =============================================================================

def build_features(df):
    df = df.copy()

    df["request_text"] = (
        df["request_text"]
        .fillna("")
        .astype(str)
    )

    # Word TF-IDF
    word_features = word.transform(
        df["request_text"]
    )

    # Character TF-IDF
    char_features = char.transform(
        df["request_text"]
    )

    # Categorical features
    categorical_columns = [
        "channel",
        "product_family",
        "warranty_status",
        "source",
    ]

    categorical_features = encoder.transform(
        df[categorical_columns]
    )

    # Engineered numeric features
    numeric_features = engineered_features(df)

    numeric_features = scaler.transform(
        numeric_features
    )

    numeric_features = csr_matrix(
        numeric_features
    )

    # Same feature ordering as train_final.py
    X = hstack(
        [
            word_features,
            char_features,
            categorical_features,
            numeric_features,
        ],
        format="csr",
    )

    return X


# =============================================================================
# QUALITY GATE INPUT
# =============================================================================

def build_quality_gate_input(request: RoutingRequest):
    return pd.DataFrame(
        [
            {
                "request_text": request.request_text,
                "channel": request.channel,
                "product_family": request.product_family,
                "warranty_status": request.warranty_status,
                "source": request.source,
            }
        ]
    )


# =============================================================================
# QUALITY GATE RESPONSE MESSAGES
# =============================================================================

def clarification_question(request_text):
    text = request_text.lower().strip()

    if not text:
        return "What issue are you experiencing with your product?"

    if any(
        re.search(pattern, text)
        for pattern in [
            r"\bhelp\b",
            r"\bquery\b",
            r"\bproblem\b",
            r"\bissue\b",
            r"\bcomplaint\b",
            r"\bservice request\b",
        ]
    ):
        return (
            "Could you briefly describe the specific issue, "
            "such as a fault, payment problem, installation request, "
            "return, warranty issue, or product-usage question?"
        )

    return "What specific issue would you like us to help you with?"


def quality_gate_reason(status):
    if status == "DATA_CONFLICT":
        return (
            "The request text and selected product metadata appear "
            "inconsistent. Please verify the product information before routing."
        )

    if status == "MULTI_INTENT":
        return (
            "The request appears to contain multiple issues. "
            "The customer should identify which issue needs attention first."
        )

    if status == "NEEDS_CLARIFICATION":
        return (
            "The request does not contain enough specific information "
            "to safely select a service team."
        )

    return None


# =============================================================================
# ROUTER EXPLANATION
# =============================================================================

def explain_prediction(team, request_text):

    if team == "Repairs":
        return (
            "The request contains product-fault or service-problem "
            "language, so it is routed to Repairs."
        )

    if team == "Filters & Consumables":
        return (
            "The request concerns filters, consumables, spare parts, "
            "or replacement consumable items."
        )

    if team == "Billing":
        return (
            "The request appears to concern payment, invoice, refund, "
            "GST, coupon, or another billing issue."
        )

    if team == "Returns & Replacement":
        return (
            "The request concerns a return, exchange, damaged delivery, "
            "wrong item, or replacement."
        )

    if team == "Warranty Claims":
        return (
            "The request contains warranty, coverage, registration, "
            "or warranty-claim language."
        )

    if team == "Installs & Demo":
        return (
            "The request concerns installation, demonstration, "
            "wall mounting, or an installation visit."
        )

    if team == "Product Advice":
        return (
            "The request appears to be a product usage or "
            "pre/post-purchase advice question without a clear fault."
        )

    return f"The model routed this request to {team}."


# =============================================================================
# HEALTH
# =============================================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "model": "kestrel_router",
        "target": "final_team",
        "quality_gate": "enabled",
    }


# =============================================================================
# ROUTING
# =============================================================================

@app.post("/route")
def route_request(request: RoutingRequest):

    # -------------------------------------------------------------------------
    # 1. QUALITY GATE
    # -------------------------------------------------------------------------

    quality_input = build_quality_gate_input(request)

    quality_prediction = quality_gate_model.predict(
        quality_input
    )[0]

    quality_status = str(quality_prediction)

    # -------------------------------------------------------------------------
    # 2. HANDLE NON-ROUTABLE REQUESTS
    # -------------------------------------------------------------------------

    if quality_status == "NEEDS_CLARIFICATION":

        return {
            "status": "NEEDS_CLARIFICATION",
            "predicted_team": None,
            "clarification_question": clarification_question(
                request.request_text
            ),
            "reason": quality_gate_reason(quality_status),
        }

    if quality_status == "MULTI_INTENT":

        return {
            "status": "MULTI_INTENT",
            "predicted_team": None,
            "clarification_question": (
                "Your request appears to contain multiple issues. "
                "Which issue should be handled first?"
            ),
            "reason": quality_gate_reason(quality_status),
        }

    if quality_status == "DATA_CONFLICT":

        return {
            "status": "DATA_CONFLICT",
            "predicted_team": None,
            "reason": quality_gate_reason(quality_status),
        }

    # -------------------------------------------------------------------------
    # 3. NORMAL ROUTING
    # -------------------------------------------------------------------------

    df = pd.DataFrame(
        [
            {
                "request_text": request.request_text,
                "channel": request.channel,
                "product_family": request.product_family,
                "warranty_status": request.warranty_status,
                "source": request.source,
            }
        ]
    )

    X = build_features(df)

    prediction = model.predict(X)[0]

    return {
        "status": "ROUTABLE",
        "predicted_team": prediction,
        "reason": explain_prediction(
            prediction,
            request.request_text,
        ),
    }