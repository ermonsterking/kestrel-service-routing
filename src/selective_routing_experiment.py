import joblib
import pandas as pd
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    f1_score,
)


# ============================================================
# CONFIG
# ============================================================

QUALITY_MODEL = (
    "evaluation/quality_gate/quality_gate_model.joblib"
)

QUALITY_VALIDATION = (
    "evaluation/quality_gate/"
    "quality_gate_validation_predictions.csv"
)

ROUTER_VALIDATION = (
    "evaluation/final_model_validation_predictions.csv"
)

OUT_DIR = Path("evaluation/quality_gate")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD
# ============================================================

quality_model = joblib.load(QUALITY_MODEL)

quality_df = pd.read_csv(
    QUALITY_VALIDATION
)

router_df = pd.read_csv(
    ROUTER_VALIDATION
)

print("Quality validation:", quality_df.shape)
print("Router validation:", router_df.shape)


# ============================================================
# CHECK REQUEST IDS
# ============================================================

if quality_df["request_id"].duplicated().any():
    raise ValueError(
        "Duplicate request IDs in quality validation."
    )

if router_df["request_id"].duplicated().any():
    raise ValueError(
        "Duplicate request IDs in router validation."
    )


# ============================================================
# MERGE
# ============================================================

router_cols = [
    "request_id",
    "final_team",
    "predicted_team",
    "historical_bot",
]

router = router_df[router_cols].copy()

df = quality_df.merge(
    router,
    on="request_id",
    how="inner",
    validate="one_to_one",
)

print("Merged:", df.shape)

if len(df) != len(quality_df):
    raise ValueError(
        "Quality and router validation sets do not match."
    )


# ============================================================
# CALCULATE ROUTER / BOT CORRECTNESS
# ============================================================

df["router_correct"] = (
    df["final_team"]
    ==
    df["predicted_team"]
)

df["bot_correct"] = (
    df["final_team"]
    ==
    df["historical_bot"]
)


# ============================================================
# QUALITY-GATE PREDICTION
# ============================================================

feature_columns = [
    "request_text",
    "product_family",
    "warranty_status",
    "channel",
    "source",
]

X = quality_df[feature_columns]

df["predicted_quality"] = (
    quality_model.predict(X)
)


# ============================================================
# QUALITY GATE METRICS
# ============================================================

print("\n==========================================")
print("QUALITY GATE")
print("==========================================")

print(
    f"Accuracy: "
    f"{accuracy_score(df['quality_label'], df['predicted_quality']):.4f}"
)

print(
    f"Macro F1: "
    f"{f1_score(df['quality_label'], df['predicted_quality'], average='macro'):.4f}"
)


# ============================================================
# ROUTABLE SUBSETS
# ============================================================

actual_routable = df[
    df["quality_label"] == "ROUTABLE"
].copy()

selected_routable = df[
    df["predicted_quality"] == "ROUTABLE"
].copy()


# ============================================================
# ACTUAL ROUTABLE PERFORMANCE
# ============================================================

print("\n==========================================")
print("ACTUAL ROUTABLE SUBSET")
print("==========================================")

print(
    "Requests:",
    len(actual_routable)
)

print(
    "Coverage:",
    f"{len(actual_routable) / len(df) * 100:.2f}%"
)

print(
    "Router accuracy:",
    f"{actual_routable['router_correct'].mean() * 100:.2f}%"
)

print(
    "Router macro F1:",
    f"{f1_score(
        actual_routable['final_team'],
        actual_routable['predicted_team'],
        average='macro'
    ): .4f}"
)


# ============================================================
# GATE-SELECTED ROUTABLE PERFORMANCE
# ============================================================

print("\n==========================================")
print("GATE-SELECTED ROUTABLE SUBSET")
print("==========================================")

print(
    "Requests:",
    len(selected_routable)
)

print(
    "Coverage:",
    f"{len(selected_routable) / len(df) * 100:.2f}%"
)

print(
    "Router accuracy:",
    f"{selected_routable['router_correct'].mean() * 100:.2f}%"
)

print(
    "Router macro F1:",
    f"{f1_score(
        selected_routable['final_team'],
        selected_routable['predicted_team'],
        average='macro'
    ): .4f}"
)


# ============================================================
# QUALITY-GATE REJECTION
# ============================================================

rejected = df[
    df["predicted_quality"] != "ROUTABLE"
].copy()

print("\n==========================================")
print("QUALITY-GATE REJECTION")
print("==========================================")

print(
    "Rejected:",
    len(rejected)
)

print(
    "Rejected:",
    f"{len(rejected) / len(df) * 100:.2f}%"
)

print("\nRejected distribution:")

print(
    rejected["predicted_quality"]
    .value_counts()
    .to_string()
)


# ============================================================
# ROUTING PERFORMANCE BY PREDICTED QUALITY
# ============================================================

print("\n==========================================")
print("ROUTER ACCURACY BY QUALITY STATE")
print("==========================================")

for state in [
    "ROUTABLE",
    "MULTI_INTENT",
    "NEEDS_CLARIFICATION",
    "DATA_CONFLICT",
]:

    subset = df[
        df["predicted_quality"] == state
    ]

    if len(subset) == 0:
        continue

    print(
        f"{state:22s} "
        f"n={len(subset):4d} "
        f"router_acc="
        f"{subset['router_correct'].mean() * 100:.2f}%"
    )


# ============================================================
# SELECTIVE ROUTING SUMMARY
# ============================================================

summary = pd.DataFrame(
    [
        {
            "total_validation": len(df),

            "actual_routable":
                len(actual_routable),

            "actual_routable_coverage":
                len(actual_routable) / len(df),

            "actual_routable_router_accuracy":
                actual_routable["router_correct"].mean(),

            "gate_selected_routable":
                len(selected_routable),

            "gate_selected_coverage":
                len(selected_routable) / len(df),

            "gate_selected_router_accuracy":
                selected_routable["router_correct"].mean(),

            "gate_rejected":
                len(rejected),

            "gate_rejected_rate":
                len(rejected) / len(df),
        }
    ]
)

summary.to_csv(
    OUT_DIR /
    "selective_routing_summary.csv",
    index=False,
)


# ============================================================
# SAVE DETAILED OUTPUT
# ============================================================

df.to_csv(
    OUT_DIR /
    "selective_routing_validation.csv",
    index=False,
)


# ============================================================
# FINAL
# ============================================================

print("\nSaved:")
print(
    OUT_DIR /
    "selective_routing_summary.csv"
)

print(
    OUT_DIR /
    "selective_routing_validation.csv"
)