import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
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
    # Load
    # --------------------------------------------------

    df = pd.read_csv(TRAIN_PATH)

    df["created_at_ist"] = pd.to_datetime(
        df["created_at_ist"]
    )

    # --------------------------------------------------
    # Normalize historical team names
    # --------------------------------------------------

    df["target"] = df["team_label"].replace(
        TEAM_RENAME_MAP
    )

    # --------------------------------------------------
    # Chronological ordering
    # --------------------------------------------------

    df = df.sort_values(
        "created_at_ist"
    ).reset_index(drop=True)

    # --------------------------------------------------
    # 80/20 chronological split
    # --------------------------------------------------

    split_idx = int(len(df) * 0.80)

    train_df = df.iloc[:split_idx]
    valid_df = df.iloc[split_idx:]

    X_train = train_df["request_text"].fillna("")
    y_train = train_df["target"]

    X_valid = valid_df["request_text"].fillna("")
    y_valid = valid_df["target"]

    # --------------------------------------------------
    # Model
    # --------------------------------------------------

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=2,
                sublinear_tf=True,
            ),
        ),

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

    print("Training baseline model...")

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
    # Metrics
    # --------------------------------------------------

    accuracy = accuracy_score(
        y_valid,
        predictions
    )

    print("\n" + "=" * 70)
    print("BASELINE RESULTS")
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

    print("\nConfusion Matrix:")

    labels = sorted(
        y_valid.unique()
    )

    cm = confusion_matrix(
        y_valid,
        predictions,
        labels=labels
    )

    print(
        pd.DataFrame(
            cm,
            index=labels,
            columns=labels
        )
    )


if __name__ == "__main__":
    main()