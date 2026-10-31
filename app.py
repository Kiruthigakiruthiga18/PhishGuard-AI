
from flask import Flask, render_template, request, jsonify
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import joblib
import shap

from url_features import extract_features

app = Flask(__name__)

# Project directory and model path
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "phishguard_model_retrained.joblib"

saved_model = None
prediction_model = None
explanation_model = None
explainer = None
feature_names = None


# --------------------------------------------------
# LOAD MODELS
# --------------------------------------------------
def load_models():
    global saved_model
    global prediction_model
    global explanation_model
    global explainer
    global feature_names

    try:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found: {MODEL_PATH}"
            )

        saved_model = joblib.load(MODEL_PATH)

        # Calibrated model for probability prediction
        prediction_model = saved_model["model"]

        # Original Random Forest for SHAP explanations
        explanation_model = saved_model.get("base_model")

        if explanation_model is None:
            raise KeyError(
                "'base_model' missing from saved model. "
                "Run train_model.py again."
            )

        feature_names = saved_model["feature_names"]

        # Explain the underlying Random Forest
        explainer = shap.TreeExplainer(explanation_model)

        print("\nPhishGuard AI model loaded successfully!")
        print(
            "Prediction model:",
            type(prediction_model).__name__
        )
        print(
            "Explanation model:",
            type(explanation_model).__name__
        )
        print("SHAP explainer loaded successfully!")
        print("Feature count:", len(feature_names))
        print("Model path:", MODEL_PATH)

    except Exception as error:
        saved_model = None
        prediction_model = None
        explanation_model = None
        explainer = None
        feature_names = None

        app.logger.exception("MODEL LOADING FAILED")
        print("Model loading error:", str(error))


load_models()


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# URL SCAN API
# --------------------------------------------------
@app.route("/scan", methods=["POST"])
def scan_url():

    if (
        prediction_model is None
        or explanation_model is None
        or explainer is None
    ):
        return jsonify({
            "success": False,
            "message": (
                "ML model is unavailable. "
                "Check the Flask terminal for the model loading error."
            )
        }), 503

    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()

    # Validate empty input
    if not url:
        return jsonify({
            "success": False,
            "message": "Please enter a URL."
        }), 400

    # Prevent excessively long input
    if len(url) > 2048:
        return jsonify({
            "success": False,
            "message": "URL is too long."
        }), 400

    # Add HTTPS when a scheme is not provided
    if "://" not in url:
        url = "https://" + url

    # Validate URL structure
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        # Accessing port can raise ValueError for invalid ports
        _ = parsed.port

        if (
            parsed.scheme.lower() not in ("http", "https")
            or not hostname
            or any(char.isspace() for char in url)
            or "@" in parsed.netloc
        ):
            return jsonify({
                "success": False,
                "message": (
                    "Please enter a valid HTTP or HTTPS URL."
                )
            }), 400

    except ValueError:
        return jsonify({
            "success": False,
            "message": "Please enter a valid URL."
        }), 400

    # Extract features and predict
    try:
        features = extract_features(url)

        X = pd.DataFrame(
            [features],
            columns=feature_names
        )

        # Use calibrated model for class probabilities
        probabilities = prediction_model.predict_proba(X)[0]

        class_probabilities = dict(
            zip(prediction_model.classes_, probabilities)
        )

        # Dataset labels: 0 = Phishing, 1 = Legitimate
        phishing_probability = float(
            class_probabilities.get(0, 0.0)
        )

        legitimate_probability = float(
            class_probabilities.get(1, 0.0)
        )

        prediction = (
            "Potential phishing"
            if phishing_probability >= 0.5
            else "Likely legitimate"
        )

        # --------------------------------------------------
        # SHAP EXPLANATION
        # Explain class 1: LEGITIMATE
        # --------------------------------------------------
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):
            # Older SHAP versions:
            # list contains one array per class
            if len(shap_values) < 2:
                raise ValueError(
                    "SHAP output does not contain both classes."
                )

            contributions = shap_values[1][0]

        else:
            shap_array = getattr(
                shap_values,
                "values",
                shap_values
            )

            if getattr(shap_array, "ndim", 0) == 3:
                # Shape: samples x features x classes
                # Class 1 = Legitimate
                contributions = shap_array[0, :, 1]

            elif getattr(shap_array, "ndim", 0) == 2:
                # Binary-class SHAP output in a 2D format
                contributions = shap_array[0]

            else:
                raise ValueError(
                    "Unexpected SHAP output shape: "
                    f"{getattr(shap_array, 'shape', None)}"
                )

        if len(contributions) != len(feature_names):
            raise ValueError(
                "SHAP feature count does not match model features."
            )

        # Prepare explanation data
        explanation = pd.DataFrame({
            "feature": feature_names,
            "value": X.iloc[0].values,
            "shap_value": contributions
        })

        explanation["impact"] = (
            explanation["shap_value"].abs()
        )

        # Select top 5 features by absolute SHAP impact
        explanation = explanation.sort_values(
            by="impact",
            ascending=False
        ).head(5)

        top_features = []

        for _, row in explanation.iterrows():
            shap_value = float(row["shap_value"])

            # Signs are interpreted for the LEGITIMATE class
            if shap_value > 0:
                effect = "Supports legitimate prediction"
            elif shap_value < 0:
                effect = "Opposes legitimate prediction"
            else:
                effect = "Minimal contribution"

            top_features.append({
                "feature": str(row["feature"]),
                "value": float(row["value"]),
                "shap_value": round(shap_value, 5),
                "effect": effect
            })

        # Return fields expected by the existing frontend
        return jsonify({
            "success": True,
            "url": url,
            "prediction": prediction,
            "phishing_probability": round(
                phishing_probability * 100, 2
            ),
            "legitimate_probability": round(
                legitimate_probability * 100, 2
            ),
            "explanation": top_features,
            "message": (
                "This research prototype estimates URL-based risk. "
                "Predictions may be incorrect and do not guarantee "
                "website safety. SHAP explanations describe the "
                "underlying Random Forest and show contributions "
                "toward or against the legitimate class."
            )
        })

    except Exception:
        app.logger.exception("URL SCAN FAILED")

        return jsonify({
            "success": False,
            "message": (
                "Unable to scan this URL. "
                "Check the Flask terminal for details."
            )
        }), 500


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
