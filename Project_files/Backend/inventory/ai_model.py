from pathlib import Path
import joblib
import pandas as pd


# ============================================================
# MODEL FILE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = BASE_DIR / "Models"


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

MODEL_PATH = MODEL_DIR / "final_inventory_model.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoders.pkl"
FEATURE_PATH = MODEL_DIR / "feature_columns.pkl"


model = joblib.load(MODEL_PATH)
encoders = joblib.load(ENCODER_PATH)
feature_columns = joblib.load(FEATURE_PATH)


print("FEATURE COLUMNS:")
print(feature_columns)

print("\nENCODER CLASSES:")

for column, encoder in encoders.items():
    print(
        column,
        ":",
        list(encoder.classes_)
    )

# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_demand(data):
    """
    Predict Units Sold using the trained
    Optimized Random Forest model.
    """

    # Convert input dictionary to DataFrame
    input_data = pd.DataFrame([data])

    # --------------------------------------------------------
    # Encode categorical features
    # --------------------------------------------------------

    categorical_columns = [
        "Store ID",
        "Product ID",
        "Category",
        "Region",
        "Weather Condition",
        "Seasonality"
    ]

    for column in categorical_columns:

        encoder = encoders[column]

        input_data[column] = encoder.transform(
            input_data[column]
        )

    # --------------------------------------------------------
    # Create Month and Day
    # --------------------------------------------------------

    input_data["Month"] = input_data["Month"].astype(int)
    input_data["Day"] = input_data["Day"].astype(int)

    # --------------------------------------------------------
    # Arrange features in EXACT training order
    # --------------------------------------------------------

    input_data = input_data[feature_columns]

    # --------------------------------------------------------
    # Make prediction
    # --------------------------------------------------------

    prediction = model.predict(input_data)

    return float(prediction[0])