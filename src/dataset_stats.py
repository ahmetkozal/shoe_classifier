from pathlib import Path
from collections import Counter


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
# KLASÖR SEÇ
# --------------------------------------------------

source_dir = Path(
    input("Dataset klasörünün yolunu gir: ").strip()
)

processed_dir = source_dir / "processed"


if not processed_dir.exists():

    print(
        "\nHata: 'processed' klasörü bulunamadı."
    )

    exit()


# --------------------------------------------------
# SAYIMLAR
# --------------------------------------------------

category_counts = Counter()
style_counts = Counter()
category_style_counts = Counter()

total_images = 0


# --------------------------------------------------
# DATASET'İ TARA
# --------------------------------------------------

for category in CATEGORIES:

    category_dir = processed_dir / category

    if not category_dir.exists():
        continue


    for style_dir in category_dir.iterdir():

        if not style_dir.is_dir():
            continue


        category = category_dir.name
        style = style_dir.name


        for image in style_dir.iterdir():

            if not image.is_file():
                continue

            if image.suffix.lower() not in IMAGE_EXTENSIONS:
                continue


            total_images += 1

            category_counts[category] += 1

            style_counts[style] += 1

            category_style_counts[
                (category, style)
            ] += 1


# --------------------------------------------------
# BAŞLIK
# --------------------------------------------------

print()
print("=" * 50)
print("DATASET STATISTICS")
print("=" * 50)

print()

print(
    f"Total images: {total_images}"
)


# --------------------------------------------------
# CATEGORY
# --------------------------------------------------

print()
print("Categories")
print("-" * 50)


for category in CATEGORIES:

    count = category_counts[category]

    print(
        f"{category:<15} : {count}"
    )


# --------------------------------------------------
# STYLE
# --------------------------------------------------

print()
print("Styles")
print("-" * 50)


for style, count in style_counts.most_common():

    print(
        f"{style:<15} : {count}"
    )


# --------------------------------------------------
# CATEGORY / STYLE
# --------------------------------------------------

print()
print("Category / Style")
print("-" * 50)


for category in CATEGORIES:

    if category_counts[category] == 0:
        continue


    print()
    print(category)


    styles = [
        (style, count)
        for (cat, style), count
        in category_style_counts.items()
        if cat == category
    ]


    styles.sort()


    for style, count in styles:

        print(
            f"  {style:<15} : {count}"
        )


# --------------------------------------------------
# EN AZ / EN ÇOK SINIFLAR
# --------------------------------------------------

print()
print("Class Balance")
print("-" * 50)


if category_style_counts:

    sorted_classes = sorted(
        category_style_counts.items(),
        key=lambda x: x[1]
    )


    smallest = sorted_classes[:5]

    largest = sorted_classes[-5:]


    print()
    print("Smallest classes:")

    for (category, style), count in smallest:

        print(
            f"  {category} / {style}: {count}"
        )


    print()
    print("Largest classes:")

    for (category, style), count in reversed(largest):

        print(
            f"  {category} / {style}: {count}"
        )


# --------------------------------------------------
# SON
# --------------------------------------------------

print()
print("=" * 50)
print("Inspection complete.")
print("=" * 50)