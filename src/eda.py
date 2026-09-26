import pandas as pd

TRAIN_PATH = "data/train.csv"
TEST_PATH = "data/test_unlabelled.csv"
RESOLUTION_PATH = "data/resolution_log.csv"
TEAMS_PATH = "data/teams.csv"


def inspect_dataframe(name, df):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("Shape:", df.shape)

    print("\nColumns:")
    for col in df.columns:
        print(f"  - {col}: {df[col].dtype}")

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nDuplicate rows:", df.duplicated().sum())


# ---------------------------------------------------------
# Load
# ---------------------------------------------------------

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)
resolution = pd.read_csv(RESOLUTION_PATH)
teams = pd.read_csv(TEAMS_PATH)


# ---------------------------------------------------------
# Basic inspection
# ---------------------------------------------------------

inspect_dataframe("TRAIN", train)
inspect_dataframe("TEST", test)
inspect_dataframe("RESOLUTION LOG", resolution)
inspect_dataframe("TEAMS", teams)


# ---------------------------------------------------------
# Date ranges
# ---------------------------------------------------------

train["created_at_ist"] = pd.to_datetime(train["created_at_ist"])
test["created_at_ist"] = pd.to_datetime(test["created_at_ist"])

print("\n" + "=" * 70)
print("DATE RANGES")
print("=" * 70)

print(
    "Train:",
    train["created_at_ist"].min(),
    "→",
    train["created_at_ist"].max()
)

print(
    "Test:",
    test["created_at_ist"].min(),
    "→",
    test["created_at_ist"].max()
)


# ---------------------------------------------------------
# Team distribution BEFORE normalization
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("RAW TEAM LABEL DISTRIBUTION")
print("=" * 70)

print(
    train["team_label"]
    .value_counts()
    .to_string()
)


# ---------------------------------------------------------
# Team normalization
# ---------------------------------------------------------

TEAM_RENAME_MAP = {
    "Installations": "Installs & Demo",
    "Consumables": "Filters & Consumables",
}

train["normalized_team"] = train["team_label"].replace(
    TEAM_RENAME_MAP
)

print("\n" + "=" * 70)
print("NORMALIZED TEAM DISTRIBUTION")
print("=" * 70)

team_counts = train["normalized_team"].value_counts()

team_summary = pd.DataFrame({
    "count": team_counts,
    "percentage": (team_counts / len(train) * 100).round(2)
})

print(team_summary)


# ---------------------------------------------------------
# Other categorical distributions
# ---------------------------------------------------------

for column in [
    "channel",
    "product_family",
    "warranty_status",
    "source",
]:
    print("\n" + "=" * 70)
    print(f"{column.upper()} DISTRIBUTION")
    print("=" * 70)

    print(train[column].value_counts().to_string())


# ---------------------------------------------------------
# Request text statistics
# ---------------------------------------------------------

train["text_length"] = (
    train["request_text"]
    .fillna("")
    .astype(str)
    .str.len()
)

print("\n" + "=" * 70)
print("REQUEST TEXT STATISTICS")
print("=" * 70)

print(train["text_length"].describe())


# ---------------------------------------------------------
# Resolution analysis
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("RESOLUTION ANALYSIS")
print("=" * 70)

print("Total transfers:", resolution["transfers"].sum())

print(
    "Requests with >=1 transfer:",
    (resolution["transfers"] > 0).sum()
)

print(
    "Transfer rate:",
    round(
        (resolution["transfers"] > 0).mean() * 100,
        2
    ),
    "%"
)

print(
    "Average transfers/request:",
    round(resolution["transfers"].mean(), 4)
)


# ---------------------------------------------------------
# Compare initial vs final team
# ---------------------------------------------------------

resolution["first_team_normalized"] = (
    resolution["first_team"].replace(TEAM_RENAME_MAP)
)

resolution["final_team_normalized"] = (
    resolution["final_team"].replace(TEAM_RENAME_MAP)
)

resolution["team_mismatch"] = (
    resolution["first_team_normalized"]
    != resolution["final_team_normalized"]
)

print(
    "\nInitial team != final team:",
    resolution["team_mismatch"].sum()
)

print(
    "Mismatch rate:",
    round(
        resolution["team_mismatch"].mean() * 100,
        2
    ),
    "%"
)


# ---------------------------------------------------------
# Teams file
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("TEAMS")
print("=" * 70)

print(teams.to_string(index=False))


# ---------------------------------------------------------
# Sample records
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("SAMPLE TRAIN RECORDS")
print("=" * 70)

print(
    train[
        [
            "request_id",
            "created_at_ist",
            "channel",
            "product_family",
            "warranty_status",
            "request_text",
            "source",
            "team_label",
        ]
    ]
    .head(10)
    .to_string(index=False)
)