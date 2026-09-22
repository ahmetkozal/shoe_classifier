from pathlib import Path
import csv
import shutil


# ============================================================
# SETTINGS
# ============================================================

CONFIDENCE_THRESHOLD = 0.70

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


# ============================================================
# INPUT
# ============================================================

source_dir = Path(
    input("\nFotoğraf klasörünün yolunu gir: ").strip()
)

csv_path = source_dir / "predictions.csv"

review_dir = source_dir / "review"


# ============================================================
# CHECK
# ============================================================

if not source_dir.exists():

    print("\nHata: Klasör bulunamadı.")
    exit()


if not csv_path.exists():

    print()
    print(
        "Hata: predictions.csv bulunamadı."
    )

    print()
    print(
        "Önce predict_folder.py çalıştır."
    )

    exit()


# ============================================================
# CREATE REVIEW FOLDER
# ============================================================

if review_dir.exists():

    print()
    print(
        "Mevcut review klasörü siliniyor..."
    )

    shutil.rmtree(review_dir)


review_dir.mkdir()


# ============================================================
# READ CSV
# ============================================================

review_results = []

total = 0
review_count = 0


with open(
    csv_path,
    "r",
    encoding="utf-8-sig"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        total += 1

        filename = row["filename"]

        prediction = row["prediction"]

        confidence = float(
            row["confidence"]
        )


        if confidence >= CONFIDENCE_THRESHOLD:

            continue


        image_path = source_dir / filename


        if not image_path.exists():

            print(
                f"Bulunamadı: {filename}"
            )

            continue


        # ----------------------------------------------------
        # Copy image
        # ----------------------------------------------------

        destination = (
            review_dir /
            filename
        )


        shutil.copy2(
            image_path,
            destination
        )


        review_results.append({

            "filename":
                filename,

            "prediction":
                prediction,

            "confidence":
                confidence

        })


        review_count += 1


# ============================================================
# CREATE REVIEW CSV
# ============================================================

review_csv = (
    review_dir /
    "review.csv"
)


with open(
    review_csv,
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


    for result in review_results:

        writer.writerow([

            result["filename"],

            result["prediction"],

            f"{result['confidence']:.4f}"

        ])


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("REVIEW DATASET")
print("=" * 60)

print()

print(
    "Total predictions:",
    total
)

print(
    "Low confidence:",
    review_count
)

print()

print(
    f"Threshold: "
    f"{CONFIDENCE_THRESHOLD * 100:.0f}%"
)

print()

print(
    "Review folder:"
)

print(
    review_dir
)

print()

print(
    "Review CSV:"
)

print(
    review_csv
)

print()
print("Done.")