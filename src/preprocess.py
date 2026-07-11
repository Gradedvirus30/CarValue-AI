import pandas as pd

from clean import clean_dataframe

def preprocess(df):

    df = clean_dataframe(df)

    df = df.drop(columns=["Unnamed: 0", "car_name"])

    X = df.drop("selling_price", axis=1)
    y = df["selling_price"]

    X = pd.get_dummies(X)

    return X, y