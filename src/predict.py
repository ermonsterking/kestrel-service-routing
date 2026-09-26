import os
import joblib
import pandas as pd


MODEL_PATH = "models/kestrel_router.joblib"
TEST_PATH = "data/test_unlabelled.csv"
OUTPUT_PATH = "outputs/predictions.csv"


os.makedirs("outputs", exist_ok=True)


print("Loading final model...")
model = joblib.load(MODEL_PATH)

print("Loading test data...")
test = pd.read_csv(TEST_PATH)

features = [
    "request_text",
    "channel",
    "product_family",
    "warranty_status",
    "source",
]

print(f"Test rows: {len(test)}")

# Generate predictions
predictions = model.predict(test[features])

# Build submission
submission = pd.DataFrame({
    "request_id": test["request_id"],
    "team": predictions,
})

submission.to_csv(OUTPUT_PATH, index=False)

print("\n" + "=" * 70)
print("PREDICTIONS GENERATED")
print("=" * 70)

print(f"Rows       : {len(submission)}")
print(f"Output     : {OUTPUT_PATH}")
print(f"Columns    : {submission.columns.tolist()}")

print("\nPrediction distribution:")
print(submission["team"].value_counts())

print("\nFirst 10 predictions:")
print(submission.head(10).to_string(index=False))

print("=" * 70)