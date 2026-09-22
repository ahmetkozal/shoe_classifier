from pathlib import Path
import random
import shutil

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models


# --------------------------------------------------
# AYARLAR
# --------------------------------------------------

IMAGE_SIZE = 224

BATCH_SIZE = 16

EPOCHS = 10

LEARNING_RATE = 0.0001

SEED = 42


# --------------------------------------------------
# RANDOM SEED
# --------------------------------------------------

random.seed(SEED)
torch.manual_seed(SEED)


# --------------------------------------------------
# KLASÖR SEÇ
# --------------------------------------------------

source_dir = Path(
    input("Dataset klasörünün yolunu gir: ").strip()
)

processed_dir = source_dir / "processed"

if not processed_dir.exists():

    print()
    print("Hata: 'processed' klasörü bulunamadı.")
    exit()


# --------------------------------------------------
# TRAINING DATASET KLASÖRÜ
# --------------------------------------------------

training_dir = source_dir / "training_data"

if training_dir.exists():

    print()
    print("training_data klasörü zaten mevcut.")
    print("Eski klasör siliniyor...")

    shutil.rmtree(training_dir)


train_dir = training_dir / "train"
val_dir = training_dir / "val"
test_dir = training_dir / "test"

train_dir.mkdir(
    parents=True
)

val_dir.mkdir(
    parents=True
)

test_dir.mkdir(
    parents=True
)


# --------------------------------------------------
# CLASS'LARI BUL
# --------------------------------------------------

classes = []

for category_dir in sorted(
    processed_dir.iterdir()
):

    if not category_dir.is_dir():
        continue

    for style_dir in sorted(
        category_dir.iterdir()
    ):

        if not style_dir.is_dir():
            continue

        class_name = (
            f"{category_dir.name}_{style_dir.name}"
        )

        classes.append(
            (
                class_name,
                style_dir
            )
        )


print()
print("Classes found:")
print("-" * 50)

for class_name, _ in classes:

    print(
        class_name
    )


print()
print(
    f"Total classes: {len(classes)}"
)


# --------------------------------------------------
# DATASET'İ TRAIN / VAL / TEST OLARAK BÖL
# --------------------------------------------------

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


for class_name, class_dir in classes:

    images = [
        image
        for image in class_dir.iterdir()
        if (
            image.is_file()
            and image.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    ]


    random.shuffle(
        images
    )


    total = len(images)

    train_count = int(
        total * 0.70
    )

    val_count = int(
        total * 0.15
    )


    train_images = images[
        :train_count
    ]

    val_images = images[
        train_count:
        train_count + val_count
    ]

    test_images = images[
        train_count + val_count:
    ]


    # --------------------------------------------------
    # CLASS KLASÖRLERİ
    # --------------------------------------------------

    train_class_dir = (
        train_dir / class_name
    )

    val_class_dir = (
        val_dir / class_name
    )

    test_class_dir = (
        test_dir / class_name
    )


    train_class_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    val_class_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    test_class_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------
    # DOSYALARI KOPYALA
    # --------------------------------------------------

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


    print()
    print(
        f"{class_name:<35}"
        f"{len(train_images):>4} train  "
        f"{len(val_images):>4} val  "
        f"{len(test_images):>4} test"
    )


# --------------------------------------------------
# IMAGE TRANSFORMS
# --------------------------------------------------

train_transform = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.RandomHorizontalFlip(),

    transforms.RandomRotation(
        10
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


# --------------------------------------------------
# DATASET
# --------------------------------------------------

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


# --------------------------------------------------
# DATALOADER
# --------------------------------------------------

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


# --------------------------------------------------
# DEVICE
# --------------------------------------------------

if torch.cuda.is_available():

    device = torch.device(
        "cuda"
    )

else:

    device = torch.device(
        "cpu"
    )


print()
print(
    f"Using device: {device}"
)


# --------------------------------------------------
# MODEL
# --------------------------------------------------

print()
print("Loading pretrained model...")


model = models.resnet18(
    weights=models.ResNet18_Weights.DEFAULT
)


# --------------------------------------------------
# SON CLASSIFIER KATMANI
# --------------------------------------------------

number_of_classes = len(
    train_dataset.classes
)

model.fc = nn.Linear(
    model.fc.in_features,
    number_of_classes
)


model = model.to(
    device
)


# --------------------------------------------------
# LOSS
# --------------------------------------------------

criterion = nn.CrossEntropyLoss()


# --------------------------------------------------
# OPTIMIZER
# --------------------------------------------------

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# --------------------------------------------------
# TRAINING
# --------------------------------------------------

print()
print("=" * 60)
print("TRAINING")
print("=" * 60)


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


        _, predicted = torch.max(
            outputs,
            1
        )


        total += labels.size(0)

        correct += (
            predicted == labels
        ).sum().item()


    train_loss = (
        running_loss / total
    )

    train_accuracy = (
        correct / total
    )


    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    model.eval()

    val_correct = 0
    val_total = 0

    val_loss_total = 0.0


    with torch.no_grad():

        for images, labels in val_loader:

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


            val_loss_total += (
                loss.item()
                * images.size(0)
            )


            _, predicted = torch.max(
                outputs,
                1
            )


            val_total += (
                labels.size(0)
            )

            val_correct += (
                predicted == labels
            ).sum().item()


    val_loss = (
        val_loss_total / val_total
    )

    val_accuracy = (
        val_correct / val_total
    )


    print(
        f"Epoch {epoch + 1:02d}/{EPOCHS} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Train Acc: {train_accuracy:.2%} | "
        f"Val Loss: {val_loss:.4f} | "
        f"Val Acc: {val_accuracy:.2%}"
    )


# --------------------------------------------------
# TEST
# --------------------------------------------------

print()
print("=" * 60)
print("TEST")
print("=" * 60)


model.eval()

test_correct = 0
test_total = 0


with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(
            device
        )

        labels = labels.to(
            device
        )


        outputs = model(
            images
        )


        _, predicted = torch.max(
            outputs,
            1
        )


        test_total += (
            labels.size(0)
        )

        test_correct += (
            predicted == labels
        ).sum().item()


test_accuracy = (
    test_correct / test_total
)


print(
    f"Test Accuracy: {test_accuracy:.2%}"
)


# --------------------------------------------------
# MODEL KAYDET
# --------------------------------------------------

models_dir = source_dir / "models"

models_dir.mkdir(
    exist_ok=True
)


model_path = (
    models_dir / "shoe_classifier.pth"
)


torch.save(
    {
        "model_state_dict":
            model.state_dict(),

        "classes":
            train_dataset.classes
    },
    model_path
)


print()
print(
    f"Model saved to:"
)

print(
    model_path
)

print()
print("=" * 60)
print("Training complete.")
print("=" * 60)