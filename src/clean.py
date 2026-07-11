def clean_dataframe(df):
    df = df.copy()

    df["brand"] = df["brand"].replace({
        "ISUZU": "Isuzu"
    })

    return df