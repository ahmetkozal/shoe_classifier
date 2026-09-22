from pathlib import Path
import csv

import torch
from PIL import Image
from torchvision import transforms, models
import torch.nn as nn


# ============================================================
# SETTINGS
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

LOW_CONFIDENCE = 0.70


# ============================================================
# DEVICE
# ============================================================

if torch.cuda.is_available():

    device = torch.device("cuda")

    print()
    print(
        "Using GPU:",
        torch.cuda.get_device_name(0)
    )

else:

    device = torch.device("cpu")

    print()
    print("Using CPU.")


# ============================================================
# INPUT
# ============================================================

model_path = Path(
    input("\nModel dosyasının yolunu gir: ").strip()
)

source_dir = Path(
    input("Fotoğraf klasörünün yolunu gir: ").strip()
)


if not model_path.exists():

    print("\nHata: Model dosyası bulunamadı.")
    exit()


if not source_dir.exists():

    print("\nHata: Fotoğraf klasörü bulunamadı.")
    exit()


# ============================================================
# FIND IMAGES
# ============================================================

images = sorted(
    [
        path
        for path in source_dir.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    ]
)


if not images:

    print(
        "\nBu klasörde desteklenen fotoğraf bulunamadı."
    )

    exit()


print()
print(
    f"{len(images)} fotoğraf bulundu."
)


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("Loading model...")


checkpoint = torch.load(
    model_path,
    map_location=device
)


classes = checkpoint["classes"]


model = models.resnet18(
    weights=None
)


model.fc = nn.Linear(
    model.fc.in_features,
    len(classes)
)


model.load_state_dict(
    checkpoint["model_state_dict"]
)

model = model.to(device)

model.eval()


# ============================================================
# TRANSFORM
# ============================================================

transform = transforms.Compose([

    transforms.Resize((224, 224)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],
        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# CSV
# ============================================================

csv_path = source_dir / "predictions.csv"


results = []


# ============================================================
# PREDICT
# ============================================================

print()
print("=" * 70)
print("PREDICTIONS")
print("=" * 70)


for number, image_path in enumerate(
    images,
    start=1
):

    try:

        image = Image.open(
            image_path
        ).convert("RGB")

        image_tensor = transform(
            image
        ).unsqueeze(0)

        image_tensor = image_tensor.to(
            device
        )


        with torch.no_grad():

            outputs = model(
                image_tensor
            )

            probabilities = torch.softmax(
                outputs,
                dim=1
            )

            confidence, prediction = (
                torch.max(
                    probabilities,
                    1
                )
            )


        predicted_class = classes[
            prediction.item()
        ]

        confidence_value = (
            confidence.item()
        )


        results.append({

            "filename":
                image_path.name,

            "prediction":
                predicted_class,

            "confidence":
                confidence_value

        })


        warning = ""

        if confidence_value < LOW_CONFIDENCE:

            warning = "  <-- LOW CONFIDENCE"


        print(
            f"[{number:>4}/{len(images)}] "
            f"{image_path.name:<35} "
            f"{predicted_class:<30} "
            f"{confidence_value * 100:>6.2f}%"
            f"{warning}"
        )


    except Exception as error:

        print()
        print(
            f"HATA: {image_path.name}"
        )

        print(error)


# ============================================================
# SAVE CSV
# ============================================================

with open(
    csv_path,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "filename",
        "prediction",
        "confidence"
    ])


    for result in results:

        writer.writerow([
            result["filename"],
            result["prediction"],
            f"{result['confidence']:.4f}"
        ])


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)


print()
print(
    "Processed:",
    len(results)
)


low_confidence_results = [
    result
    for result in results
    if result["confidence"] < LOW_CONFIDENCE
]


print(
    "Low confidence:",
    len(low_confidence_results)
)


print()
print(
    "CSV saved to:"
)

print(
    csv_path
)


# ============================================================
# CLASS COUNTS
# ============================================================

class_counts = {}


for result in results:

    class_name = result["prediction"]

    class_counts[class_name] = (
        class_counts.get(
            class_name,
            0
        ) + 1
    )


print()
print("Predicted class counts:")
print("-" * 70)


for class_name in sorted(
    class_counts
):

    print(
        f"{class_name:<35}"
        f"{class_counts[class_name]:>6}"
    )


# ============================================================
# LOW CONFIDENCE LIST
# ============================================================

if low_confidence_results:

    print()
    print("=" * 70)
    print("LOW CONFIDENCE IMAGES")
    print("=" * 70)


    for result in low_confidence_results:

        print(
            f"{result['filename']:<40}"
            f"{result['prediction']:<30}"
            f"{result['confidence'] * 100:>6.2f}%"
        )


print()
print("Done.")

