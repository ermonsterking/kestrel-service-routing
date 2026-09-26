import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report


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

    y_train = train_df["target"]
    y_valid = valid_df["target"]

    # --------------------------------------------------
    # Text
    # --------------------------------------------------

    train_text = train_df["request_text"].fillna("")
    valid_text = valid_df["request_text"].fillna("")

    # --------------------------------------------------
    # Combine text + structured fields into one DataFrame
    # --------------------------------------------------

    text_and_meta_train = train_df[
        [
            "request_text",
            "channel",
            "product_family",
            "warranty_status",
            "source",
        ]
    ].copy()

    text_and_meta_valid = valid_df[
        [
            "request_text",
            "channel",
            "product_family",
            "warranty_status",
            "source",
        ]
    ].copy()

    # --------------------------------------------------
    # Feature engineering
    # --------------------------------------------------

    preprocess = ColumnTransformer(
        transformers=[

            # Word TF-IDF
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

            # Character TF-IDF
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

            # Structured categorical features
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

    # --------------------------------------------------
    # Full model
    # --------------------------------------------------

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

    print("Training Experiment 3...")

    model.fit(
        text_and_meta_train,
        y_train
    )

    # --------------------------------------------------
    # Predict
    # --------------------------------------------------

    predictions = model.predict(
        text_and_meta_valid
    )

    # --------------------------------------------------
    # Evaluate
    # --------------------------------------------------

    accuracy = accuracy_score(
        y_valid,
        predictions
    )

    print("\n" + "=" * 70)
    print("EXPERIMENT 3 RESULTS")
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