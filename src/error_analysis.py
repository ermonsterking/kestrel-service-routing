import re
from pathlib import Path

import pandas as pd
from scipy.sparse import hstack, csr_matrix

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT / "data" / "train.csv"
RESOLUTION_PATH = ROOT / "data" / "resolution_log.csv"
EVAL_DIR = ROOT / "evaluation"

EVAL_DIR.mkdir(exist_ok=True)


TEAM_RENAME_MAP = {
    "Installations": "Installs & Demo",
    "Consumables": "Filters & Consumables",
}


# --------------------------------------------------
# Intent patterns
# Exact patterns used by Experiment 4
# --------------------------------------------------

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
# --------------------------------------------------
# Feature engineering
# Exact structure used by Experiment 4
# --------------------------------------------------

def engineered_features(df):
    text = df["request_text"].fillna("").astype(str).str.lower()

    features = pd.DataFrame(index=df.index)

    features["text_length"] = text.str.len()
    features["word_count"] = text.str.split().str.len()
    features["question_count"] = text.str.count(r"\?")
    features["exclamation_count"] = text.str.count(r"!")
    features["digit_count"] = text.str.count(r"\d")
    features["rupee_count"] = text.str.count("₹")

    features["order_id_indicator"] = text.apply(
        lambda x: int(bool(re.search(r"\bko\d+\b", x)))
    )

    for intent, patterns in INTENT_PATTERNS.items():
        features[f"{intent}_count"] = text.apply(
            lambda x: sum(
                len(re.findall(pattern, x))
                for pattern in patterns
            )
        )

    return features


# --------------------------------------------------
# Build Experiment 4 features
# --------------------------------------------------

def build_features(
    train_df,
    valid_df,
):
    word_vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
    )

    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=2,
        sublinear_tf=True,
    )

    categorical_encoder = OneHotEncoder(
        handle_unknown="ignore"
    )

    numeric_scaler = StandardScaler()

    word_train = word_vectorizer.fit_transform(
        train_df["request_text"].fillna("").astype(str)
    )

    word_valid = word_vectorizer.transform(
        valid_df["request_text"].fillna("").astype(str)
    )

    char_train = char_vectorizer.fit_transform(
        train_df["request_text"].fillna("").astype(str)
    )

    char_valid = char_vectorizer.transform(
        valid_df["request_text"].fillna("").astype(str)
    )

    categorical_columns = [
        "channel",
        "product_family",
        "warranty_status",
        "source",
    ]

    cat_train = categorical_encoder.fit_transform(
        train_df[categorical_columns].fillna("")
    )

    cat_valid = categorical_encoder.transform(
        valid_df[categorical_columns].fillna("")
    )

    numeric_train_df = engineered_features(train_df)
    numeric_valid_df = engineered_features(valid_df)

    numeric_train = numeric_scaler.fit_transform(
        numeric_train_df
    )

    numeric_valid = numeric_scaler.transform(
        numeric_valid_df
    )

    X_train = hstack(
        [
            word_train,
            char_train,
            cat_train,
            csr_matrix(numeric_train),
        ]
    ).tocsr()

    X_valid = hstack(
        [
            word_valid,
            char_valid,
            cat_valid,
            csr_matrix(numeric_valid),
        ]
    ).tocsr()

    return X_train, X_valid


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("Loading data...")

    train = pd.read_csv(TRAIN_PATH)
    resolution = pd.read_csv(RESOLUTION_PATH)

    train["created_at_ist"] = pd.to_datetime(
        train["created_at_ist"]
    )

    resolution["final_team"] = resolution[
        "final_team"
    ].replace(TEAM_RENAME_MAP)

    resolution["first_team"] = resolution[
        "first_team"
    ].replace(TEAM_RENAME_MAP)

    # --------------------------------------------------
    # Merge final operational target
    # --------------------------------------------------

    df = train.merge(
        resolution[
            [
                "request_id",
                "first_team",
                "final_team",
                "transfers",
            ]
        ],
        on="request_id",
        how="inner",
        validate="one_to_one",
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

    print(
        f"Training rows: {len(train_df)}"
    )

    print(
        f"Validation rows: {len(valid_df)}"
    )

    print(
        "Training period:",
        train_df["created_at_ist"].min(),
        "->",
        train_df["created_at_ist"].max(),
    )

    print(
        "Validation period:",
        valid_df["created_at_ist"].min(),
        "->",
        valid_df["created_at_ist"].max(),
    )

    # --------------------------------------------------
    # Build features
    # --------------------------------------------------

    print("\nBuilding Experiment 4 features...")

    X_train, X_valid = build_features(
        train_df,
        valid_df,
    )

    print(
        "Feature matrix:",
        X_train.shape
    )

    # --------------------------------------------------
    # Target
    # --------------------------------------------------

    y_train = train_df["final_team"]
    y_valid = valid_df["final_team"]

    # --------------------------------------------------
    # Final Experiment 4 model
    # --------------------------------------------------

    model = LinearSVC(
        class_weight="balanced",
        C=2.0,
        max_iter=10000,
    )

    print("\nTraining final operational model...")

    model.fit(
        X_train,
        y_train,
    )

    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    predictions = model.predict(
        X_valid
    )

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    results = valid_df.copy()

    results["predicted_team"] = predictions

    results["correct"] = (
        results["final_team"]
        == results["predicted_team"]
    )

    # Historical bot prediction
    results["historical_bot"] = (
        results["team_label"]
        .replace(TEAM_RENAME_MAP)
    )

    results["bot_correct"] = (
        results["historical_bot"]
        == results["final_team"]
    )

    # --------------------------------------------------
    # Overall metrics
    # --------------------------------------------------

    accuracy = accuracy_score(
        y_valid,
        predictions,
    )

    print("\n" + "=" * 80)
    print("FINAL OPERATIONAL ERROR ANALYSIS")
    print("=" * 80)

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )

    print(
        f"Correct: {results['correct'].sum()}"
    )

    print(
        f"Incorrect: {(~results['correct']).sum()}"
    )

    print(
        f"Error rate: {(~results['correct']).mean():.2%}"
    )

    # --------------------------------------------------
    # Classification report
    # --------------------------------------------------

    print("\n" + "-" * 80)
    print("CLASSIFICATION REPORT")
    print("-" * 80)

    report = classification_report(
        y_valid,
        predictions,
        digits=4,
    )

    print(report)

    # --------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------

    labels = sorted(
        y_valid.unique()
    )

    cm = confusion_matrix(
        y_valid,
        predictions,
        labels=labels,
    )

    cm_df = pd.DataFrame(
        cm,
        index=labels,
        columns=labels,
    )

    print("\n" + "-" * 80)
    print("CONFUSION MATRIX")
    print("-" * 80)

    print(cm_df)

    cm_df.to_csv(
        EVAL_DIR / "final_model_confusion_matrix.csv"
    )

    # --------------------------------------------------
    # Top confusion pairs
    # --------------------------------------------------

    errors = results[
        ~results["correct"]
    ].copy()

    confusion_pairs = (
        errors
        .groupby(
            [
                "final_team",
                "predicted_team",
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            "count",
            ascending=False,
        )
    )

    print("\n" + "-" * 80)
    print("TOP CONFUSION PAIRS")
    print("-" * 80)

    print(
        confusion_pairs
        .head(20)
        .to_string(index=False)
    )

    confusion_pairs.to_csv(
        EVAL_DIR / "final_model_confusion_pairs.csv",
        index=False,
    )

    # --------------------------------------------------
    # Errors by channel
    # --------------------------------------------------

    channel_stats = (
        results
        .groupby("channel")
        .agg(
            requests=("request_id", "count"),
            errors=("correct", lambda x: (~x).sum()),
        )
    )

    channel_stats["error_rate"] = (
        channel_stats["errors"]
        / channel_stats["requests"]
    )

    print("\n" + "-" * 80)
    print("ERRORS BY CHANNEL")
    print("-" * 80)

    print(
        channel_stats
        .sort_values(
            "error_rate",
            ascending=False,
        )
        .to_string()
    )

    channel_stats.to_csv(
        EVAL_DIR / "final_model_errors_by_channel.csv"
    )

    # --------------------------------------------------
    # Errors by product family
    # --------------------------------------------------

    product_stats = (
        results
        .groupby("product_family")
        .agg(
            requests=("request_id", "count"),
            errors=("correct", lambda x: (~x).sum()),
        )
    )

    product_stats["error_rate"] = (
        product_stats["errors"]
        / product_stats["requests"]
    )

    print("\n" + "-" * 80)
    print("ERRORS BY PRODUCT FAMILY")
    print("-" * 80)

    print(
        product_stats
        .sort_values(
            "error_rate",
            ascending=False,
        )
        .to_string()
    )

    product_stats.to_csv(
        EVAL_DIR / "final_model_errors_by_product.csv"
    )

    # --------------------------------------------------
    # Errors by warranty status
    # --------------------------------------------------

    warranty_stats = (
        results
        .groupby("warranty_status")
        .agg(
            requests=("request_id", "count"),
            errors=("correct", lambda x: (~x).sum()),
        )
    )

    warranty_stats["error_rate"] = (
        warranty_stats["errors"]
        / warranty_stats["requests"]
    )

    print("\n" + "-" * 80)
    print("ERRORS BY WARRANTY STATUS")
    print("-" * 80)

    print(
        warranty_stats
        .sort_values(
            "error_rate",
            ascending=False,
        )
        .to_string()
    )

    warranty_stats.to_csv(
        EVAL_DIR / "final_model_errors_by_warranty.csv"
    )

    # --------------------------------------------------
    # Historical bot vs model correction analysis
    # --------------------------------------------------

    old_bot_wrong_model_correct = results[
        (~results["bot_correct"])
        & (results["correct"])
    ]

    old_bot_correct_model_wrong = results[
        (results["bot_correct"])
        & (~results["correct"])
    ]

    both_wrong = results[
        (~results["bot_correct"])
        & (~results["correct"])
    ]

    both_correct = results[
        (results["bot_correct"])
        & (results["correct"])
    ]

    print("\n" + "-" * 80)
    print("HISTORICAL BOT VS MODEL")
    print("-" * 80)

    print(
        "Old bot wrong -> model correct:",
        len(old_bot_wrong_model_correct),
    )

    print(
        "Old bot correct -> model wrong:",
        len(old_bot_correct_model_wrong),
    )

    print(
        "Both wrong:",
        len(both_wrong),
    )

    print(
        "Both correct:",
        len(both_correct),
    )

    # --------------------------------------------------
    # Save correction analysis
    # --------------------------------------------------

    correction_rows = []

    for _, row in results.iterrows():

        if not row["bot_correct"] and row["correct"]:
            category = "old_bot_wrong_model_correct"

        elif row["bot_correct"] and not row["correct"]:
            category = "old_bot_correct_model_wrong"

        elif not row["bot_correct"] and not row["correct"]:
            category = "both_wrong"

        else:
            category = "both_correct"

        correction_rows.append(
            {
                "request_id": row["request_id"],
                "request_text": row["request_text"],
                "product_family": row["product_family"],
                "warranty_status": row["warranty_status"],
                "channel": row["channel"],
                "source": row["source"],
                "historical_bot": row["historical_bot"],
                "final_team": row["final_team"],
                "predicted_team": row["predicted_team"],
                "transfers": row["transfers"],
                "category": category,
            }
        )

    correction_df = pd.DataFrame(
        correction_rows
    )

    correction_df.to_csv(
        EVAL_DIR / "bot_vs_model_cases.csv",
        index=False,
    )

    # --------------------------------------------------
    # Save all validation predictions
    # --------------------------------------------------

    results[
        [
            "request_id",
            "request_text",
            "product_family",
            "warranty_status",
            "channel",
            "source",
            "historical_bot",
            "final_team",
            "predicted_team",
            "transfers",
            "correct",
            "bot_correct",
        ]
    ].to_csv(
        EVAL_DIR / "final_model_validation_predictions.csv",
        index=False,
    )

    # --------------------------------------------------
    # Representative hard cases
    #
    # Prioritize model errors with:
    # - short/vague text
    # - disagreement with historical bot
    # - transfers
    # --------------------------------------------------

    errors["text_length"] = (
        errors["request_text"]
        .fillna("")
        .astype(str)
        .str.len()
    )

    hard_cases = (
        errors
        .sort_values(
            [
                "transfers",
                "text_length",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .head(30)
    )

    hard_cases[
        [
            "request_id",
            "request_text",
            "product_family",
            "warranty_status",
            "channel",
            "historical_bot",
            "final_team",
            "predicted_team",
            "transfers",
        ]
    ].to_csv(
        EVAL_DIR / "representative_hard_cases.csv",
        index=False,
    )

    
    # --------------------------------------------------
    # Markdown evidence
    # --------------------------------------------------

    model_correct = int(results["correct"].sum())
    model_wrong = int((~results["correct"]).sum())

    bot_correct = int(results["bot_correct"].sum())
    bot_wrong = int((~results["bot_correct"]).sum())

    old_bot_wrong_model_correct = len(old_bot_wrong_model_correct)
    old_bot_correct_model_wrong = len(old_bot_correct_model_wrong)
    both_wrong_count = len(both_wrong)
    both_correct_count = len(both_correct)
    evidence_lines = [
        "# Kestrel Home — Final Model Error Analysis",
        "",
        "## 1. Validation Result",
        "",
        "The final operational model was evaluated on a chronological holdout using",
        "`final_team` as the operational target.",
        "",
        f"- Validation rows: **{len(results):,}**",
        f"- Correct predictions: **{model_correct:,}**",
        f"- Incorrect predictions: **{model_wrong:,}**",
        f"- Accuracy: **{accuracy:.2%}**",
        f"- Error rate: **{1 - accuracy:.2%}**",
        "",
        "The historical routing bot was evaluated on the same validation rows.",
        "",
        f"- Historical bot correct: **{bot_correct:,}**",
        f"- Historical bot incorrect: **{bot_wrong:,}**",
        f"- Historical bot accuracy: **{bot_correct / len(results):.2%}**",
        "",
        "## 2. Classification Performance",
        "",
        "```text",
        report,
        "```",
        "",
        "## 3. Confusion Matrix",
        "",
        "The complete confusion matrix is available in:",
        "",
        "`evaluation/final_model_confusion_matrix.csv`",
        "",
        "Detailed confusion-pair analysis is available in:",
        "",
        "`evaluation/final_model_confusion_pairs.csv`",
        "",
        "## 4. Error Breakdown",
        "",
        "Error breakdowns are available in:",
        "",
        "- `evaluation/final_model_errors_by_channel.csv`",
        "- `evaluation/final_model_errors_by_product.csv`",
        "- `evaluation/final_model_errors_by_warranty.csv`",
        "",
        "## 5. Historical Bot vs Final Model",
        "",
        "On the same chronological validation set:",
        "",
        f"- Old bot wrong → model correct: **{old_bot_wrong_model_correct:,}**",
        f"- Old bot correct → model wrong: **{old_bot_correct_model_wrong:,}**",
        f"- Both wrong: **{both_wrong_count:,}**",
        f"- Both correct: **{both_correct_count:,}**",
        "",
        "The key business comparison is therefore between the historical bot's",
        "agreement with `final_team` and the new model's agreement with `final_team`.",
        "",
        "## 6. Representative Hard Cases",
        "",
        "Representative difficult validation cases are saved in:",
        "",
        "`evaluation/representative_hard_cases.csv`",
        "",
        "These cases prioritize model errors involving transfers and short or vague",
        "request text.",
        "",
        "## 7. Leakage Controls",
        "",
        "The model uses only information available at request creation time:",
        "",
        "- request text",
        "- channel",
        "- product family",
        "- warranty status",
        "- source",
        "- request-text-derived features",
        "",
        "The following post-routing fields were not used as model features:",
        "",
        "- `final_team`",
        "- `first_team`",
        "- `transfers`",
        "- `resolved_at`",
        "",
        "The historical `team_label` is treated as the historical bot decision and",
        "benchmark, not as the operational target.",
        "",
        "## 8. Generated Evidence Files",
        "",
        "The analysis generated:",
        "",
        "- `final_model_confusion_matrix.csv`",
        "- `final_model_confusion_pairs.csv`",
        "- `final_model_errors_by_channel.csv`",
        "- `final_model_errors_by_product.csv`",
        "- `final_model_errors_by_warranty.csv`",
        "- `bot_vs_model_cases.csv`",
        "- `final_model_validation_predictions.csv`",
        "- `representative_hard_cases.csv`",
        "- `final_error_analysis.md`",
    ]

    evidence = "\n".join(evidence_lines)

    with open(
        EVAL_DIR / "final_error_analysis.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(evidence)

    print()
    print("=" * 70)
    print("FINAL ERROR ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Validation accuracy: {accuracy:.2%}")
    print(f"Historical bot accuracy: {bot_correct / len(results):.2%}")
    print(f"Model errors: {model_wrong:,}")
    print(
        f"Old bot wrong -> model correct: "
        f"{old_bot_wrong_model_correct:,}"
    )
    print(
        f"Old bot correct -> model wrong: "
        f"{old_bot_correct_model_wrong:,}"
    )
    print(f"Both wrong: {both_wrong_count:,}")
    print(f"Both correct: {both_correct_count:,}")
    print()
    print("Generated evidence files:")

    for path in sorted(EVAL_DIR.glob("*")):
        print(f"  - {path.name}")

if __name__ == "__main__":
    main()