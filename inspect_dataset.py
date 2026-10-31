
import pandas as pd
from pathlib import Path

dataset_path = Path("data/raw/PhiUSIIL_Phishing_URL_Dataset.csv")

print("Loading full dataset...")

df = pd.read_csv(dataset_path)

print("\n========== DATASET SUMMARY ==========")
print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\n========== LABEL DISTRIBUTION ==========")
print(df["label"].value_counts(dropna=False).sort_index())

print("\n========== URL CHECK ==========")
print("Missing URLs:", df["URL"].isna().sum())
print("Duplicate URLs:", df["URL"].duplicated().sum())
print("Missing labels:", df["label"].isna().sum())

print("\n========== LABEL MEANING CHECK ==========")
print("Unique labels:", sorted(df["label"].dropna().unique()))

print("\n========== SAMPLE URLS ==========")
print(df[["URL", "label"]].head(10).to_string(index=False))

print("\nDataset verification completed!")
