from pathlib import Path
from collections import Counter
from PIL import Image


# --------------------------------------------------
# AYARLAR
# --------------------------------------------------

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

CATEGORIES = [
    "terlik",
    "sandalet",
    "basanojki",
    "tufli",
    "babet",
    "bot",
    "cizme"
]


# --------------------------------------------------
# DATASET KLASÖRÜ
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
# DEĞİŞKENLER
# --------------------------------------------------

total_images = 0
valid_images = 0
corrupted_images = []

category_counts = Counter()
class_counts = Counter()

width_counts = Counter()
height_counts = Counter()

resolutions = Counter()


# --------------------------------------------------
# DATASET'İ KONTROL ET
# --------------------------------------------------

print()
print("Dataset kontrol ediliyor...")
print()


for category in CATEGORIES:

    category_dir = (
        processed_dir / category
    )

    if not category_dir.exists():
        continue


    for style_dir in category_dir.iterdir():

        if not style_dir.is_dir():
            continue


        style = style_dir.name

        class_name = (
            f"{category} / {style}"
        )


        for image_path in style_dir.iterdir():

            if not image_path.is_file():
                continue


            if (
                image_path.suffix.lower()
                not in IMAGE_EXTENSIONS
            ):
                continue


            total_images += 1

            category_counts[
                category
            ] += 1

            class_counts[
                class_name
            ] += 1


            # --------------------------------------------------
            # IMAGE KONTROLÜ
            # --------------------------------------------------

            try:

                with Image.open(
                    image_path
                ) as image:

                    image.verify()


                # verify() sonrasında resmi
                # tekrar açıyoruz.

                with Image.open(
                    image_path
                ) as image:

                    width, height = image.size


                valid_images += 1

                width_counts[
                    width
                ] += 1

                height_counts[
                    height
                ] += 1

                resolutions[
                    (width, height)
                ] += 1


            except Exception:

                corrupted_images.append(
                    image_path
                )


# --------------------------------------------------
# SONUÇLAR
# --------------------------------------------------

print("=" * 60)
print("DATASET VALIDATION")
print("=" * 60)


# --------------------------------------------------
# GENEL
# --------------------------------------------------

print()
print("General")
print("-" * 60)

print(
    f"Total images     : {total_images}"
)

print(
    f"Valid images     : {valid_images}"
)

print(
    f"Corrupted images : {len(corrupted_images)}"
)


# --------------------------------------------------
# KATEGORİLER
# --------------------------------------------------

print()
print("Categories")
print("-" * 60)

for category in CATEGORIES:

    count = category_counts[
        category
    ]

    print(
        f"{category:<15} : {count}"
    )


# --------------------------------------------------
# CLASS DAĞILIMI
# --------------------------------------------------

print()
print("Classes")
print("-" * 60)

for class_name, count in sorted(
    class_counts.items()
):

    print(
        f"{class_name:<30} : {count}"
    )


# --------------------------------------------------
# RESOLUTION
# --------------------------------------------------

print()
print("Resolutions")
print("-" * 60)

for resolution, count in (
    resolutions.most_common()
):

    width, height = resolution

    print(
        f"{width} x {height:<10} : {count}"
    )


# --------------------------------------------------
# BOZUK DOSYALAR
# --------------------------------------------------

if corrupted_images:

    print()
    print("Corrupted images")
    print("-" * 60)

    for image_path in corrupted_images:

        print(
            image_path
        )


# --------------------------------------------------
# CLASS BALANCE
# --------------------------------------------------

print()
print("Class Balance")
print("-" * 60)


if class_counts:

    smallest = min(
        class_counts.values()
    )

    largest = max(
        class_counts.values()
    )

    print(
        f"Smallest class : {smallest}"
    )

    print(
        f"Largest class  : {largest}"
    )


    if smallest > 0:

        ratio = (
            largest / smallest
        )

        print(
            f"Ratio          : {ratio:.2f}x"
        )


# --------------------------------------------------
# SONUÇ
# --------------------------------------------------

print()
print("=" * 60)

if corrupted_images:

    print(
        "WARNING: Corrupted images found."
    )

else:

    print(
        "OK: Dataset validation passed."
    )

print("=" * 60)