import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


TRAIN_PATH = "data/train.csv"

TEAM_RENAME_MAP = {
    "Installations": "Installs & Demo",
    "Consumables": "Filters & Consumables",
}


def main():

    # --------------------------------------------------
    # Load data
    # --------------------------------------------------

    df = pd.read_csv(TRAIN_PATH)

    df["created_at_ist"] = pd.to_datetime(
        df["created_at_ist"]
    )

    df["target"] = df["team_label"].replace(
        TEAM_RENAME_MAP
    )

    df = df.sort_values(
        "created_at_ist"
    ).reset_index(drop=True)

    # --------------------------------------------------
    # Chronological split
    # --------------------------------------------------

    split_idx = int(len(df) * 0.80)

    train_df = df.iloc[:split_idx].copy()
    valid_df = df.iloc[split_idx:].copy()

    features = [
        "request_text",
        "channel",
        "product_family",
        "warranty_status",
        "source",
    ]

    X_train = train_df[features]
    y_train = train_df["target"]

    X_valid = valid_df[features]
    y_valid = valid_df["target"]

    # --------------------------------------------------
    # Feature pipeline
    # --------------------------------------------------

    preprocess = ColumnTransformer(
        transformers=[

            (
                "word",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
                "request_text",
            ),

            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                ),
                "request_text",
            ),

            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                [
                    "channel",
                    "product_family",
                    "warranty_status",
                    "source",
                ],
            ),
        ]
    )

    model = Pipeline([
        ("features", preprocess),

        (
            "classifier",
            LinearSVC(
                class_weight="balanced",
                C=1.0,
            ),
        ),
    ])

    # --------------------------------------------------
    # Train
    # --------------------------------------------------

    print("Training final validation model...")

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------
    # Predict
    # --------------------------------------------------

    predictions = model.predict(
        X_valid
    )

    # --------------------------------------------------
    # Basic metrics
    # --------------------------------------------------

    accuracy = accuracy_score(
        y_valid,
        predictions
    )

    print("\n" + "=" * 70)
    print("ERROR ANALYSIS")
    print("=" * 70)

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )

    # --------------------------------------------------
    # Create validation results
    # --------------------------------------------------

    results = valid_df.copy()

    results["predicted_team"] = predictions

    results["correct"] = (
        results["target"]
        == results["predicted_team"]
    )

    # --------------------------------------------------
    # Overall errors
    # --------------------------------------------------

    errors = results[
        ~results["correct"]
    ].copy()

    print(
        "\nCorrect:",
        results["correct"].sum()
    )

    print(
        "Incorrect:",
        len(errors)
    )

    print(
        "Error rate:",
        round(
            len(errors) / len(results) * 100,
            2
        ),
        "%"
    )

    # --------------------------------------------------
    # Confusion pairs
    # --------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP CONFUSION PAIRS")
    print("-" * 70)

    confusion_pairs = (
        errors
        .groupby(
            [
                "target",
                "predicted_team"
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            "count",
            ascending=False
        )
    )

    print(
        confusion_pairs.head(15).to_string(
            index=False
        )
    )

    # --------------------------------------------------
    # Errors by channel
    # --------------------------------------------------

    print("\n" + "-" * 70)
    print("ERRORS BY CHANNEL")
    print("-" * 70)

    channel_stats = (
        results
        .groupby("channel")
        .agg(
            total=("correct", "size"),
            errors=("correct", lambda x: (~x).sum())
        )
    )

    channel_stats["error_rate"] = (
        channel_stats["errors"]
        / channel_stats["total"]
        * 100
    ).round(2)

    print(channel_stats)

    # --------------------------------------------------
    # Errors by product
    # --------------------------------------------------

    print("\n" + "-" * 70)
    print("ERRORS BY PRODUCT")
    print("-" * 70)

    product_stats = (
        results
        .groupby("product_family")
        .agg(
            total=("correct", "size"),
            errors=("correct", lambda x: (~x).sum())
        )
    )

    product_stats["error_rate"] = (
        product_stats["errors"]
        / product_stats["total"]
        * 100
    ).round(2)

    print(
        product_stats.sort_values(
            "error_rate",
            ascending=False
        )
    )

    # --------------------------------------------------
    # Errors by warranty
    # --------------------------------------------------

    print("\n" + "-" * 70)
    print("ERRORS BY WARRANTY STATUS")
    print("-" * 70)

    warranty_stats = (
        results
        .groupby("warranty_status")
        .agg(
            total=("correct", "size"),
            errors=("correct", lambda x: (~x).sum())
        )
    )

    warranty_stats["error_rate"] = (
        warranty_stats["errors"]
        / warranty_stats["total"]
        * 100
    ).round(2)

    print(warranty_stats)

    # --------------------------------------------------
    # Show sample errors
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("SAMPLE MISCLASSIFICATIONS")
    print("=" * 70)

    columns = [
        "request_id",
        "request_text",
        "product_family",
        "warranty_status",
        "channel",
        "target",
        "predicted_team",
    ]

    print(
        errors[columns]
        .head(30)
        .to_string(index=False)
    )

    # --------------------------------------------------
    # Save errors
    # --------------------------------------------------

    errors.to_csv(
        "evaluation/validation_errors.csv",
        index=False
    )

    confusion_pairs.to_csv(
        "evaluation/confusion_pairs.csv",
        index=False
    )

    print(
        "\nSaved:"
        "\n  evaluation/validation_errors.csv"
        "\n  evaluation/confusion_pairs.csv"
    )


if __name__ == "__main__":
    main()