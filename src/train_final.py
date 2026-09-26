import os
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC


DATA_PATH = "data/train.csv"
MODEL_PATH = "models/kestrel_router.joblib"

os.makedirs("models", exist_ok=True)


def normalize_team(label):
    mapping = {
        "Installations": "Installs & Demo",
        "Consumables": "Filters & Consumables",
    }
    return mapping.get(label, label)


print("Loading training data...")
df = pd.read_csv(DATA_PATH)

df["team_label"] = df["team_label"].map(normalize_team)

print(f"Training rows: {len(df)}")
print(f"Classes: {sorted(df['team_label'].unique())}")


# Text features
word_tfidf = TfidfVectorizer(
    analyzer="word",
    ngram_range=(1, 2),
    min_df=2,
    sublinear_tf=True,
)

char_tfidf = TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(3, 5),
    min_df=2,
    sublinear_tf=True,
)


# Combine text + structured request-time features
preprocessor = ColumnTransformer(
    transformers=[
        (
            "word_tfidf",
            word_tfidf,
            "request_text",
        ),
        (
            "char_tfidf",
            char_tfidf,
            "request_text",
        ),
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            [
                "channel",
                "product_family",
                "warranty_status",
                "source",
            ],
        ),
    ]
)


model = Pipeline(
    steps=[
        ("features", preprocessor),
        (
            "classifier",
            LinearSVC(
                C=1.0,
                class_weight="balanced",
            ),
        ),
    ]
)


X = df[
    [
        "request_text",
        "channel",
        "product_family",
        "warranty_status",
        "source",
    ]
]

y = df["team_label"]


print("\nTraining final model...")
model.fit(X, y)

joblib.dump(model, MODEL_PATH)

print("\n" + "=" * 70)
print("FINAL MODEL TRAINED")
print("=" * 70)
print(f"Training rows : {len(df)}")
print(f"Classes       : {model.classes_.tolist()}")
print(f"Saved to      : {MODEL_PATH}")
print("=" * 70)