import math
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from preprocess import preprocess


def main():

    df = pd.read_csv("data/cars.csv")

    X, y = preprocess(df)

    joblib.dump(X.columns.tolist(), "models/feature_columns.pkl")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = RandomForestRegressor(random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)

    mse = mean_squared_error(y_test, predictions)
    rmse = math.sqrt(mse)

    r2 = r2_score(y_test, predictions)

    print(f"MAE  : {mae:.2f}")
    print(f"RMSE : {rmse:.2f}")
    print(f"R²   : {r2:.4f}")

    joblib.dump(model, "models/random_forest.pkl")

    print("\nModel saved successfully.")


if __name__ == "__main__":
    main()