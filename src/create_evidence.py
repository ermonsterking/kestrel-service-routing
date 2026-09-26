import os
import pandas as pd


os.makedirs("evaluation", exist_ok=True)


results = pd.DataFrame([
    {
        "experiment": "Baseline",
        "features": "Word TF-IDF (1,2)",
        "model": "LinearSVC",
        "validation_accuracy": 0.9409,
    },
    {
        "experiment": "Experiment 2",
        "features": "Word TF-IDF + Character TF-IDF",
        "model": "LinearSVC",
        "validation_accuracy": 0.9566,
    },
    {
        "experiment": "Experiment 3",
        "features": (
            "Word TF-IDF + Character TF-IDF + "
            "channel/product/warranty/source"
        ),
        "model": "LinearSVC",
        "validation_accuracy": 0.9649,
    },
])


results["improvement_vs_baseline_pp"] = (
    results["validation_accuracy"] - results.iloc[0]["validation_accuracy"]
) * 100


results.to_csv(
    "evaluation/model_comparison.csv",
    index=False,
)


with open("evaluation/model_evidence.md", "w") as f:

    f.write("# Kestrel Home — Model Evidence\n\n")

    f.write("## Validation design\n\n")
    f.write(
        "A chronological 80/20 validation split was used so that "
        "validation requests occur after the training period. "
        "This better represents the future test period than a random split.\n\n"
    )

    f.write("Training period: 2025-04-01 to 2026-03-30\n\n")
    f.write("Validation period: 2026-03-30 to 2026-06-30\n\n")

    f.write("## Model comparison\n\n")
    f.write(
        "| Experiment | Features | Model | Accuracy |\n"
        "|---|---|---|---:|\n"
    )

    f.write(
        "| Baseline | Word TF-IDF | LinearSVC | 94.09% |\n"
    )

    f.write(
        "| Experiment 2 | Word + character TF-IDF | "
        "LinearSVC | 95.66% |\n"
    )

    f.write(
        "| Experiment 3 | Word + character TF-IDF + "
        "structured metadata | LinearSVC | 96.49% |\n"
    )

    f.write("\n## Selected model\n\n")
    f.write(
        "Experiment 3 was selected because it achieved 96.49% "
        "chronological validation accuracy, exceeding the client's "
        "90% target by 6.49 percentage points.\n\n"
    )

    f.write("## Remaining errors\n\n")
    f.write(
        "The validation set contained 2,165 requests. "
        "2,089 were classified correctly and 76 were incorrect, "
        "for an error rate of 3.51%.\n\n"
    )

    f.write(
        "The largest confusion pattern was Repairs being predicted "
        "as Filters & Consumables (11 cases). Other recurring "
        "confusions involved Repairs with Billing or Warranty Claims, "
        "and multi-intent requests involving returns, installation, "
        "warranty, or consumables.\n\n"
    )

    f.write("## Data leakage controls\n\n")
    f.write(
        "The model uses request-time fields only: request_text, "
        "channel, product_family, warranty_status, and source. "
        "Post-routing fields such as final_team, transfers, and "
        "resolved_at were excluded from model features.\n"
    )


print("Evidence files created:")
print("  evaluation/model_comparison.csv")
print("  evaluation/model_evidence.md")