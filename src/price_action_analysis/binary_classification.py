import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit

from price_action_analysis.constants import MONTHS


def prepare_classification_data(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure index is named 'year' and reset
    if df.index.name != "year":
        df.index.name = "year"
    df = df.reset_index().melt(id_vars="year", var_name="month", value_name="return")
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
        y_train, _y_test = y.iloc[train_idx], y.iloc[test_idx]

        clf = LogisticRegression(random_state=42, max_iter=1000)
        clf.fit(X_train, y_train)
        clf.predict(X_test)

    # save final model on all data
    final_model = LogisticRegression(random_state=42, max_iter=1000)
    final_model.fit(X, y)

    # print_up_down(sector)
    print_monthly_max_up_down(sector) # type: ignore

    return final_model


def print_monthly_max_up_down(df: pd.DataFrame):
    # Ensure index is named 'year' and reset
    if df.index.name != "year":
        df.index.name = "year"
    df = df.reset_index().melt(id_vars="year", var_name="month", value_name="return")
    df = df.dropna(subset=["return"])

    # label each month as Up or Down
    df["direction"] = df["return"].apply(lambda r: "Up" if r > 0 else "Down")

    # group by month across all years and count Up vs Down
    counts = df.groupby("month")["direction"].value_counts().unstack(fill_value=0)

    # decide majority direction for each month
    majority = counts.apply(
        lambda row: "Up" if row.get("Up", 0) > row.get("Down", 0) else "Down", axis=1
    )

    return majority
