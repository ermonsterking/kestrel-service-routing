import os
import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field


MODEL_PATH = "models/kestrel_router.joblib"

app = FastAPI(
    title="Kestrel Home Service Request Router",
    version="1.0.0",
)


# ------------------------------------------------------------------
# Load model once when the service starts
# ------------------------------------------------------------------

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(
        f"Model not found at {MODEL_PATH}. "
        "Run src/train_final.py first."
    )

model = joblib.load(MODEL_PATH)


# ------------------------------------------------------------------
# Request schema
# ------------------------------------------------------------------

class RoutingRequest(BaseModel):
    request_text: str = Field(..., min_length=1)
    product_family: str
    warranty_status: str
    channel: str
    source: str


# ------------------------------------------------------------------
# Human-readable operational explanation
# ------------------------------------------------------------------

def explain_prediction(team: str, request_text: str) -> str:

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


# ------------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "kestrel_router",
    }


# ------------------------------------------------------------------
# Routing endpoint
# ------------------------------------------------------------------

@app.post("/route")
def route_request(request: RoutingRequest):

    features = [{
        "request_text": request.request_text,
        "channel": request.channel,
        "product_family": request.product_family,
        "warranty_status": request.warranty_status,
        "source": request.source,
    }]

    import pandas as pd

    X = pd.DataFrame(features)

    prediction = model.predict(X)[0]

    return {
        "predicted_team": prediction,
        "reason": explain_prediction(
            prediction,
            request.request_text,
        ),
    }