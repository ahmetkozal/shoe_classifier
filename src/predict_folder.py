import csv
import shutil
from pathlib import Path

import tkinter as tk
from tkinter import filedialog

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image


# ============================================================
# AYARLAR
# ============================================================

CONFIDENCE_THRESHOLD = 0.70

IMAGE_SIZE = 224

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ============================================================
# KLASÖR / DOSYA SEÇİMİ
# ============================================================

root = tk.Tk()
root.withdraw()


# ------------------------------------------------------------
# MODEL SEÇ
# ------------------------------------------------------------

model_path = filedialog.askopenfilename(
    title="Model dosyasını seç",
    filetypes=[
        (
            "PyTorch model",
            "*.pth"
        ),
        (
            "All files",
            "*.*"
        )
    ]
)


if not model_path:

    root.destroy()

    raise SystemExit(
        "Model seçilmedi."
    )


model_path = Path(
    model_path
)


# ------------------------------------------------------------
# FOTOĞRAF KLASÖRÜ SEÇ
# ------------------------------------------------------------

print()

print(
    "Şimdi fotoğrafların bulunduğu "
    "klasörü seç."
)

image_dir = filedialog.askdirectory(
    title="Fotoğrafların bulunduğu klasörü seç"
)


if not image_dir:

    root.destroy()

    raise SystemExit(
        "Fotoğraf klasörü seçilmedi."
    )


image_dir = Path(
    image_dir
)


root.destroy()


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


print()
print(
    f"Device: {device}"
)

print(
    f"Model: {model_path}"
)

print(
    f"Images: {image_dir}"
)


# ============================================================
# MODEL YÜKLE
# ============================================================

print()
print(
    "Loading model..."
)


checkpoint = torch.load(
    model_path,
    map_location=device,
    weights_only=False
)


# ------------------------------------------------------------
# V2 checkpoint
# ------------------------------------------------------------

if isinstance(
    checkpoint,
    dict
) and "classes" in checkpoint:

    classes = checkpoint[
        "classes"
    ]

    num_classes = checkpoint.get(
        "num_classes",
        len(classes)
    )

    model_name = checkpoint.get(
        "model",
        "resnet18"
    )

    print(
        f"Model type: {model_name}"
    )

    print(
        f"Classes: {num_classes}"
    )


    # --------------------------------------------------------
    # ResNet18
    # --------------------------------------------------------

    model = models.resnet18(
        weights=None
    )


    model.fc = nn.Linear(
        model.fc.in_features,
        num_classes
    )


    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )


# ------------------------------------------------------------
# Eski format
# ------------------------------------------------------------

else:

    print(
        "Eski model formatı algılandı."
    )


    if isinstance(
        checkpoint,
        dict
    ) and "model_state_dict" in checkpoint:

        state_dict = checkpoint[
            "model_state_dict"
        ]

    else:

        state_dict = checkpoint


    # Eski modelin sınıfları
    # Bu bölüm yalnızca eski model kullanılırsa
    # gerekli olabilir.

    raise SystemExit(
        "Bu script V2 model formatını bekliyor. "
        "V2 .pth dosyasını seç."
    )


model = model.to(
    device
)

model.eval()


# ============================================================
# TRANSFORM
# ============================================================

transform = transforms.Compose([
    transforms.Resize(
        (
            IMAGE_SIZE,
            IMAGE_SIZE
        )
    ),

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
# FOTOĞRAFLARI BUL
# ============================================================

images = [
    path
    for path in image_dir.iterdir()
    if path.is_file()
    and path.suffix.lower()
    in IMAGE_EXTENSIONS
]


images.sort(
    key=lambda x: x.name.lower()
)


print()

print(
    f"Found images: {len(images)}"
)


if not images:

    raise SystemExit(
        "Bu klasörde fotoğraf bulunamadı."
    )


# ============================================================
# OUTPUT KLASÖRLERİ
# ============================================================

processed_dir = (
    image_dir
    / "processed"
)

review_dir = (
    image_dir
    / "review"
)


processed_dir.mkdir(
    exist_ok=True
)

review_dir.mkdir(
    exist_ok=True
)


# ============================================================
# CSV
# ============================================================

csv_path = (
    review_dir
    / "predictions.csv"
)


csv_file = open(
    csv_path,
    "w",
    encoding="utf-8-sig",
    newline=""
)


csv_writer = csv.writer(
    csv_file
)


csv_writer.writerow([
    "filename",
    "prediction",
    "confidence"
])


# ============================================================
# COUNTERS
# ============================================================

processed_count = 0

review_count = 0

error_count = 0


# ============================================================
# PREDICTION
# ============================================================

print()
print("=" * 60)
print("PREDICTING")
print("=" * 60)
print()


for index, image_path in enumerate(
    images,
    start=1
):

    try:

        # ----------------------------------------------------
        # Image
        # ----------------------------------------------------

        image = Image.open(
            image_path
        ).convert(
            "RGB"
        )


        tensor = transform(
            image
        ).unsqueeze(
            0
        )


        tensor = tensor.to(
            device
        )


        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        with torch.no_grad():

            output = model(
                tensor
            )


            probabilities = torch.softmax(
                output,
                dim=1
            )


            confidence, prediction = (
                probabilities.max(
                    dim=1
                )
            )


        confidence_value = (
            confidence.item()
        )


        prediction_index = (
            prediction.item()
        )


        predicted_class = classes[
            prediction_index
        ]


        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        csv_writer.writerow([
            image_path.name,
            predicted_class,
            f"{confidence_value:.4f}"
        ])


        # ----------------------------------------------------
        # HIGH CONFIDENCE
        # ----------------------------------------------------

        if (
            confidence_value
            >= CONFIDENCE_THRESHOLD
        ):

            destination = (
                processed_dir
                / predicted_class
            )

            destination.mkdir(
                parents=True,
                exist_ok=True
            )


            shutil.copy2(
                image_path,
                destination
                / image_path.name
            )


            processed_count += 1


            status = "PROCESSED"


        # ----------------------------------------------------
        # LOW CONFIDENCE
        # ----------------------------------------------------

        else:

            destination = (
                review_dir
                / image_path.name
            )


            shutil.copy2(
                image_path,
                destination
            )


            review_count += 1


            status = "REVIEW"


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        print(
            f"[{index:4d}/{len(images)}] "
            f"{status:9s} "
            f"{predicted_class:30s} "
            f"{confidence_value:6.2%} "
            f"{image_path.name}"
        )


    except Exception as e:

        error_count += 1

        print()

        print(
            f"ERROR: {image_path.name}"
        )

        print(
            e
        )

        print()


# ============================================================
# CSV KAPAT
# ============================================================

csv_file.close()


# ============================================================
# SONUÇ
# ============================================================

print()
print("=" * 60)
print("TAMAMLANDI")
print("=" * 60)

print()

print(
    f"Toplam fotoğraf : {len(images)}"
)

print(
    f"Processed        : {processed_count}"
)

print(
    f"Review            : {review_count}"
)

print(
    f"Hata              : {error_count}"
)

print()

print(
    f"Confidence threshold: "
    f"{CONFIDENCE_THRESHOLD:.0%}"
)

print()

print(
    f"Processed klasörü:"
)

print(
    processed_dir
)

print()

print(
    f"Review klasörü:"
)

print(
    review_dir
)

print()

print(
    f"Predictions CSV:"
)

print(
    csv_path
)

print()

print("=" * 60)