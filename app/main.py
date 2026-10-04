import os
import re
import joblib
import numpy as np
import pandas as pd

from scipy.sparse import hstack, csr_matrix
from fastapi import FastAPI
from pydantic import BaseModel, Field


MODEL_PATH = "models/kestrel_router.joblib"


app = FastAPI(
    title="Kestrel Home Service Request Router",
    version="2.0.0",
)


# =============================================================================
# LOAD FINAL MODEL ARTIFACT
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
# REQUEST SCHEMA
# =============================================================================

class RoutingRequest(BaseModel):
    request_text: str = Field(..., min_length=1)
    product_family: str
    warranty_status: str
    channel: str
    source: str


# =============================================================================
# EXACT SAME INTENT PATTERNS AS TRAINING
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
# EXACT SAME ENGINEERED FEATURES AS TRAINING
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
# BUILD MODEL FEATURES
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

    # IMPORTANT:
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
# EXPLANATION
# =============================================================================

def explain_prediction(team, request_text):

    text = request_text.lower()

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
    }


# =============================================================================
# ROUTING
# =============================================================================

@app.post("/route")
def route_request(request: RoutingRequest):

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
        "predicted_team": prediction,
        "reason": explain_prediction(
            prediction,
            request.request_text,
        ),
    }
