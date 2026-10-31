
import pandas as pd

dataset_path = "data/raw/PhiUSIIL_Phishing_URL_Dataset.csv"

df = pd.read_csv(dataset_path, usecols=["URL", "label"])

print("Total rows:", len(df))
print("Duplicate URL rows:", df["URL"].duplicated().sum())

# Check URLs that have conflicting labels
label_counts = df.groupby("URL")["label"].nunique()
conflicting_urls = label_counts[label_counts > 1]

print("URLs with conflicting labels:", len(conflicting_urls))

if len(conflicting_urls) > 0:
    print("\nExamples of conflicting URLs:")
    print(
        df[df["URL"].isin(conflicting_urls.index)]
        .sort_values("URL")
        .head(10)
        .to_string(index=False)
    )
else:
    print("No conflicting URL labels found.")

print("\nDuplicate check completed!")
