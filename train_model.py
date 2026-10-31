
from pathlib import Path
from urllib.parse import urlparse

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import (
    CalibratedClassifierCV,
    calibration_curve,
)
from sklearn.frozen import FrozenEstimator
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    brier_score_loss,
    log_loss,
    confusion_matrix,
    classification_report,
    ConfusionMatrixDisplay,
)

from url_features import extract_features


# --------------------------------------------------
# PATHS AND SETTINGS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "PhiUSIIL_Phishing_URL_Dataset.csv"
)

RESULTS_DIR = BASE_DIR / "results"

# Save to a NEW file to preserve the previous models.
MODEL_PATH = (
    BASE_DIR
    / "models"
    / "phishguard_model_wwwfix.joblib"
)

URL_COLUMN = "URL"
LABEL_COLUMN = "label"
RANDOM_STATE = 42


# --------------------------------------------------
# HOSTNAME EXTRACTION
# --------------------------------------------------

def get_hostname(url):
    """Normalize hostname for group-based data splitting."""
    url = str(url).strip()

    if not url:
        return ""

    if "://" not in url:
        url = "http://" + url

    try:
        hostname = (urlparse(url).hostname or "").lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    except ValueError:
        return ""


# --------------------------------------------------
# FEATURE EXTRACTION
# --------------------------------------------------

def build_feature_table(urls):
    """Extract URL features using url_features.py."""
    records = []
    total = len(urls)

    for index, url in enumerate(urls, start=1):
        try:
            features = extract_features(url)

        except (ValueError, TypeError):
            # Fallback for malformed URLs.
            features = extract_features(
                "http://invalid.example"
            )

        records.append(features)

        if index % 10000 == 0 or index == total:
            print(
                f"Processed {index:,}/{total:,} URLs"
            )

    return pd.DataFrame(records)


# --------------------------------------------------
# GROUP SPLITTING
# --------------------------------------------------

def split_by_hostname(X, y, groups, test_size, seed):
    """Keep each hostname within one data split."""
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=seed,
    )

    train_indices, test_indices = next(
        splitter.split(X, y, groups=groups)
    )

    return train_indices, test_indices


# --------------------------------------------------
# MODEL EVALUATION
# --------------------------------------------------

def evaluate_model(name, model, X_test, y_test):
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)

    # Dataset labels:
    # 0 = phishing
    # 1 = legitimate
    phishing_probabilities = probabilities[:, 0]
    actual_phishing = (y_test == 0).astype(int)

    print(f"\n{'=' * 55}")
    print(name)
    print("=" * 55)

    print(
        "Accuracy:",
        round(accuracy_score(y_test, predictions), 6),
    )

    print(
        "Macro F1:",
        round(
            f1_score(
                y_test,
                predictions,
                average="macro",
            ),
            6,
        ),
    )

    print(
        "ROC-AUC:",
        round(
            roc_auc_score(
                actual_phishing,
                phishing_probabilities,
            ),
            6,
        ),
    )

    print(
        "Brier Score:",
        round(
            brier_score_loss(
                actual_phishing,
                phishing_probabilities,
            ),
            6,
        ),
    )

    print(
        "Log Loss:",
        round(
            log_loss(
                y_test,
                probabilities,
                labels=[0, 1],
            ),
            6,
        ),
    )

    # Confusion matrix
    print("\nConfusion Matrix (labels: 0, 1):")

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1],
    )

    print(cm)

    # Matrix layout:
    # [[actual phishing predicted phishing,
    #   actual phishing predicted legitimate],
    #  [actual legitimate predicted phishing,
    #   actual legitimate predicted legitimate]]

    true_phishing = cm[0, 0]
    missed_phishing = cm[0, 1]
    false_positives = cm[1, 0]
    correct_legitimate = cm[1, 1]

    # False Positive Rate:
    # Legitimate URLs incorrectly flagged as phishing.
    legitimate_total = (
        false_positives + correct_legitimate
    )

    if legitimate_total > 0:
        fpr = (
            false_positives / legitimate_total
        ) * 100

        print(f"False Positive Rate (FPR): {fpr:.4f}%")
        print(
            "Legitimate URLs wrongly flagged as phishing:",
            false_positives,
        )
    else:
        print(
            "FPR cannot be calculated: "
            "no legitimate test URLs."
        )

    # False Negative Rate:
    # Phishing URLs incorrectly classified as legitimate.
    phishing_total = true_phishing + missed_phishing

    if phishing_total > 0:
        fnr = (
            missed_phishing / phishing_total
        ) * 100

        print(f"False Negative Rate (FNR): {fnr:.4f}%")
        print("Phishing URLs missed:", missed_phishing)
    else:
        print(
            "FNR cannot be calculated: "
            "no phishing test URLs."
        )

    # Classification report
    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            labels=[0, 1],
            target_names=[
                "Phishing (0)",
                "Legitimate (1)",
            ],
            zero_division=0,
        )
    )

    return phishing_probabilities


# --------------------------------------------------
# MAIN TRAINING PROCESS
# --------------------------------------------------

def main():
    print("Loading dataset...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH,
        usecols=[
            URL_COLUMN,
            LABEL_COLUMN,
        ],
    )

    df = df.dropna(
        subset=[
            URL_COLUMN,
            LABEL_COLUMN,
        ]
    ).copy()

    df[URL_COLUMN] = (
        df[URL_COLUMN]
        .astype(str)
        .str.strip()
    )

    df = df[df[URL_COLUMN] != ""]

    df[LABEL_COLUMN] = pd.to_numeric(
        df[LABEL_COLUMN],
        errors="coerce",
    )

    df = df.dropna(
        subset=[LABEL_COLUMN]
    )

    df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(int)

    df = df[df[LABEL_COLUMN].isin([0, 1])]

    # Remove exact duplicate URLs.
    df = df.drop_duplicates(
        subset=[URL_COLUMN]
    ).reset_index(drop=True)

    print("Unique URLs:", len(df))

    print("\nLabel distribution:")
    print(
        df[LABEL_COLUMN]
        .value_counts()
        .sort_index()
    )

    # Create normalized hostname groups.
    groups = df[URL_COLUMN].map(get_hostname)

    if (groups == "").any():
        raise ValueError(
            "Some URLs have empty hostnames. "
            "Check the dataset."
        )

    # Feature extraction
    print("\nExtracting URL features...")

    X = build_feature_table(
        df[URL_COLUMN].tolist()
    )

    y = df[LABEL_COLUMN].to_numpy()

    feature_names = list(X.columns)

    print("\nFeature count:", len(feature_names))
    print("Feature names:", feature_names)

    if len(feature_names) != 22:
        raise ValueError(
            f"Expected 22 features, found {len(feature_names)}."
        )

    # Ensure feature values are valid.
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError(
            "Feature table contains NaN or infinite values."
        )

    # --------------------------------------------------
    # SPLIT INTO TRAINING, CALIBRATION AND TEST SETS
    # --------------------------------------------------

    fit_cal_indices, test_indices = split_by_hostname(
        X,
        y,
        groups,
        test_size=0.20,
        seed=RANDOM_STATE,
    )

    fit_local, calibration_local = split_by_hostname(
        X.iloc[fit_cal_indices],
        y[fit_cal_indices],
        groups.iloc[fit_cal_indices],
        test_size=0.20,
        seed=RANDOM_STATE + 1,
    )

    fit_indices = fit_cal_indices[fit_local]

    calibration_indices = (
        fit_cal_indices[calibration_local]
    )

    fit_groups = set(groups.iloc[fit_indices])
    calibration_groups = set(
        groups.iloc[calibration_indices]
    )
    test_groups = set(groups.iloc[test_indices])

    assert fit_groups.isdisjoint(calibration_groups)
    assert fit_groups.isdisjoint(test_groups)
    assert calibration_groups.isdisjoint(test_groups)

    print("\n========== DATA SPLIT ==========")
    print("Training URLs:", len(fit_indices))
    print("Calibration URLs:", len(calibration_indices))
    print("Final test URLs:", len(test_indices))
    print("Hostname overlap between splits: 0")

    X_fit = X.iloc[fit_indices]
    y_fit = y[fit_indices]

    X_calibration = X.iloc[calibration_indices]
    y_calibration = y[calibration_indices]

    X_test = X.iloc[test_indices]
    y_test = y[test_indices]

    # --------------------------------------------------
    # TRAIN RANDOM FOREST
    # --------------------------------------------------

    base_model = RandomForestClassifier(
        n_estimators=150,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        min_samples_leaf=2,
    )

    print("\nTraining Random Forest model...")

    base_model.fit(X_fit, y_fit)

    print("Random Forest training completed.")

    # --------------------------------------------------
    # CALIBRATE USING SEPARATE CALIBRATION DATA
    # --------------------------------------------------

    print(
        "\nCalibrating model using sigmoid calibration..."
    )

    calibrated_model = CalibratedClassifierCV(
        estimator=FrozenEstimator(base_model),
        method="sigmoid",
    )

    calibrated_model.fit(
        X_calibration,
        y_calibration,
    )

    print("Calibration completed.")

    # --------------------------------------------------
    # EVALUATE BOTH MODELS ON FINAL TEST DATA
    # --------------------------------------------------

    base_probabilities = evaluate_model(
        "BASE RANDOM FOREST",
        base_model,
        X_test,
        y_test,
    )

    calibrated_probabilities = evaluate_model(
        "SIGMOID-CALIBRATED RANDOM FOREST",
        calibrated_model,
        X_test,
        y_test,
    )

    # --------------------------------------------------
    # SAVE RESULTS AND PLOTS
    # --------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    actual_phishing = (y_test == 0).astype(int)

    base_fraction, base_mean = calibration_curve(
        actual_phishing,
        base_probabilities,
        n_bins=10,
        strategy="uniform",
    )

    calibrated_fraction, calibrated_mean = calibration_curve(
        actual_phishing,
        calibrated_probabilities,
        n_bins=10,
        strategy="uniform",
    )

    # Calibration comparison plot.
    plt.figure(figsize=(8, 6))

    plt.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        label="Ideal calibration",
    )

    plt.plot(
        base_mean,
        base_fraction,
        marker="o",
        label="Base Random Forest",
    )

    plt.plot(
        calibrated_mean,
        calibrated_fraction,
        marker="s",
        label="Sigmoid-calibrated Random Forest",
    )

    plt.xlabel("Mean predicted phishing probability")
    plt.ylabel("Observed phishing fraction")
    plt.title("PhishGuard AI - Calibration Comparison")
    plt.legend()
    plt.tight_layout()

    calibration_plot = (
        RESULTS_DIR
        / "calibration_comparison_wwwfix.png"
    )

    plt.savefig(calibration_plot, dpi=150)
    plt.close()

    # Confusion matrix plot for calibrated model.
    ConfusionMatrixDisplay.from_predictions(
        y_test,
        calibrated_model.predict(X_test),
        labels=[0, 1],
        display_labels=[
            "Phishing (0)",
            "Legitimate (1)",
        ],
        values_format="d",
    )

    plt.tight_layout()

    confusion_plot = (
        RESULTS_DIR
        / "confusion_matrix_wwwfix.png"
    )

    plt.savefig(confusion_plot, dpi=150)
    plt.close()

    # --------------------------------------------------
    # SAVE RETRAINED MODEL TO A NEW FILE
    # --------------------------------------------------

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if MODEL_PATH.exists():
        raise FileExistsError(
            f"Model file already exists: {MODEL_PATH}\n"
            "Rename or back up that file before retraining."
        )

    joblib.dump(
        {
            "model": calibrated_model,
            "base_model": base_model,
            "feature_names": feature_names,
            "label_meanings": {
                0: "phishing",
                1: "legitimate",
            },
            "evaluation_method": (
                "Hostname-grouped fit/calibration/test split"
            ),
            "calibration_method": "sigmoid",
            "feature_logic": "www-prefix-ignored-v1",
        },
        MODEL_PATH,
    )

    print("\n========== COMPLETED ==========")
    print("New model saved to:", MODEL_PATH)
    print("Calibration plot:", calibration_plot)
    print("Confusion matrix plot:", confusion_plot)
    print("Previous model files were not overwritten.")


if __name__ == "__main__":
    main()
