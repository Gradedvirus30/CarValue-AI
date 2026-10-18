
from collections import Counter
from copy import deepcopy


# Experimental defaults — tune after testing on labelled examples.
DEFAULT_CONFIDENCE_THRESHOLD = 0.50
DEFAULT_STARTING_SCORE = 100.0
DEFAULT_IOU_THRESHOLD = 0.50

DEFAULT_DAMAGE_PENALTIES = {
    "dent": 8.0,
    "scratch": 3.0,
    "crack": 10.0,
    "glass_shatter": 15.0,
    "lamp_broken": 12.0,
    "tire_flat": 15.0,
}


def calculate_iou(box_a, box_b):
    """Calculate intersection-over-union for [x1, y1, x2, y2] boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def deduplicate_detections(detections, iou_threshold=DEFAULT_IOU_THRESHOLD):
    """
    Remove overlapping detections of the same class within one image.
    Keep the detection with the highest confidence.
    """
    ordered = sorted(
        detections,
        key=lambda detection: detection["confidence"],
        reverse=True,
    )

    kept = []
    removed = []

    for candidate in ordered:
        is_duplicate = False

        for existing in kept:
            if candidate["damage_type"] != existing["damage_type"]:
                continue

            overlap = calculate_iou(
                candidate["bounding_box"],
                existing["bounding_box"],
            )

            if overlap >= iou_threshold:
                is_duplicate = True
                removed.append({
                    "image": candidate.get("image", "unknown"),
                    "damage_type": candidate["damage_type"],
                    "confidence": candidate["confidence"],
                    "duplicate_of_confidence": existing["confidence"],
                    "iou": round(overlap, 4),
                })
                break

        if not is_duplicate:
            kept.append(candidate)

    return kept, removed


def score_inspection(
    image_results,
    confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD,
    starting_score=DEFAULT_STARTING_SCORE,
    damage_penalties=None,
    iou_threshold=DEFAULT_IOU_THRESHOLD,
):
    """
    Produce an experimental 0-100 vehicle condition score.

    image_results is a list of dictionaries returned by analyze_image(),
    or equivalent dictionaries with image and detections fields.
    """
    if not 0.0 <= confidence_threshold <= 1.0:
        raise ValueError("confidence_threshold must be between 0 and 1.")

    if not 0.0 <= iou_threshold <= 1.0:
        raise ValueError("iou_threshold must be between 0 and 1.")

    if not 0.0 <= starting_score <= 100.0:
        raise ValueError("starting_score must be between 0 and 100.")

    penalties = dict(DEFAULT_DAMAGE_PENALTIES)

    if damage_penalties is not None:
        penalties.update(damage_penalties)

    accepted_detections = []
    ignored_low_confidence = []
    removed_duplicates = []
    per_image = []

    for image_result in image_results:
        image_name = image_result.get("image", "unknown")
        detections = image_result.get("detections", [])

        eligible = []
        below_threshold = []

        for detection in detections:
            confidence = float(detection["confidence"])

            if not 0.0 <= confidence <= 1.0:
                raise ValueError("Detection confidence must be between 0 and 1.")

            item = deepcopy(detection)
            item["confidence"] = confidence
            item["image"] = image_name

            if confidence < confidence_threshold:
                below_threshold.append(item)
            else:
                eligible.append(item)

        unique, duplicates = deduplicate_detections(
            eligible,
            iou_threshold,
        )

        for detection in unique:
            detection["penalty"] = float(
                penalties.get(detection["damage_type"], 0.0)
            )
            accepted_detections.append(detection)

        ignored_low_confidence.extend(below_threshold)
        removed_duplicates.extend(duplicates)

        per_image.append({
            "image": image_name,
            "detections_received": len(detections),
            "accepted_detections": len(unique),
            "ignored_low_confidence": len(below_threshold),
            "duplicates_removed": len(duplicates),
        })

    penalty_totals = Counter()

    for detection in accepted_detections:
        penalty_totals[detection["damage_type"]] += detection["penalty"]

    total_penalty = sum(
        detection["penalty"] for detection in accepted_detections
    )

    final_score = max(
        0.0,
        min(100.0, starting_score - total_penalty),
    )

    return {
        "score": round(final_score, 2),
        "starting_score": round(starting_score, 2),
        "total_penalty": round(total_penalty, 2),
        "rating": "Experimental; not a validated industry standard",
        "confidence_threshold": confidence_threshold,
        "iou_threshold": iou_threshold,
        "damage_penalties": penalties,
        "penalty_breakdown": {
            damage_type: round(penalty, 2)
            for damage_type, penalty in penalty_totals.items()
        },
        "detections_counted": len(accepted_detections),
        "detections": accepted_detections,
        "ignored_low_confidence": ignored_low_confidence,
        "duplicates_removed": removed_duplicates,
        "per_image": per_image,
        "limitations": [
            "Confidence filters detections; it does not determine severity.",
            "Overlapping boxes are deduplicated within each image only.",
            "The same physical damage across different views may be counted twice.",
            "Penalty values are provisional, not validated repair costs.",
            "A score of 100 means no qualifying damage was detected; "
            "it does not prove the vehicle is damage-free.",
        ],
    }
