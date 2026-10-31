
import joblib
import pandas as pd
import shap

from pathlib import Path
from url_features import extract_features

MODEL_PATH = Path("models/phishguard_model.joblib")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "Trained model not found. Run python train_model.py first."
    )

print("Loading trained model...")
saved = joblib.load(MODEL_PATH)

model = saved["model"]
feature_names = saved["feature_names"]

# Test URL for explanation
url = "https://secure-account-example.com/signin"

features = extract_features(url)
X = pd.DataFrame([features], columns=feature_names)

print("\nURL:", url)

probabilities = model.predict_proba(X)[0]
class_probabilities = dict(zip(model.classes_, probabilities))

phishing_probability = float(class_probabilities.get(0, 0.0))
legitimate_probability = float(class_probabilities.get(1, 0.0))

print("Phishing probability:", round(phishing_probability * 100, 2), "%")
print("Legitimate probability:", round(legitimate_probability * 100, 2), "%")

print("\nCalculating SHAP explanations...")

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# SHAP output shapes differ between library/model versions.
if isinstance(shap_values, list):
    # Binary-class output: class 0 = phishing
    values = shap_values[0][0]
else:
    values_array = shap_values

    if getattr(values_array, "ndim", 0) == 3:
        # Common shape: samples x features x classes
        values = values_array[0, :, 0]
    elif getattr(values_array, "ndim", 0) == 2:
        values = values_array[0]
    else:
        raise ValueError(
            f"Unexpected SHAP output shape: {values_array.shape}"
        )

explanation = pd.DataFrame({
    "feature": feature_names,
    "feature_value": X.iloc[0].values,
    "shap_value_for_phishing_class": values
})

explanation["absolute_impact"] = (
    explanation["shap_value_for_phishing_class"].abs()
)

explanation = explanation.sort_values(
    "absolute_impact",
    ascending=False
)

print("\nTop 10 features by SHAP impact:")
print(
    explanation[
        ["feature", "feature_value", "shap_value_for_phishing_class"]
    ].head(10).to_string(index=False)
)

print("\nExplanation complete!")
