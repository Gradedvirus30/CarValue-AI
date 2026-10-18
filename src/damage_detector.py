
from pathlib import Path

from ultralytics import YOLO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "damage_detection" / "best.pt"

# Load the model once when this module is imported.
model = YOLO(str(MODEL_PATH))


def analyze_image(image_path: str | Path, confidence: float = 0.25):
    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    results = model.predict(
        source=str(image_path),
        imgsz=640,
        conf=confidence,
        device="cpu",
        save=False,
        verbose=False,
    )

    result = results[0]
    detections = []

    for box in result.boxes:
        class_id = int(box.cls[0])
        score = float(box.conf[0])
        coordinates = [round(float(v), 2) for v in box.xyxy[0]]

        detections.append({
            "damage_type": model.names[class_id],
            "confidence": round(score, 4),
            "bounding_box": coordinates,
        })

    return {
        "image": image_path.name,
        "detections_count": len(detections),
        "detections": detections,
    }
