from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
from src.clean import clean_dataframe

df = clean_dataframe(
    pd.read_csv("data/cars.csv")
)

from src.predict import predict_price



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://car-value-ai-theta.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CarInput(BaseModel):
    brand: str
    model: str
    vehicle_age: int
    km_driven: int
    seller_type: str
    fuel_type: str
    transmission_type: str
    mileage: float
    engine: int
    max_power: float
    seats: int


@app.get("/")
def home():
    return {"message": "Car Price Prediction API is running"}


@app.post("/predict")
def predict(car: CarInput):

    return predict_price(car.dict())


@app.get("/options")
def get_options():

    brands = sorted(df["brand"].dropna().unique().tolist())

    models_by_brand = {}

    for brand in brands:
        models = (
            df[df["brand"] == brand]["model"]
            .dropna()
            .unique()
            .tolist()
        )

        models_by_brand[brand] = sorted(models)

    return {
        "brands": brands,
        "models_by_brand": models_by_brand,
        "seller_types": sorted(
            df["seller_type"].dropna().unique().tolist()
        ),
        "fuel_types": sorted(
            df["fuel_type"].dropna().unique().tolist()
        ),
        "transmission_types": sorted(
            df["transmission_type"].dropna().unique().tolist()
        ),
    }