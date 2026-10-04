from pathlib import Path
import re
import joblib
import numpy as np
import pandas as pd

from scipy.sparse import hstack, csr_matrix

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC


ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT / "data" / "train.csv"
TEST_PATH = ROOT / "data" / "test_unlabelled.csv"
RESOLUTION_PATH = ROOT / "data" / "resolution_log.csv"

MODEL_PATH = ROOT / "models" / "kestrel_router.joblib"
PREDICTIONS_PATH = ROOT / "outputs" / "predictions.csv"

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)


# =============================================================================
# TEAM NORMALIZATION
# =============================================================================

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


# =============================================================================
# REQUEST-TIME ENGINEERED FEATURES
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
# LOAD DATA
# =============================================================================

print("=" * 80)
print("FINAL MODEL TRAINING — OPERATIONAL TARGET")
print("=" * 80)

print("\nLoading data...")

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)
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

print(f"Historical training rows : {len(df)}")
print(f"Test rows                : {len(test)}")
print(f"Final teams              : {sorted(df['final_team'].unique())}")

assert len(df) == 10822, (
    f"Expected 10822 merged training rows, got {len(df)}"
)

assert len(test) == 2178, (
    f"Expected 2178 test rows, got {len(test)}"
)

assert df["final_team"].notna().all(), (
    "Missing final_team values detected"
)

assert test["request_id"].is_unique, (
    "Duplicate request_id values in test set"
)


# =============================================================================
# TEXT FEATURES
# =============================================================================

print("\nBuilding TF-IDF features...")

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
    df["request_text"].fillna("")
)

word_test = word.transform(
    test["request_text"].fillna("")
)

char_train = char.fit_transform(
    df["request_text"].fillna("")
)

char_test = char.transform(
    test["request_text"].fillna("")
)


# =============================================================================
# CATEGORICAL FEATURES
# =============================================================================

print("Building categorical features...")

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
    df[categorical_columns]
)

cat_test = encoder.transform(
    test[categorical_columns]
)


# =============================================================================
# ENGINEERED FEATURES
# =============================================================================

print("Building engineered request-time features...")

numeric_train = engineered_features(df)
numeric_test = engineered_features(test)

scaler = StandardScaler()

numeric_train = scaler.fit_transform(numeric_train)
numeric_test = scaler.transform(numeric_test)

numeric_train = csr_matrix(numeric_train)
numeric_test = csr_matrix(numeric_test)


# =============================================================================
# COMBINE FEATURES
# =============================================================================

X_train = hstack(
    [
        word_train,
        char_train,
        cat_train,
        numeric_train,
    ]
).tocsr()

X_test = hstack(
    [
        word_test,
        char_test,
        cat_test,
        numeric_test,
    ]
).tocsr()

y = df["final_team"]

print("\nFeature matrix:")
print(f"Train shape: {X_train.shape}")
print(f"Test shape : {X_test.shape}")


# =============================================================================
# FINAL MODEL
# =============================================================================

print("\nTraining final LinearSVC...")
print("Target: final_team")
print("C: 2.0")
print("class_weight: balanced")
print("max_iter: 10000")

model = LinearSVC(
    C=2.0,
    class_weight="balanced",
    max_iter=10000,
)

model.fit(X_train, y)


# =============================================================================
# TEST PREDICTIONS
# =============================================================================

print("\nGenerating test predictions...")

test_predictions = model.predict(X_test)

predictions = pd.DataFrame(
    {
        "request_id": test["request_id"],
        "team": test_predictions,
    }
)

assert len(predictions) == 2178
assert predictions["request_id"].is_unique
assert predictions["team"].notna().all()

expected_teams = set(df["final_team"].unique())

unexpected = set(predictions["team"]) - expected_teams

assert not unexpected, (
    f"Unexpected predicted teams: {unexpected}"
)


# =============================================================================
# SAVE MODEL ARTIFACT
# =============================================================================

artifact = {
    "model": model,
    "word_vectorizer": word,
    "char_vectorizer": char,
    "categorical_encoder": encoder,
    "numeric_scaler": scaler,
    "feature_version": "experiment_4_final_team_v1",
    "target": "final_team",
    "C": 2.0,
    "class_weight": "balanced",
    "max_iter": 10000,
    "categorical_columns": categorical_columns,
}

joblib.dump(
    artifact,
    MODEL_PATH,
)


# =============================================================================
# SAVE PREDICTIONS
# =============================================================================

predictions.to_csv(
    PREDICTIONS_PATH,
    index=False,
)


# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("FINAL MODEL COMPLETE")
print("=" * 80)

print(f"Training rows : {len(df)}")
print(f"Test rows     : {len(test)}")
print(f"Feature shape : {X_train.shape}")
print(f"Classes       : {model.classes_.tolist()}")

print("\nPrediction distribution:")
print(
    predictions["team"]
    .value_counts()
    .to_string()
)

print(f"\nModel saved to:")
print(f"  {MODEL_PATH}")

print(f"\nPredictions saved to:")
print(f"  {PREDICTIONS_PATH}")

print("=" * 80)
