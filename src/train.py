import random
import shutil
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models


# ============================================================
# AYARLAR
# ============================================================

SEED = 42

BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 0.0001

IMAGE_SIZE = 224

VAL_RATIO = 0.15
TEST_RATIO = 0.15

MODEL_NAME = "shoe_classifier_v2.pth"


# ============================================================
# RANDOM SEED
# ============================================================

random.seed(SEED)
torch.manual_seed(SEED)


# ============================================================
# DATASET YOLU
# ============================================================

dataset_path = input(
    "Dataset klasörünün yolunu gir: "
).strip().strip('"')


dataset_path = Path(dataset_path)


if not dataset_path.exists():

    print()
    print("Dataset bulunamadı.")

    raise SystemExit


# ============================================================
# DATASET KLASÖRÜ
# ============================================================

train_dir = dataset_path / "_train"
val_dir = dataset_path / "_val"
test_dir = dataset_path / "_test"


for directory in [
    train_dir,
    val_dir,
    test_dir
]:

    if directory.exists():

        shutil.rmtree(
            directory
        )


# ============================================================
# SINIFLARI BUL
# ============================================================

classes = []

for category_dir in dataset_path.iterdir():

    if not category_dir.is_dir():
        continue

    if category_dir.name.startswith("_"):
        continue

    for style_dir in category_dir.iterdir():

        if not style_dir.is_dir():
            continue

        label = (
            f"{category_dir.name}_"
            f"{style_dir.name}"
        )

        classes.append(
            (
                label,
                style_dir
            )
        )


classes.sort(
    key=lambda x: x[0].lower()
)


print()
print("=" * 60)
print("CLASSES")
print("=" * 60)


for label, path in classes:

    print(
        f"{label:30s}"
        f"{path}"
    )


print()
print(
    f"Total classes: {len(classes)}"
)


# ============================================================
# DATASET SPLIT
# ============================================================

print()
print("=" * 60)
print("DATASET SPLIT")
print("=" * 60)
print()


total_images = 0


for label, source_dir in classes:

    images = [
        p
        for p in source_dir.iterdir()
        if p.is_file()
        and p.suffix.lower() in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        }
    ]


    random.shuffle(
        images
    )


    count = len(images)

    total_images += count


    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    if count >= 10:

        test_count = max(
            1,
            int(count * TEST_RATIO)
        )

        val_count = max(
            1,
            int(count * VAL_RATIO)
        )

    elif count >= 3:

        test_count = 1
        val_count = 1

    elif count == 2:

        test_count = 1
        val_count = 0

    else:

        test_count = 0
        val_count = 0


    train_count = (
        count
        - val_count
        - test_count
    )


    # --------------------------------------------------------
    # Klasörler
    # --------------------------------------------------------

    train_class_dir = (
        train_dir
        / label
    )

    val_class_dir = (
        val_dir
        / label
    )

    test_class_dir = (
        test_dir
        / label
    )


    train_class_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    if val_count > 0:

        val_class_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    if test_count > 0:

        test_class_dir.mkdir(
            parents=True,
            exist_ok=True
        )


    # --------------------------------------------------------
    # Dosyaları dağıt
    # --------------------------------------------------------

    test_images = (
        images[:test_count]
    )

    val_images = (
        images[
            test_count:
            test_count + val_count
        ]
    )

    train_images = (
        images[
            test_count + val_count:
        ]
    )


    for image in train_images:

        shutil.copy2(
            image,
            train_class_dir / image.name
        )


    for image in val_images:

        shutil.copy2(
            image,
            val_class_dir / image.name
        )


    for image in test_images:

        shutil.copy2(
            image,
            test_class_dir / image.name
        )


    print(
        f"{label:30s}"
        f"{len(train_images):4d} train   "
        f"{len(val_images):4d} val   "
        f"{len(test_images):4d} test"
    )


print()
print(
    f"Total images: {total_images}"
)


# ============================================================
# TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.RandomHorizontalFlip(),

    transforms.RandomRotation(
        10
    ),

    transforms.ColorJitter(
        brightness=0.2,
        contrast=0.2,
        saturation=0.2
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


eval_transform = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
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
# DATASETS
# ============================================================

print()
print("=" * 60)
print("LOADING DATA")
print("=" * 60)


train_dataset = datasets.ImageFolder(
    train_dir,
    transform=train_transform
)


val_dataset = datasets.ImageFolder(
    val_dir,
    transform=eval_transform
)


test_dataset = datasets.ImageFolder(
    test_dir,
    transform=eval_transform
)


print(
    f"Train: {len(train_dataset)}"
)

print(
    f"Validation: {len(val_dataset)}"
)

print(
    f"Test: {len(test_dataset)}"
)

print(
    f"Classes: {len(train_dataset.classes)}"
)


# ============================================================
# DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)


val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)


test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)


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


# ============================================================
# MODEL
# ============================================================

print()
print("=" * 60)
print("LOADING MODEL")
print("=" * 60)


model = models.resnet18(
    weights=models.ResNet18_Weights.DEFAULT
)


num_classes = len(
    train_dataset.classes
)


model.fc = nn.Linear(
    model.fc.in_features,
    num_classes
)


model = model.to(
    device
)


# ============================================================
# LOSS / OPTIMIZER
# ============================================================

criterion = nn.CrossEntropyLoss()


optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=0.0001
)


# ============================================================
# EVALUATION FUNCTION
# ============================================================

def evaluate(loader):

    model.eval()

    total_loss = 0.0

    correct = 0

    total = 0


    with torch.no_grad():

        for images, labels in loader:

            images = images.to(
                device
            )

            labels = labels.to(
                device
            )


            outputs = model(
                images
            )


            loss = criterion(
                outputs,
                labels
            )


            total_loss += (
                loss.item()
                * images.size(0)
            )


            predictions = (
                outputs.argmax(
                    dim=1
                )
            )


            correct += (
                predictions == labels
            ).sum().item()


            total += (
                labels.size(0)
            )


    if total == 0:

        return 0, 0


    return (
        total_loss / total,
        correct / total
    )


# ============================================================
# TRAINING
# ============================================================

print()
print("=" * 60)
print("TRAINING")
print("=" * 60)

print()
print(
    f"Epochs: {EPOCHS}"
)

print(
    f"Batch size: {BATCH_SIZE}"
)

print(
    f"Learning rate: {LEARNING_RATE}"
)

print(
    f"Device: {device}"
)


best_val_accuracy = 0.0

best_state = None


for epoch in range(
    EPOCHS
):

    model.train()


    running_loss = 0.0

    correct = 0

    total = 0


    for images, labels in train_loader:

        images = images.to(
            device
        )

        labels = labels.to(
            device
        )


        optimizer.zero_grad()


        outputs = model(
            images
        )


        loss = criterion(
            outputs,
            labels
        )


        loss.backward()


        optimizer.step()


        running_loss += (
            loss.item()
            * images.size(0)
        )


        predictions = (
            outputs.argmax(
                dim=1
            )
        )


        correct += (
            predictions == labels
        ).sum().item()


        total += (
            labels.size(0)
        )


    train_loss = (
        running_loss / total
    )

    train_accuracy = (
        correct / total
    )


    val_loss, val_accuracy = (
        evaluate(
            val_loader
        )
    )


    print()
    print(
        f"Epoch {epoch + 1}/{EPOCHS}"
    )

    print(
        f"Train Loss: "
        f"{train_loss:.4f}"
    )

    print(
        f"Train Accuracy: "
        f"{train_accuracy:.2%}"
    )

    print(
        f"Val Loss: "
        f"{val_loss:.4f}"
    )

    print(
        f"Val Accuracy: "
        f"{val_accuracy:.2%}"
    )


    # --------------------------------------------------------
    # En iyi modeli sakla
    # --------------------------------------------------------

    if val_accuracy > best_val_accuracy:

        best_val_accuracy = (
            val_accuracy
        )

        best_state = {
            key: value.cpu().clone()
            for key, value
            in model.state_dict().items()
        }


# ============================================================
# BEST MODEL'I GERİ YÜKLE
# ============================================================

if best_state is not None:

    model.load_state_dict(
        best_state
    )


model = model.to(
    device
)


# ============================================================
# TEST
# ============================================================

print()
print("=" * 60)
print("TEST")
print("=" * 60)


test_loss, test_accuracy = (
    evaluate(
        test_loader
    )
)


print(
    f"Test Loss: "
    f"{test_loss:.4f}"
)

print(
    f"Test Accuracy: "
    f"{test_accuracy:.2%}"
)


# ============================================================
# MODEL KAYDET
# ============================================================

model_output = (
    Path(__file__).resolve().parent.parent
    / "models"
    / MODEL_NAME
)


model_output.parent.mkdir(
    parents=True,
    exist_ok=True
)


checkpoint = {
    "model_state_dict":
        model.state_dict(),

    "classes":
        train_dataset.classes,

    "num_classes":
        num_classes,

    "image_size":
        IMAGE_SIZE,

    "model":
        "resnet18",

    "best_val_accuracy":
        best_val_accuracy,

    "test_accuracy":
        test_accuracy
}


torch.save(
    checkpoint,
    model_output
)


print()
print("=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print()

print(
    "Model saved to:"
)

print(
    model_output
)

print()

print(
    f"Best validation accuracy: "
    f"{best_val_accuracy:.2%}"
)

print(
    f"Final test accuracy: "
    f"{test_accuracy:.2%}"
)