import pandas as pd

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
)


TRAIN_PATH = "data/train.csv"

TEAM_RENAME_MAP = {
    "Installations": "Installs & Demo",
    "Consumables": "Filters & Consumables",
}


def main():

    # -----------------------------
    # Load
    # -----------------------------

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

    # -----------------------------
    # Chronological split
    # -----------------------------

    split_idx = int(len(df) * 0.80)

    train_df = df.iloc[:split_idx]
    valid_df = df.iloc[split_idx:]

    X_train = train_df["request_text"].fillna("")
    y_train = train_df["target"]

    X_valid = valid_df["request_text"].fillna("")
    y_valid = valid_df["target"]

    # -----------------------------
    # Word + character TF-IDF
    # -----------------------------

    features = FeatureUnion([
        (
            "word",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=2,
                sublinear_tf=True,
            ),
        ),

        (
            "char",
            TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=2,
                sublinear_tf=True,
            ),
        ),
    ])

    model = Pipeline([
        ("features", features),

        (
            "classifier",
            LinearSVC(
                class_weight="balanced",
                C=1.0,
            ),
        ),
    ])

    # -----------------------------
    # Train
    # -----------------------------

    print("Training word + character model...")

    model.fit(
        X_train,
        y_train
    )

    # -----------------------------
    # Predict
    # -----------------------------

    predictions = model.predict(
        X_valid
    )

    # -----------------------------
    # Evaluate
    # -----------------------------

    accuracy = accuracy_score(
        y_valid,
        predictions
    )

    print("\n" + "=" * 70)
    print("EXPERIMENT 2 RESULTS")
    print("=" * 70)

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_valid,
            predictions,
            digits=4
        )
    )


if __name__ == "__main__":
    main()