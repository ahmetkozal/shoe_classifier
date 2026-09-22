from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms, models
import torch.nn as nn


# ============================================================
# DEVICE
# ============================================================

if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")


# ============================================================
# ASK FOR PATHS
# ============================================================

model_path = Path(
    input("Model dosyasının yolunu gir: ").strip()
)

image_path = Path(
    input("Test fotoğrafının yolunu gir: ").strip()
)


if not model_path.exists():

    print()
    print("Hata: Model dosyası bulunamadı.")
    exit()


if not image_path.exists():

    print()
    print("Hata: Fotoğraf bulunamadı.")
    exit()


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
# IMAGE TRANSFORM
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
# LOAD IMAGE
# ============================================================

image = Image.open(
    image_path
).convert("RGB")


image_tensor = transform(
    image
).unsqueeze(0)

image_tensor = image_tensor.to(device)


# ============================================================
# PREDICTION
# ============================================================

with torch.no_grad():

    outputs = model(
        image_tensor
    )

    probabilities = torch.softmax(
        outputs,
        dim=1
    )

    confidence, prediction = torch.max(
        probabilities,
        1
    )


predicted_class = classes[
    prediction.item()
]

confidence_value = (
    confidence.item() * 100
)


# ============================================================
# TOP 5
# ============================================================

top_count = min(
    5,
    len(classes)
)

top_probabilities, top_indices = (
    torch.topk(
        probabilities,
        top_count
    )
)


# ============================================================
# RESULT
# ============================================================

print()
print("=" * 60)
print("PREDICTION")
print("=" * 60)

print()

print(
    "Image:",
    image_path.name
)

print()

print(
    "Prediction:",
    predicted_class
)

print(
    f"Confidence: {confidence_value:.2f}%"
)


print()
print("Top predictions:")
print("-" * 60)


for probability, index in zip(
    top_probabilities[0],
    top_indices[0]
):

    class_name = classes[
        index.item()
    ]

    percentage = (
        probability.item() * 100
    )

    print(
        f"{class_name:<35} "
        f"{percentage:>6.2f}%"
    )


print()