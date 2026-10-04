from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT / "data" / "train.csv"
RESOLUTION_PATH = ROOT / "data" / "resolution_log.csv"
TEAMS_PATH = ROOT / "data" / "teams.csv"

OUTPUT_DIR = ROOT / "evaluation"
OUTPUT_DIR.mkdir(exist_ok=True)


def normalize_team(label):
    """Map historical team names to the current operational names."""
    if pd.isna(label):
        return label

    label = str(label).strip()

    mapping = {
        "Installations": "Installs & Demo",
        "Installs & Demo": "Installs & Demo",
        "Consumables": "Filters & Consumables",
        "Filters & Consumables": "Filters & Consumables",
    }

    return mapping.get(label, label)


def main():

    train = pd.read_csv(TRAIN_PATH)
    resolution = pd.read_csv(RESOLUTION_PATH)
    teams = pd.read_csv(TEAMS_PATH)

    print("=" * 80)
    print("KESTREL HOME — OPERATIONAL TARGET AUDIT")
    print("=" * 80)

    print("\nDataset sizes")
    print("-" * 80)
    print(f"Train rows:       {len(train):,}")
    print(f"Resolution rows:  {len(resolution):,}")
    print(f"Teams rows:       {len(teams):,}")

    # ------------------------------------------------------------------
    # Normalize historical labels
    # ------------------------------------------------------------------

    train["team_label_norm"] = train["team_label"].map(normalize_team)
    resolution["first_team_norm"] = resolution["first_team"].map(normalize_team)
    resolution["final_team_norm"] = resolution["final_team"].map(normalize_team)

    # ------------------------------------------------------------------
    # Validate request IDs
    # ------------------------------------------------------------------

    print("\nRequest ID checks")
    print("-" * 80)

    print(
        "Train unique request IDs:",
        train["request_id"].nunique()
    )

    print(
        "Resolution unique request IDs:",
        resolution["request_id"].nunique()
    )

    print(
        "Train IDs missing from resolution:",
        len(set(train["request_id"]) - set(resolution["request_id"]))
    )

    print(
        "Resolution IDs missing from train:",
        len(set(resolution["request_id"]) - set(train["request_id"]))
    )

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    df = train.merge(
        resolution[
            [
                "request_id",
                "first_team_norm",
                "final_team_norm",
                "transfers",
                "resolved_at",
            ]
        ],
        on="request_id",
        how="left",
        validate="one_to_one",
    )

    print("\nMerged dataset:", df.shape)

    # ------------------------------------------------------------------
    # Validate team_label vs first_team
    # ------------------------------------------------------------------

    df["bot_matches_first"] = (
        df["team_label_norm"] == df["first_team_norm"]
    )

    print("\nHistorical bot label vs first_team")
    print("-" * 80)

    print(
        df["bot_matches_first"].value_counts(dropna=False)
    )

    print(
        "Agreement:",
        f"{df['bot_matches_first'].mean() * 100:.2f}%"
    )

    # ------------------------------------------------------------------
    # Historical bot vs final operational outcome
    # ------------------------------------------------------------------

    df["bot_matches_final"] = (
        df["team_label_norm"] == df["final_team_norm"]
    )

    df["needed_transfer"] = (
        df["team_label_norm"] != df["final_team_norm"]
    )

    print("\nHistorical bot vs final operational outcome")
    print("-" * 80)

    bot_final_accuracy = df["bot_matches_final"].mean()

    print(
        f"Bot agreement with final_team: "
        f"{bot_final_accuracy * 100:.2f}%"
    )

    print(
        f"Historical mismatch: "
        f"{(1 - bot_final_accuracy) * 100:.2f}%"
    )

    print(
        "Mismatched requests:",
        int(df["needed_transfer"].sum())
    )

    # ------------------------------------------------------------------
    # Final team distribution
    # ------------------------------------------------------------------

    print("\nFinal-team distribution")
    print("-" * 80)

    final_distribution = (
        df["final_team_norm"]
        .value_counts()
        .rename_axis("final_team")
        .reset_index(name="count")
    )

    final_distribution["percentage"] = (
        final_distribution["count"] / len(df) * 100
    )

    print(final_distribution.to_string(index=False))

    # ------------------------------------------------------------------
    # Initial bot distribution
    # ------------------------------------------------------------------

    print("\nHistorical bot-label distribution")
    print("-" * 80)

    bot_distribution = (
        df["team_label_norm"]
        .value_counts()
        .rename_axis("team_label")
        .reset_index(name="count")
    )

    bot_distribution["percentage"] = (
        bot_distribution["count"] / len(df) * 100
    )

    print(bot_distribution.to_string(index=False))

    # ------------------------------------------------------------------
    # Transition matrix
    # ------------------------------------------------------------------

    transition = pd.crosstab(
        df["team_label_norm"],
        df["final_team_norm"],
        margins=True,
    )

    print("\nHistorical routing transition matrix")
    print("-" * 80)
    print(transition.to_string())

    transition.to_csv(
        OUTPUT_DIR / "team_label_to_final_team.csv"
    )

    # ------------------------------------------------------------------
    # Mismatch matrix only
    # ------------------------------------------------------------------

    mismatches = df[
        df["team_label_norm"] != df["final_team_norm"]
    ].copy()

    mismatch_matrix = pd.crosstab(
        mismatches["team_label_norm"],
        mismatches["final_team_norm"],
        margins=True,
    )

    print("\nMismatch matrix")
    print("-" * 80)
    print(mismatch_matrix.to_string())

    mismatch_matrix.to_csv(
        OUTPUT_DIR / "routing_mismatch_matrix.csv"
    )

    # ------------------------------------------------------------------
    # Mismatch by initial team
    # ------------------------------------------------------------------

    by_initial_team = (
        df.groupby("team_label_norm")
        .agg(
            requests=("request_id", "count"),
            mismatches=("needed_transfer", "sum"),
            avg_transfers=("transfers", "mean"),
        )
        .reset_index()
    )

    by_initial_team["mismatch_rate"] = (
        by_initial_team["mismatches"]
        / by_initial_team["requests"]
    )

    by_initial_team = by_initial_team.sort_values(
        "mismatch_rate",
        ascending=False,
    )

    print("\nMismatch rate by historical bot team")
    print("-" * 80)
    print(by_initial_team.to_string(index=False))

    by_initial_team.to_csv(
        OUTPUT_DIR / "mismatch_by_initial_team.csv",
        index=False,
    )

    # ------------------------------------------------------------------
    # Transfer distribution
    # ------------------------------------------------------------------

    print("\nTransfer distribution")
    print("-" * 80)

    print(
        df["transfers"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    # ------------------------------------------------------------------
    # Save merged audit data locally
    # ------------------------------------------------------------------

    audit_columns = [
        "request_id",
        "created_at_ist",
        "channel",
        "product_family",
        "warranty_status",
        "request_text",
        "source",
        "team_label",
        "team_label_norm",
        "first_team_norm",
        "final_team_norm",
        "transfers",
        "resolved_at",
        "bot_matches_final",
    ]

    df[audit_columns].to_csv(
        OUTPUT_DIR / "operational_target_audit.csv",
        index=False,
    )

    print("\nFiles written:")
    print("  evaluation/team_label_to_final_team.csv")
    print("  evaluation/routing_mismatch_matrix.csv")
    print("  evaluation/mismatch_by_initial_team.csv")
    print("  evaluation/operational_target_audit.csv")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()