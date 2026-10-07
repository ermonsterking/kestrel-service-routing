import re
import pandas as pd
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

TRAIN_PATH = "data/train.csv"
OUT_DIR = Path("evaluation/quality_labels")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(TRAIN_PATH)

df["request_text"] = (
    df["request_text"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df["text_lower"] = df["request_text"].str.lower()

# ============================================================
# PRODUCT DETECTION
# ============================================================

PRODUCT_PATTERNS = {
    "Water Purifier": [
        r"\bwater purifier\b",
        r"\bpurifier\b",
        r"\bro purifier\b",
    ],
    "Air Fryer": [
        r"\bair fryer\b",
        r"\bairfryer\b",
    ],
    "Mixer Grinder": [
        r"\bmixer grinder\b",
        r"\bmixer\b",
        r"\bgrinder\b",
    ],
    "Induction Cooktop": [
        r"\binduction cooktop\b",
        r"\binduction\b",
        r"\bcooktop\b",
    ],
    "Room Heater": [
        r"\broom heater\b",
        r"\bheater\b",
    ],
    "Ceiling Fan": [
        r"\bceiling fan\b",
        r"\bfan\b",
    ],
    "Robot Vacuum": [
        r"\brobot vacuum\b",
        r"\brobotic vacuum\b",
        r"\bvaccum\b",
        r"\bvacuum\b",
    ],
}


def detect_products(text):
    found = []

    for product, patterns in PRODUCT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                found.append(product)
                break

    return found


df["mentioned_products"] = df["text_lower"].apply(detect_products)

# ============================================================
# STRONG ROUTING SIGNALS
# ============================================================

INTENT_PATTERNS = {
    "Repairs": [
        r"\bnot working\b",
        r"\bdoesn't work\b",
        r"\bdoesnt work\b",
        r"\bnot turning on\b",
        r"\bnot turn on\b",
        r"\bnot heating\b",
        r"\bnot cooling\b",
        r"\bbroken\b",
        r"\bfault\b",
        r"\bfaulty\b",
        r"\brepair\b",
        r"\bleaking\b",
        r"\bleak\b",
        r"\berror code\b",
        r"\berror\b",
        r"\bnoise\b",
        r"\bloud noise\b",
        r"\bburnt smell\b",
        r"\boverheating\b",
        r"\btripping\b",
        r"\bstopped working\b",
        r"\bstopped\b",
        r"\bnot starting\b",
    ],

    "Billing": [
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
        r"\bpayment deducted\b",
        r"\bpayment failed\b",
        r"\bpayment not\b",
    ],

    "Warranty Claims": [
        r"\bwarranty\b",
        r"\bwarranty claim\b",
        r"\bwarranty certificate\b",
        r"\bwarranty rejected\b",
        r"\bshield\b",
        r"\bshield plan\b",
        r"\bcoverage\b",
        r"\bclaim status\b",
        r"\bclaim\b",
    ],

    "Returns & Replacement": [
        r"\breturn\b",
        r"\breplacement\b",
        r"\breplace\b",
        r"\bexchange\b",
        r"\bdamaged\b",
        r"\bscratch(?:ed)?\b",
        r"\bwrong product\b",
        r"\bwrong item\b",
        r"\bmissing parts\b",
        r"\bmissing\b",
        r"\bincomplete\b",
        r"\breturn pickup\b",
        r"\bcancel.*order\b",
    ],

    "Filters & Consumables": [
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

    "Installs & Demo": [
        r"\binstallation\b",
        r"\binstall\b",
        r"\binstalled\b",
        r"\breschedule installation\b",
        r"\binstallation pending\b",
        r"\bdemo\b",
        r"\bwall mount\b",
        r"\bwall mounting\b",
        r"\binstaller\b",
    ],

    "Product Advice": [
        r"\bhow to\b",
        r"\bhow do i\b",
        r"\bhow can i\b",
        r"\bmanual\b",
        r"\brecipe\b",
        r"\busage\b",
        r"\bdifference\b",
        r"\bguide\b",
        r"\bbest settings\b",
        r"\bsettings\b",
        r"\bhow does\b",
        r"\bsafe for\b",
        r"\bsafety\b",
        r"\bpower consumption\b",
        r"\bwhich .* right\b",
        r"\brecommend\b",
    ],
}


def detect_intents(text):
    detected = []

    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                detected.append(intent)
                break

    return detected


df["detected_intents"] = df["text_lower"].apply(detect_intents)

# ============================================================
# GENERIC / WEAK SIGNALS
# These NEVER create a routing intent by themselves.
# ============================================================

GENERIC_PATTERNS = [
    r"\bhelp\b",
    r"\bquery\b",
    r"\bproblem\b",
    r"\bissue\b",
    r"\bcomplaint\b",
    r"\bservice request\b",
    r"\bplease call\b",
    r"\bcall back\b",
    r"\bkindly resolve\b",
    r"\bneed assistance\b",
    r"\bsomeone contact me\b",
    r"\bnot happy\b",
    r"\bdisappointed\b",
    r"\burgent\b",
    r"\basap\b",
]


def generic_count(text):
    return sum(
        bool(re.search(pattern, text))
        for pattern in GENERIC_PATTERNS
    )


df["generic_count"] = df["text_lower"].apply(generic_count)

# ============================================================
# MULTI-INTENT CONNECTORS
# ============================================================

MULTI_CONNECTORS = [
    r"\band\b",
    r"\balso\b",
    r"\bas well as\b",
    r"\bplus\b",
    r"\btogether with\b",
    r"\badditionally\b",
    r"\bneed.*also\b",
]


def has_multi_connector(text):
    return any(
        re.search(pattern, text)
        for pattern in MULTI_CONNECTORS
    )


df["has_multi_connector"] = df["text_lower"].apply(
    has_multi_connector
)

# ============================================================
# PRODUCT / METADATA CONFLICT
# ============================================================

def product_conflict(row):
    mentioned = row["mentioned_products"]

    if not mentioned:
        return False

    metadata_product = row["product_family"]

    return metadata_product not in mentioned


df["product_text_conflict"] = df.apply(
    product_conflict,
    axis=1,
)

# ============================================================
# QUALITY CLASSIFICATION V2.1
# ============================================================

def classify_quality(row):

    intents = row["detected_intents"]

    # --------------------------------------------------------
    # 1. DATA CONFLICT
    # --------------------------------------------------------

    if row["product_text_conflict"]:
        return "DATA_CONFLICT"

    # --------------------------------------------------------
    # 2. MULTI-INTENT
    #
    # Multiple strong intents always take priority over
    # ROUTABLE / clarification.
    # --------------------------------------------------------

    if len(intents) >= 2:
        return "MULTI_INTENT"

    # --------------------------------------------------------
    # 3. ROUTABLE
    #
    # One strong intent is enough even when the request also
    # contains generic words such as help/problem/complaint.
    # --------------------------------------------------------

    if len(intents) == 1:
        return "ROUTABLE"

    # --------------------------------------------------------
    # 4. NEEDS CLARIFICATION
    #
    # No strong routing signal exists.
    # --------------------------------------------------------

    return "NEEDS_CLARIFICATION"


df["quality_label"] = df.apply(
    classify_quality,
    axis=1,
)

# ============================================================
# SAVE
# ============================================================

output_columns = [
    "request_id",
    "request_text",
    "product_family",
    "warranty_status",
    "channel",
    "source",
    "mentioned_products",
    "detected_intents",
    "generic_count",
    "has_multi_connector",
    "product_text_conflict",
    "quality_label",
]

result = df[output_columns].copy()

result["mentioned_products"] = result[
    "mentioned_products"
].apply(lambda x: "|".join(x))

result["detected_intents"] = result[
    "detected_intents"
].apply(lambda x: "|".join(x))

output_path = OUT_DIR / "routing_quality_labels_v21.csv"

result.to_csv(
    output_path,
    index=False,
)

# ============================================================
# SUMMARY
# ============================================================

print("\n==========================================")
print("KESTREL ROUTING QUALITY LABELS V2.1")
print("==========================================")

counts = result["quality_label"].value_counts()

print("\nCounts:")
print(counts.to_string())

print("\nPercentages:")
print(
    (
        result["quality_label"]
        .value_counts(normalize=True)
        * 100
    ).round(2).to_string()
)

print("\nSaved:")
print(output_path)