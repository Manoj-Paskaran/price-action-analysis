import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import sys
import os

from price_action_analysis.constants import MONTHS

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(PROJECT_ROOT)

SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
sys.path.append(SRC_ROOT)

from pages.monthly_analysis import get_sector_monthly_analysis

def prepare_classification_data(sector: str) -> pd.DataFrame:
    sector_analysis = get_sector_monthly_analysis(sector)

    # melt into long form
    df = sector_analysis.reset_index().melt(
        id_vars="year", var_name="month", value_name="return"
    )
    df = df.dropna(subset=["return"])

    # target variable: 1 if return > 0 else 0
    df["up"] = (df["return"] > 0).astype(int)

    # month as numeric feature
    month_map = {m: i + 1 for i, m in enumerate(MONTHS)}
    df["month_num"] = df["month"].map(month_map)

    # lag features (previous 1 and 2 months return)
    df["return_lag1"] = df["return"].shift(1)
    df["return_lag2"] = df["return"].shift(2)

    # drop rows with missing lag features
    return df.dropna()


def train_classifier(df: pd.DataFrame, sector: str):
    """
    Train and evaluate a simple Logistic Regression binary classifier.
    """
    X = df[["month_num", "return_lag1", "return_lag2"]]
    y = df["up"]

    tscv = TimeSeriesSplit(n_splits=5)

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        clf = LogisticRegression(random_state=42, max_iter=1000)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        print(f"\nFold {fold} Results for sector {sector}:")
        print(classification_report(y_test, y_pred, digits=3))
        print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    # save final model on all data
    final_model = LogisticRegression(random_state=42, max_iter=1000)
    final_model.fit(X, y)
    joblib.dump(final_model, f"{sector}_binary_classifier.pkl")

    return final_model


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.price_action_analysis.binary_classification <sector_name>")
        sys.exit(1)

    sector = sys.argv[1]
    df = prepare_classification_data(sector)
    model = train_classifier(df, sector)
    print(f"Model saved as {sector}_binary_classifier.pkl")
