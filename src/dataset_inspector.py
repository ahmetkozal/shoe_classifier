from pathlib import Path
from PIL import Image

DATASET = Path("data/raw")

images = []

for file in DATASET.iterdir():
    if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
        images.append(file)

print(f"Image count: {len(images)}")

for file in images[:10]:
    try:
        with Image.open(file) as image:
            print(file.name, image.size)
    except Exception:
        print(f"Could not open: {file.name}")