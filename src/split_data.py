import pandas as pd


TRAIN_PATH = "data/train.csv"

TEAM_RENAME_MAP = {
    "Installations": "Installs & Demo",
    "Consumables": "Filters & Consumables",
}


def main():

    df = pd.read_csv(TRAIN_PATH)

    # Parse timestamp
    df["created_at_ist"] = pd.to_datetime(df["created_at_ist"])

    # Sort chronologically
    df = df.sort_values("created_at_ist").reset_index(drop=True)

    # Normalize historical team names
    df["target"] = df["team_label"].replace(TEAM_RENAME_MAP)

    # 80/20 chronological split
    split_idx = int(len(df) * 0.80)

    train_df = df.iloc[:split_idx].copy()
    valid_df = df.iloc[split_idx:].copy()

    print("=" * 60)
    print("CHRONOLOGICAL VALIDATION SPLIT")
    print("=" * 60)

    print("\nTraining records:", len(train_df))
    print("Validation records:", len(valid_df))

    print("\nTraining period:")
    print(
        train_df["created_at_ist"].min(),
        "→",
        train_df["created_at_ist"].max()
    )

    print("\nValidation period:")
    print(
        valid_df["created_at_ist"].min(),
        "→",
        valid_df["created_at_ist"].max()
    )

    print("\nTraining distribution:")
    print(train_df["target"].value_counts())

    print("\nValidation distribution:")
    print(valid_df["target"].value_counts())


if __name__ == "__main__":
    main()