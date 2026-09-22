from pathlib import Path
from collections import Counter
import random
import shutil

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models


# ============================================================
# SETTINGS
# ============================================================

MIN_IMAGES_PER_CLASS = 10

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

BATCH_SIZE = 16
EPOCHS = 3

LEARNING_RATE = 0.0001

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

SEED = 42


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# DEVICE
# ============================================================

if torch.cuda.is_available():

    device = torch.device("cuda")

    print()
    print("CUDA available.")
    print("Using GPU:", torch.cuda.get_device_name(0))

else:

    device = torch.device("cpu")

    print()
    print("CUDA not available.")
    print("Using CPU.")


# ============================================================
# DATASET PATH
# ============================================================

source_dir = Path(
    input("\nDataset klasörünün yolunu gir: ").strip()
)

processed_dir = source_dir / "processed"

if not processed_dir.exists():

    print()
    print("Hata: 'processed' klasörü bulunamadı.")
    print()
    exit()


# ============================================================
# FIND CLASSES
# ============================================================

print()
print("Scanning dataset...")
print("-" * 60)


class_images = {}


for category_dir in processed_dir.iterdir():

    if not category_dir.is_dir():
        continue

    for style_dir in category_dir.iterdir():

        if not style_dir.is_dir():
            continue

        class_name = f"{category_dir.name}_{style_dir.name}"

        images = []

        for image_path in style_dir.iterdir():

            if not image_path.is_file():
                continue

            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            images.append(image_path)

        class_images[class_name] = images


# ============================================================
# SHOW ORIGINAL DATASET
# ============================================================

print()
print("Original classes:")
print("-" * 60)

for class_name in sorted(class_images):

    print(
        f"{class_name:<35} "
        f"{len(class_images[class_name])}"
    )


print()
print("Total classes found:", len(class_images))


# ============================================================
# FILTER SMALL CLASSES
# ============================================================

valid_classes = {}
skipped_classes = {}


for class_name, images in class_images.items():

    if len(images) < MIN_IMAGES_PER_CLASS:

        skipped_classes[class_name] = len(images)

    else:

        valid_classes[class_name] = images


# ============================================================
# SHOW SKIPPED CLASSES
# ============================================================

print()
print("=" * 60)
print("SKIPPED CLASSES")
print("=" * 60)

if skipped_classes:

    for class_name in sorted(skipped_classes):

        print(
            f"{class_name:<35} "
            f"{skipped_classes[class_name]} images"
        )

else:

    print("None")


# ============================================================
# SHOW TRAINING CLASSES
# ============================================================

print()
print("=" * 60)
print("CLASSES USED FOR TRAINING")
print("=" * 60)

for class_name in sorted(valid_classes):

    print(
        f"{class_name:<35} "
        f"{len(valid_classes[class_name])} images"
    )


print()
print("Training classes:", len(valid_classes))


# ============================================================
# CHECK
# ============================================================

if len(valid_classes) < 2:

    print()
    print(
        "Hata: Eğitim için en az 2 class gerekiyor."
    )

    exit()


# ============================================================
# CREATE TRAINING DATA FOLDER
# ============================================================

training_data_dir = source_dir / "training_data"


if training_data_dir.exists():

    print()
    print("Existing training_data folder found.")
    print("Removing it...")

    shutil.rmtree(training_data_dir)


train_dir = training_data_dir / "train"
val_dir = training_data_dir / "val"
test_dir = training_data_dir / "test"


train_dir.mkdir(parents=True)
val_dir.mkdir(parents=True)
test_dir.mkdir(parents=True)


# ============================================================
# SPLIT DATASET
# ============================================================

print()
print("=" * 60)
print("CREATING TRAIN / VAL / TEST SPLIT")
print("=" * 60)


for class_name in sorted(valid_classes):

    images = valid_classes[class_name].copy()

    random.shuffle(images)

    total = len(images)

    # --------------------------------------------------------
    # Small dataset handling
    # --------------------------------------------------------

    test_count = max(1, round(total * TEST_RATIO))
    val_count = max(1, round(total * VAL_RATIO))

    train_count = total - val_count - test_count

    # Make sure at least one training image remains.
    if train_count < 1:

        train_count = 1

        if val_count > 1:
            val_count -= 1

        elif test_count > 1:
            test_count -= 1

    train_images = images[:train_count]

    val_images = images[
        train_count:
        train_count + val_count
    ]

    test_images = images[
        train_count + val_count:
    ]

    # --------------------------------------------------------
    # Destination directories
    # --------------------------------------------------------

    class_train_dir = train_dir / class_name
    class_val_dir = val_dir / class_name
    class_test_dir = test_dir / class_name

    class_train_dir.mkdir(parents=True)
    class_val_dir.mkdir(parents=True)
    class_test_dir.mkdir(parents=True)

    # --------------------------------------------------------
    # Copy images
    # --------------------------------------------------------

    for image_path in train_images:

        shutil.copy2(
            image_path,
            class_train_dir / image_path.name
        )

    for image_path in val_images:

        shutil.copy2(
            image_path,
            class_val_dir / image_path.name
        )

    for image_path in test_images:

        shutil.copy2(
            image_path,
            class_test_dir / image_path.name
        )

    print(
        f"{class_name:<35} "
        f"{len(train_images):>3} train   "
        f"{len(val_images):>3} val   "
        f"{len(test_images):>3} test"
    )


# ============================================================
# TRANSFORMS
# ============================================================

train_transform = transforms.Compose([

    transforms.Resize((224, 224)),

    transforms.RandomHorizontalFlip(),

    transforms.RandomRotation(10),

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
# LOAD DATASETS
# ============================================================

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


# ============================================================
# DATA LOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# DATASET INFORMATION
# ============================================================

print()
print("=" * 60)
print("DATASET")
print("=" * 60)

print("Train images:", len(train_dataset))
print("Validation images:", len(val_dataset))
print("Test images:", len(test_dataset))

print()
print("Classes:")

for index, class_name in enumerate(train_dataset.classes):

    print(
        f"{index:>2}  {class_name}"
    )


print()
print("Total classes:", len(train_dataset.classes))


# ============================================================
# MODEL
# ============================================================

print()
print("=" * 60)
print("LOADING MODEL")
print("=" * 60)


weights = models.ResNet18_Weights.DEFAULT

model = models.resnet18(
    weights=weights
)


# Replace final layer.

number_of_classes = len(train_dataset.classes)

model.fc = nn.Linear(
    model.fc.in_features,
    number_of_classes
)


model = model.to(device)


# ============================================================
# LOSS + OPTIMIZER
# ============================================================

criterion = nn.CrossEntropyLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# TRAINING FUNCTION
# ============================================================

def train_one_epoch():

    model.train()

    running_loss = 0.0

    correct = 0
    total = 0

    for images, labels in train_loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            labels
        )

        loss.backward()

        optimizer.step()

        running_loss += (
            loss.item() *
            images.size(0)
        )

        _, predicted = torch.max(
            outputs,
            1
        )

        total += labels.size(0)

        correct += (
            predicted == labels
        ).sum().item()

    epoch_loss = (
        running_loss /
        total
    )

    epoch_accuracy = (
        correct /
        total
    )

    return epoch_loss, epoch_accuracy


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def evaluate(loader):

    model.eval()

    running_loss = 0.0

    correct = 0
    total = 0

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            running_loss += (
                loss.item() *
                images.size(0)
            )

            _, predicted = torch.max(
                outputs,
                1
            )

            total += labels.size(0)

            correct += (
                predicted == labels
            ).sum().item()

    epoch_loss = (
        running_loss /
        total
    )

    epoch_accuracy = (
        correct /
        total
    )

    return epoch_loss, epoch_accuracy


# ============================================================
# TRAIN
# ============================================================

print()
print("=" * 60)
print("TRAINING")
print("=" * 60)

print()
print("Epochs:", EPOCHS)
print("Batch size:", BATCH_SIZE)
print("Learning rate:", LEARNING_RATE)
print("Device:", device)


for epoch in range(EPOCHS):

    train_loss, train_accuracy = (
        train_one_epoch()
    )

    val_loss, val_accuracy = (
        evaluate(val_loader)
    )

    print()

    print(
        f"Epoch {epoch + 1}/{EPOCHS}"
    )

    print(
        f"Train Loss: {train_loss:.4f}"
    )

    print(
        f"Train Accuracy: "
        f"{train_accuracy * 100:.2f}%"
    )

    print(
        f"Val Loss: {val_loss:.4f}"
    )

    print(
        f"Val Accuracy: "
        f"{val_accuracy * 100:.2f}%"
    )


# ============================================================
# TEST
# ============================================================

print()
print("=" * 60)
print("TEST")
print("=" * 60)


test_loss, test_accuracy = evaluate(
    test_loader
)


print(
    f"Test Loss: {test_loss:.4f}"
)

print(
    f"Test Accuracy: "
    f"{test_accuracy * 100:.2f}%"
)


# ============================================================
# SAVE MODEL
# ============================================================

models_dir = source_dir / "models"

models_dir.mkdir(
    parents=True,
    exist_ok=True
)


model_path = (
    models_dir /
    "shoe_classifier.pth"
)


torch.save({

    "model_state_dict":
        model.state_dict(),

    "classes":
        train_dataset.classes,

    "class_to_idx":
        train_dataset.class_to_idx

}, model_path)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print()

print(
    "Model saved to:"
)

print(
    model_path
)

print()

print(
    f"Final test accuracy: "
    f"{test_accuracy * 100:.2f}%"
)

print()
