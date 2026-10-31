
import joblib
import pandas as pd

from url_features import extract_features


MODEL_PATH = "models/phishguard_model_wwwfix.joblib"

model_data = joblib.load(MODEL_PATH)

model = model_data["model"]
feature_names = model_data["feature_names"]

urls = [
    "https://example.com",
    "https://www.aap.org",
    "https://aap.org",
    "https://www.google.com",
    "https://google.com",
    "https://www.wikipedia.org",
    "https://www.python.org",
]

print("\nPhishGuard AI - URL Prediction Test")
print("=" * 75)

for url in urls:
    features = extract_features(url)

    # Preserve the exact feature order used during training.
    X = pd.DataFrame(
        [[features[name] for name in feature_names]],
        columns=feature_names,
    )

    probabilities = model.predict_proba(X)[0]
    classes = list(model.classes_)

    phishing_index = classes.index(0)
    phishing_probability = probabilities[phishing_index] * 100

    prediction = (
        "Phishing"
        if model.predict(X)[0] == 0
        else "Legitimate"
    )

    print(f"\nURL: {url}")
    print(f"Subdomain count: {features['subdomain_count']}")
    print(f"Phishing probability: {phishing_probability:.2f}%")
    print(f"Prediction: {prediction}")

print("\n" + "=" * 75)
