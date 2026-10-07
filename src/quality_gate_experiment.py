import pandas as pd
import numpy as np

from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC


# ============================================================
# CONFIG
# ============================================================

TRAIN_PATH = "data/train.csv"
LABEL_PATH = "evaluation/quality_labels/routing_quality_labels_v21.csv"

OUT_DIR = Path("evaluation/quality_gate")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

train = pd.read_csv(TRAIN_PATH)
labels = pd.read_csv(LABEL_PATH)

print(f"Train shape: {train.shape}")
print(f"Quality labels shape: {labels.shape}")


# ============================================================
# MERGE
# ============================================================

label_cols = [
    "request_id",
    "quality_label",
]

df = train.merge(
    labels[label_cols],
    on="request_id",
    how="inner",
    validate="one_to_one",
)

print(f"Merged shape: {df.shape}")

if len(df) != len(train):
    raise ValueError(
        "Merge mismatch: some training requests do not have "
        "quality labels."
    )


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

df["created_at_ist"] = pd.to_datetime(
    df["created_at_ist"]
)

df = df.sort_values(
    "created_at_ist"
).reset_index(drop=True)


# ============================================================
# FEATURES
# ============================================================

df["request_text"] = (
    df["request_text"]
    .fillna("")
    .astype(str)
)

categorical_columns = [
    "product_family",
    "warranty_status",
    "channel",
    "source",
]

for col in categorical_columns:
    df[col] = (
        df[col]
        .fillna("unknown")
        .astype(str)
    )


# ============================================================
# CHRONOLOGICAL 80/20 SPLIT
# ============================================================

split_idx = int(len(df) * 0.80)

train_df = df.iloc[:split_idx].copy()
val_df = df.iloc[split_idx:].copy()

print("\nChronological split:")
print(f"Training:   {len(train_df)}")
print(f"Validation: {len(val_df)}")

print(
    "\nTraining period:",
    train_df["created_at_ist"].min(),
    "→",
    train_df["created_at_ist"].max(),
)

print(
    "Validation period:",
    val_df["created_at_ist"].min(),
    "→",
    val_df["created_at_ist"].max(),
)


# ============================================================
# X / Y
# ============================================================

X_train = train_df[
    ["request_text"] + categorical_columns
]

y_train = train_df["quality_label"]

X_val = val_df[
    ["request_text"] + categorical_columns
]

y_val = val_df["quality_label"]


# ============================================================
# PREPROCESSING
# ============================================================

word_features = Pipeline(
    [
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=2,
                sublinear_tf=True,
                max_features=50000,
            ),
        )
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "text",
            word_features,
            "request_text",
        ),
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_columns,
        ),
    ]
)


# ============================================================
# MODEL
# ============================================================

model = Pipeline(
    [
        (
            "features",
            preprocessor,
        ),
        (
            "classifier",
            LinearSVC(
                C=1.0,
                class_weight="balanced",
                max_iter=10000,
            ),
        ),
    ]
)


# ============================================================
# TRAIN
# ============================================================

print("\nTraining quality gate...")

model.fit(
    X_train,
    y_train,
)


# ============================================================
# VALIDATION
# ============================================================

pred = model.predict(X_val)

accuracy = accuracy_score(
    y_val,
    pred,
)

macro_f1 = f1_score(
    y_val,
    pred,
    average="macro",
)

weighted_f1 = f1_score(
    y_val,
    pred,
    average="weighted",
)

print("\n==========================================")
print("QUALITY GATE RESULTS")
print("==========================================")

print(f"Accuracy:    {accuracy:.4f}")
print(f"Macro F1:    {macro_f1:.4f}")
print(f"Weighted F1: {weighted_f1:.4f}")


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

report = classification_report(
    y_val,
    pred,
    digits=4,
)

print("\nClassification report:")
print(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

classes = sorted(
    y_val.unique()
)

cm = confusion_matrix(
    y_val,
    pred,
    labels=classes,
)

cm_df = pd.DataFrame(
    cm,
    index=classes,
    columns=classes,
)

cm_df.to_csv(
    OUT_DIR / "quality_gate_confusion_matrix.csv"
)


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

validation_predictions = val_df[
    [
        "request_id",
        "created_at_ist",
        "request_text",
        "product_family",
        "warranty_status",
        "channel",
        "source",
        "quality_label",
    ]
].copy()

validation_predictions[
    "predicted_quality"
] = pred

validation_predictions[
    "correct"
] = (
    validation_predictions["quality_label"]
    ==
    validation_predictions["predicted_quality"]
)

validation_predictions.to_csv(
    OUT_DIR / "quality_gate_validation_predictions.csv",
    index=False,
)


# ============================================================
# PER-CLASS PERFORMANCE
# ============================================================

report_dict = classification_report(
    y_val,
    pred,
    output_dict=True,
)

rows = []

for cls in classes:
    rows.append(
        {
            "quality_label": cls,
            "precision": report_dict[cls]["precision"],
            "recall": report_dict[cls]["recall"],
            "f1": report_dict[cls]["f1-score"],
            "support": report_dict[cls]["support"],
        }
    )

class_metrics = pd.DataFrame(rows)

class_metrics.to_csv(
    OUT_DIR / "quality_gate_class_metrics.csv",
    index=False,
)


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame(
    [
        {
            "model": "TF-IDF + metadata + LinearSVC",
            "target": "quality_label",
            "split": "chronological_80_20",
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "train_rows": len(train_df),
            "validation_rows": len(val_df),
        }
    ]
)

summary.to_csv(
    OUT_DIR / "quality_gate_results.csv",
    index=False,
)


# ============================================================
# SAVE MODEL
# ============================================================

import joblib

joblib.dump(
    model,
    OUT_DIR / "quality_gate_model.joblib",
)


print("\nSaved:")
print(
    OUT_DIR / "quality_gate_model.joblib"
)
print(
    OUT_DIR / "quality_gate_results.csv"
)
print(
    OUT_DIR / "quality_gate_class_metrics.csv"
)
print(
    OUT_DIR / "quality_gate_confusion_matrix.csv"
)
print(
    OUT_DIR / "quality_gate_validation_predictions.csv"
)