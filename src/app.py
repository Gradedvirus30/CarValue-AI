from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
from src.clean import clean_dataframe

import io
import uuid
from pathlib import Path

from fastapi import File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from typing import Annotated
from fastapi.openapi.utils import get_openapi

from src.damage_detector import analyze_image
from src.conditioned_scoring import score_inspection
from src.predict import predict_price


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


# ---------- VEHICLE INSPECTION IMAGE UPLOAD ----------

INSPECTION_DIR = Path("data/inspections")
INSPECTION_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per image
MAX_IMAGES = 10


@app.post("/inspection/upload")
async def upload_inspection_images(
    files: Annotated[list[UploadFile], File()]
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Upload at least one JPEG image."
        )

    if len(files) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_IMAGES} images per inspection."
        )

    inspection_id = f"INS-{uuid.uuid4().hex[:10].upper()}"
    inspection_path = INSPECTION_DIR / inspection_id
    inspection_path.mkdir(parents=True, exist_ok=False)

    saved_images = []
    total_bytes = 0

    try:
        for index, uploaded_file in enumerate(files, start=1):
            content = await uploaded_file.read(
                MAX_FILE_SIZE + 1
            )

            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="An uploaded image is empty."
                )

            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="Each image must be 10 MB or smaller."
                )

            # Verify that the content is actually a JPEG.
            try:
                with Image.open(io.BytesIO(content)) as image:
                    if image.format != "JPEG":
                        raise HTTPException(
                            status_code=400,
                            detail="Only JPEG images are accepted."
                        )

                    image.verify()

            except UnidentifiedImageError:
                raise HTTPException(
                    status_code=400,
                    detail="One of the files is not a valid image."
                )

            filename = f"view_{index:02d}.jpg"
            destination = inspection_path / filename
            destination.write_bytes(content)

            total_bytes += len(content)

            saved_images.append({
                "filename": filename,
                "size_bytes": len(content)
            })

        return {
            "inspection_id": inspection_id,
            "images_received": len(saved_images),
            "total_size_bytes": total_bytes,
            "status": "uploaded",
            "images": saved_images
        }

    except Exception:
        # Remove partial inspection data if any upload fails.
        import shutil
        shutil.rmtree(inspection_path, ignore_errors=True)
        raise

    finally:
        for uploaded_file in files:
            await uploaded_file.close()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    # Convert FastAPI's new file schema into
    # the format Swagger UI expects.
    schema["openapi"] = "3.0.3"

    components = schema.get("components", {}).get("schemas", {})

    for component in components.values():
        for prop in component.get("properties", {}).values():

            # Handle arrays of uploaded files.
            if prop.get("type") == "array":
                items = prop.get("items", {})

                if items.get("contentMediaType") == "application/octet-stream":
                    items.pop("contentMediaType", None)
                    items["format"] = "binary"

            # Handle a single uploaded file.
            if prop.get("contentMediaType") == "application/octet-stream":
                prop.pop("contentMediaType", None)
                prop["format"] = "binary"

    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi


@app.get("/inspection/{inspection_id}/analyze")
def analyze_inspection(inspection_id: str):
    inspection_path = INSPECTION_DIR / inspection_id

    if not inspection_path.is_dir():
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    image_paths = sorted(inspection_path.glob("view_*.jpg"))

    if not image_paths:
        raise HTTPException(
            status_code=404,
            detail="No inspection images found.",
        )

    results = [
        analyze_image(image_path)
        for image_path in image_paths
    ]

    total_detections = sum(
        result["detections_count"] for result in results
    )

    return {
        "inspection_id": inspection_id,
        "images_analyzed": len(results),
        "total_detections": total_detections,
        "results": results,
    }


@app.get("/inspection/{inspection_id}/score")
def get_inspection_score(inspection_id: str):
    inspection_path = INSPECTION_DIR / inspection_id

    if not inspection_path.is_dir():
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    image_paths = sorted(inspection_path.glob("view_*.jpg"))

    if not image_paths:
        raise HTTPException(
            status_code=404,
            detail="No inspection images found.",
        )

    image_results = [
        analyze_image(image_path)
        for image_path in image_paths
    ]

    score_report = score_inspection(image_results)

    return {
        "inspection_id": inspection_id,
        "images_analyzed": len(image_results),
        "condition_report": score_report,
    }


@app.post("/inspection/{inspection_id}/report")
def generate_inspection_report(
    inspection_id: str,
    car: CarInput,
):
    # Validate the inspection ID before accessing its folder.
    if (
        len(inspection_id) != 14
        or not inspection_id.startswith("INS-")
        or any(
            char not in "0123456789ABCDEF"
            for char in inspection_id[4:]
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid inspection ID.",
        )

    inspection_path = INSPECTION_DIR / inspection_id

    if not inspection_path.is_dir():
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    image_paths = sorted(inspection_path.glob("view_*.jpg"))

    if not image_paths:
        raise HTTPException(
            status_code=404,
            detail="No inspection images found.",
        )

    # Run the pretrained damage detector on every image.
    image_results = [
        analyze_image(image_path)
        for image_path in image_paths
    ]

    # Generate the experimental condition report.
    condition_report = score_inspection(image_results)

    # Get the existing CarValueAI base price estimate.
    valuation = predict_price(car.dict())

    return {
        "inspection_id": inspection_id,
        "images_analyzed": len(image_results),
        "valuation": valuation,
        "condition_report": condition_report,
        "damage_analysis": {
            "total_detections": sum(
                result["detections_count"]
                for result in image_results
            ),
            "results": image_results,
        },
        "pricing_note": (
            "The condition score is experimental and does not "
            "currently modify the predicted vehicle price."
        ),
    }




