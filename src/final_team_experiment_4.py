from pathlib import Path

import re
import numpy as np
import pandas as pd

from scipy.sparse import hstack, csr_matrix

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC


ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT / "data" / "train.csv"
RESOLUTION_PATH = ROOT / "data" / "resolution_log.csv"


def normalize_team(label):
    if pd.isna(label):
        return label

    mapping = {
        "Installations": "Installs & Demo",
        "Installs & Demo": "Installs & Demo",
        "Consumables": "Filters & Consumables",
        "Filters & Consumables": "Filters & Consumables",
    }

    return mapping.get(str(label).strip(), str(label).strip())


# ------------------------------------------------------------------
# Request-time engineered features
# ------------------------------------------------------------------

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


def engineered_features(df):
    texts = df["request_text"].fillna("").astype(str).str.lower()

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


def evaluate(name, pred, y_val):
    accuracy = accuracy_score(y_val, pred)
    macro = f1_score(y_val, pred, average="macro")
    weighted = f1_score(y_val, pred, average="weighted")

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    print(f"Accuracy:    {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"Macro F1:    {macro:.4f}")
    print(f"Weighted F1: {weighted:.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_val,
            pred,
            digits=4,
            zero_division=0,
        )
    )

    return accuracy


def main():

    train = pd.read_csv(TRAIN_PATH)
    resolution = pd.read_csv(RESOLUTION_PATH)

    resolution["final_team"] = resolution["final_team"].map(
        normalize_team
    )

    df = train.merge(
        resolution[["request_id", "final_team"]],
        on="request_id",
        how="inner",
        validate="one_to_one",
    )

    df["created_at_ist"] = pd.to_datetime(df["created_at_ist"])

    df = df.sort_values("created_at_ist").reset_index(drop=True)

    split_idx = int(len(df) * 0.80)

    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()

    print("=" * 80)
    print("EXPERIMENT 4 — WORD + CHAR TF-IDF + ENGINEERED REQUEST FEATURES")
    print("=" * 80)

    print(f"\nTrain rows:      {len(train_df)}")
    print(f"Validation rows: {len(val_df)}")

    print(
        "\nTrain period:",
        train_df["created_at_ist"].min(),
        "->",
        train_df["created_at_ist"].max(),
    )

    print(
        "Validation period:",
        val_df["created_at_ist"].min(),
        "->",
        val_df["created_at_ist"].max(),
    )

    y_train = train_df["final_team"]
    y_val = val_df["final_team"]

    # --------------------------------------------------------------
    # Text features
    # --------------------------------------------------------------

    word = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
    )

    char = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=2,
        sublinear_tf=True,
    )

    word_train = word.fit_transform(
        train_df["request_text"].fillna("")
    )

    word_val = word.transform(
        val_df["request_text"].fillna("")
    )

    char_train = char.fit_transform(
        train_df["request_text"].fillna("")
    )

    char_val = char.transform(
        val_df["request_text"].fillna("")
    )

    # --------------------------------------------------------------
    # Categorical metadata
    # --------------------------------------------------------------

    categorical_columns = [
        "channel",
        "product_family",
        "warranty_status",
        "source",
    ]

    encoder = OneHotEncoder(
        handle_unknown="ignore",
    )

    cat_train = encoder.fit_transform(
        train_df[categorical_columns]
    )

    cat_val = encoder.transform(
        val_df[categorical_columns]
    )

    # --------------------------------------------------------------
    # Engineered request-time features
    # --------------------------------------------------------------

    numeric_train = engineered_features(train_df)
    numeric_val = engineered_features(val_df)

    scaler = StandardScaler()

    numeric_train = scaler.fit_transform(numeric_train)
    numeric_val = scaler.transform(numeric_val)

    numeric_train = csr_matrix(numeric_train)
    numeric_val = csr_matrix(numeric_val)

    # --------------------------------------------------------------
    # Combine
    # --------------------------------------------------------------

    X_train = hstack(
        [
            word_train,
            char_train,
            cat_train,
            numeric_train,
        ]
    ).tocsr()

    X_val = hstack(
        [
            word_val,
            char_val,
            cat_val,
            numeric_val,
        ]
    ).tocsr()

    print("\nFeature matrix:")
    print(f"Train shape: {X_train.shape}")
    print(f"Val shape:   {X_val.shape}")

    # --------------------------------------------------------------
    # Try several C values
    # --------------------------------------------------------------

    results = []

    for C in [0.25, 0.5, 1.0, 1.5, 2.0]:

        model = LinearSVC(
            C=C,
            class_weight="balanced",
            max_iter=10000,

        )

        model.fit(X_train, y_train)

        pred = model.predict(X_val)

        accuracy = evaluate(
            f"Experiment 4 — C={C}",
            pred,
            y_val,
        )

        results.append(
            {
                "C": C,
                "accuracy": accuracy,
            }
        )

    results_df = pd.DataFrame(results)

    print("\n" + "=" * 80)
    print("EXPERIMENT 4 SUMMARY")
    print("=" * 80)

    print(
        results_df.sort_values(
            "accuracy",
            ascending=False,
        ).to_string(index=False)
    )


if __name__ == "__main__":
    main()
