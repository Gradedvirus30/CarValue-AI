import joblib
import numpy as np
import pandas as pd

model = joblib.load("models/random_forest.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")


def predict_price(car_data):

    car_df = pd.DataFrame([car_data])

    car_df = pd.get_dummies(car_df)

    car_df = car_df.reindex(
        columns=feature_columns,
        fill_value=0
    )

    prediction = model.predict(car_df)[0]

    tree_predictions = np.array([
        tree.predict(car_df)[0]
        for tree in model.estimators_
    ])

    lower = np.percentile(tree_predictions, 10)
    upper = np.percentile(tree_predictions, 90)
    
    return {
        "predicted_price": float(prediction),
        "market_range": {
            "lower": float(lower),
            "upper": float(upper),
        },
    }