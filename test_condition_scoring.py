
from src.conditioned_scoring import score_inspection


sample_results = [
    {
        "image": "view_01.jpg",
        "detections": [
            {
                "damage_type": "dent",
                "confidence": 0.71,
                "bounding_box": [100, 100, 300, 300],
            },
            {
                "damage_type": "scratch",
                "confidence": 0.58,
                "bounding_box": [400, 400, 500, 500],
            },
            {
                "damage_type": "scratch",
                "confidence": 0.27,
                "bounding_box": [410, 410, 490, 490],
            },
        ],
    }
]

report = score_inspection(sample_results)

print("Condition score:", report["score"])
print("Counted detections:", report["detections_counted"])
print("Penalty breakdown:", report["penalty_breakdown"])
print("Ignored low-confidence:", len(report["ignored_low_confidence"]))
print("Duplicates removed:", len(report["duplicates_removed"]))
