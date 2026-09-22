import csv
from pathlib import Path
from collections import Counter, defaultdict

import tkinter as tk
from tkinter import filedialog


# ============================================================
# AYARLAR
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


# ============================================================
# KLASÖR SEÇME
# ============================================================

def select_folder(title):

    root = tk.Tk()
    root.withdraw()

    folder = filedialog.askdirectory(
        title=title
    )

    root.destroy()

    if not folder:
        raise SystemExit("Klasör seçilmedi.")

    return Path(folder)


# ============================================================
# GERÇEK ETİKETLERİ OKU
# ============================================================

def load_ground_truth(processed_dir):

    ground_truth = {}

    for category_dir in processed_dir.iterdir():

        if not category_dir.is_dir():
            continue

        category = category_dir.name

        for style_dir in category_dir.iterdir():

            if not style_dir.is_dir():
                continue

            style = style_dir.name

            label = f"{category}_{style}"

            for image in style_dir.iterdir():

                if not image.is_file():
                    continue

                if image.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue

                filename = image.name

                ground_truth[filename] = label

    return ground_truth


# ============================================================
# AI TAHMİNLERİNİ OKU
# ============================================================

def load_predictions(csv_path):

    predictions = {}

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            filename = row["filename"]

            prediction = row["prediction"]

            confidence = float(
                row["confidence"]
            )

            predictions[filename] = {
                "prediction": prediction,
                "confidence": confidence,
            }

    return predictions


# ============================================================
# MAIN
# ============================================================

print()
print("=" * 60)
print("SHOE CLASSIFIER - MODEL EVALUATION")
print("=" * 60)
print()


# ------------------------------------------------------------
# Gerçek etiketli processed
# ------------------------------------------------------------

print(
    "Önce MANUEL / GERÇEK etiketlerin bulunduğu "
    "processed klasörünü seç."
)

ground_truth_dir = select_folder(
    "MANUEL / GERÇEK ETİKETLERİN bulunduğu processed klasörünü seç"
)

print(
    f"Gerçek etiketler: {ground_truth_dir}"
)

print()


# ------------------------------------------------------------
# AI predictions
# ------------------------------------------------------------

print(
    "Şimdi predictions.csv dosyasının bulunduğu "
    "dataset klasörünü seç."
)

dataset_dir = select_folder(
    "predictions.csv dosyasının bulunduğu dataset klasörünü seç"
)

predictions_csv = (
    dataset_dir
    / "predictions.csv"
)

if not predictions_csv.exists():

    print()
    print("HATA:")
    print(
        f"predictions.csv bulunamadı:\n"
        f"{predictions_csv}"
    )

    raise SystemExit


print(
    f"AI predictions: {predictions_csv}"
)

print()


# ============================================================
# VERİLERİ YÜKLE
# ============================================================

ground_truth = load_ground_truth(
    ground_truth_dir
)

predictions = load_predictions(
    predictions_csv
)


print(
    f"Gerçek etiketli fotoğraf: "
    f"{len(ground_truth)}"
)

print(
    f"AI tahminleri: "
    f"{len(predictions)}"
)

print()


# ============================================================
# KARŞILAŞTIR
# ============================================================

correct = 0
wrong = 0
missing = 0

results = []

confusion = defaultdict(
    Counter
)

confidence_correct = []
confidence_wrong = []


for filename, ai_data in predictions.items():

    ai_prediction = ai_data["prediction"]

    confidence = ai_data["confidence"]

    true_label = ground_truth.get(
        filename
    )

    # --------------------------------------------------------
    # Gerçek etiket bulunamadı
    # --------------------------------------------------------

    if true_label is None:

        missing += 1

        results.append({
            "filename": filename,
            "true_label": "",
            "prediction": ai_prediction,
            "confidence": confidence,
            "result": "MISSING",
        })

        continue


    # --------------------------------------------------------
    # Doğru / yanlış
    # --------------------------------------------------------

    if true_label == ai_prediction:

        correct += 1

        result = "CORRECT"

        confidence_correct.append(
            confidence
        )

    else:

        wrong += 1

        result = "WRONG"

        confidence_wrong.append(
            confidence
        )

    confusion[
        true_label
    ][
        ai_prediction
    ] += 1


    results.append({
        "filename": filename,
        "true_label": true_label,
        "prediction": ai_prediction,
        "confidence": confidence,
        "result": result,
    })


# ============================================================
# ACCURACY
# ============================================================

evaluated = correct + wrong

if evaluated > 0:

    accuracy = (
        correct / evaluated
    )

else:

    accuracy = 0


print("=" * 60)
print("SONUÇ")
print("=" * 60)

print()

print(
    f"Karşılaştırılan : {evaluated}"
)

print(
    f"Doğru           : {correct}"
)

print(
    f"Yanlış          : {wrong}"
)

print(
    f"Eşleşmeyen      : {missing}"
)

print(
    f"Accuracy        : {accuracy:.2%}"
)

print()


# ============================================================
# CONFIDENCE ANALİZİ
# ============================================================

if confidence_correct:

    average_correct = (
        sum(confidence_correct)
        / len(confidence_correct)
    )

    print(
        f"Doğru tahminlerin ortalama confidence: "
        f"{average_correct:.2%}"
    )


if confidence_wrong:

    average_wrong = (
        sum(confidence_wrong)
        / len(confidence_wrong)
    )

    print(
        f"Yanlış tahminlerin ortalama confidence: "
        f"{average_wrong:.2%}"
    )


# ============================================================
# CONFUSION MATRIX
# ============================================================

print()
print("=" * 60)
print("EN ÇOK KARIŞAN SINIFLAR")
print("=" * 60)
print()


confusion_pairs = []

for true_label, predictions_for_label in confusion.items():

    for predicted_label, count in predictions_for_label.items():

        if true_label == predicted_label:
            continue

        confusion_pairs.append(
            (
                count,
                true_label,
                predicted_label
            )
        )


confusion_pairs.sort(
    reverse=True
)


for count, true_label, predicted_label in confusion_pairs[:15]:

    print(
        f"{count:3d}  "
        f"{true_label:25s} -> "
        f"{predicted_label}"
    )


# ============================================================
# SINIF BAZINDA ACCURACY
# ============================================================

class_total = Counter()
class_correct = Counter()

for row in results:

    if row["result"] != "CORRECT" and \
       row["result"] != "WRONG":

        continue

    true_label = row["true_label"]

    class_total[true_label] += 1

    if row["result"] == "CORRECT":

        class_correct[true_label] += 1


print()
print("=" * 60)
print("SINIF BAZINDA SONUÇ")
print("=" * 60)
print()


class_results = []

for label in class_total:

    total = class_total[label]

    correct_count = class_correct[label]

    class_accuracy = (
        correct_count / total
    )

    class_results.append(
        (
            total,
            class_accuracy,
            label,
            correct_count
        )
    )


class_results.sort(
    key=lambda x: x[1]
)


for total, class_accuracy, label, correct_count in class_results:

    print(
        f"{label:25s} "
        f"{correct_count:3d}/{total:<3d} "
        f"({class_accuracy:.1%})"
    )


# ============================================================
# DETAYLI CSV
# ============================================================

output_csv = (
    dataset_dir
    / "evaluation_results.csv"
)


with open(
    output_csv,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "filename",
            "true_label",
            "prediction",
            "confidence",
            "result",
        ]
    )

    writer.writeheader()

    writer.writerows(
        results
    )


print()
print("=" * 60)

print(
    "Detaylı sonuçlar:"
)

print(
    output_csv
)

print("=" * 60)
