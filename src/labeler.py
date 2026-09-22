import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from PIL import Image, ImageTk
import shutil
import json


CATEGORY_STYLES = {
    "terlik": ["klasik", "topuklu", "casual", "comfort"],
    "sandalet": ["klasik", "topuklu", "casual", "comfort"],
    "basanojki": ["klasik", "topuklu", "comfort"],
    "tufli": ["klasik", "comfort", "topuklu"],
    "babet": ["klasik", "comfort", "casual"],
    "bot": ["klasik", "topuklu", "casual"],
    "cizme": ["klasik", "topuklu", "yarim_cizme"]
}


# --------------------------------------------------
# KLASÖR SEÇ
# --------------------------------------------------

root = tk.Tk()
root.withdraw()

selected_folder = filedialog.askdirectory(
    title="Fotoğrafların bulunduğu klasörü seç"
)

if not selected_folder:
    root.destroy()
    exit()

source_dir = Path(selected_folder)
processed_dir = source_dir / "processed"
progress_file = source_dir / ".shoe_labeler_progress.json"


# --------------------------------------------------
# FOTOĞRAFLARI BUL
# --------------------------------------------------

images = [
    file
    for file in source_dir.iterdir()
    if file.is_file()
    and file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
]

images.sort(key=lambda file: file.name.lower())

print(f"Folder: {source_dir}")
print(f"Images: {len(images)}")


# --------------------------------------------------
# PROGRESS YÜKLE
# --------------------------------------------------

current_index = 0

if progress_file.exists():

    try:
        with open(progress_file, "r", encoding="utf-8") as file:
            progress = json.load(file)

        current_index = progress.get("current_index", 0)

        print(f"Resuming from image {current_index + 1}")

    except (json.JSONDecodeError, OSError):
        print("Progress file could not be read. Starting from beginning.")


# Eğer progress dosyası artık dataset'ten büyükse
if current_index >= len(images):
    current_index = 0


# --------------------------------------------------
# DEĞİŞKENLER
# --------------------------------------------------

selected_category = None

# Undo için geçmiş
history = []


# --------------------------------------------------
# PROGRESS KAYDET
# --------------------------------------------------

def save_progress():

    progress = {
        "current_index": current_index
    }

    with open(
        progress_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            progress,
            file,
            indent=4
        )


# --------------------------------------------------
# FOTOĞRAF GÖSTER
# --------------------------------------------------

def show_image():

    if current_index >= len(images):
        return

    file = images[current_index]

    try:
        image = Image.open(file)
        image.thumbnail((800, 600))

        photo = ImageTk.PhotoImage(image)

        image_label.config(image=photo)
        image_label.image = photo

        progress_label.config(
            text=(
                f"{current_index + 1} / {len(images)}\n"
                f"{file.name}"
            )
        )

    except Exception as error:

        progress_label.config(
            text=f"Could not open: {file.name}\n{error}"
        )


# --------------------------------------------------
# KATEGORİ SEÇ
# --------------------------------------------------

def choose_category(category):

    global selected_category

    selected_category = category

    category_label.config(
        text=f"Kategori: {category}"
    )

    show_styles(category)


# --------------------------------------------------
# STİLLERİ GÖSTER
# --------------------------------------------------

def show_styles(category):

    for widget in style_frame.winfo_children():
        widget.destroy()

    styles = CATEGORY_STYLES[category]

    for index, style in enumerate(styles, start=1):

        button = tk.Button(
            style_frame,
            text=f"{index} - {style}",
            width=20,
            command=lambda s=style: save_image(s)
        )

        button.pack(pady=3)


# --------------------------------------------------
# FOTOĞRAFI ETİKETLE
# --------------------------------------------------

def save_image(style):

    global current_index
    global selected_category

    file = images[current_index]

    output_dir = (
        processed_dir
        / selected_category
        / style
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = output_dir / file.name

    # Eğer aynı dosya daha önce varsa üzerine yaz
    shutil.copy2(
        file,
        destination
    )

    # Undo için kaydet
    history.append({
        "index": current_index,
        "destination": str(destination)
    })

    current_index += 1
    selected_category = None

    save_progress()

    show_next_image()


# --------------------------------------------------
# FOTOĞRAFI ATLA
# --------------------------------------------------

def skip_image():

    global current_index
    global selected_category

    # Undo için skip işlemini de kaydet
    history.append({
        "index": current_index,
        "destination": None
    })

    current_index += 1
    selected_category = None

    save_progress()

    show_next_image()


# --------------------------------------------------
# SONRAKİ FOTOĞRAF
# --------------------------------------------------

def show_next_image():

    if current_index >= len(images):

        progress_label.config(
            text="Dataset tamamlandı!"
        )

        image_label.config(image="")
        category_label.config(
            text="Dataset tamamlandı!"
        )

        for widget in style_frame.winfo_children():
            widget.destroy()

        return

    category_label.config(
        text="Kategori seç:"
    )

    for widget in style_frame.winfo_children():
        widget.destroy()

    show_image()


# --------------------------------------------------
# UNDO
# --------------------------------------------------

def undo():

    global current_index
    global selected_category

    if not history:
        return

    last_action = history.pop()

    previous_index = last_action["index"]
    destination = last_action["destination"]

    # Etiketlenmiş bir dosyaysa processed'dan sil
    if destination is not None:

        destination_path = Path(destination)

        if destination_path.exists():
            destination_path.unlink()

    current_index = previous_index
    selected_category = None

    save_progress()

    category_label.config(
        text="Kategori seç:"
    )

    for widget in style_frame.winfo_children():
        widget.destroy()

    show_image()


# --------------------------------------------------
# KLAVYE KONTROLÜ
# --------------------------------------------------

def key_pressed(event):

    global selected_category

    key = event.char.lower()

    # U = Undo
    if key == "u":
        undo()
        return

    # S = Skip
    if key == "s":
        skip_image()
        return

    # Kategori seçilmediyse
    if selected_category is None:

        categories = list(CATEGORY_STYLES.keys())

        if key in "1234567":

            index = int(key) - 1

            if index < len(categories):

                choose_category(
                    categories[index]
                )

    # Kategori seçildiyse
    else:

        styles = CATEGORY_STYLES[
            selected_category
        ]

        if key.isdigit():

            index = int(key) - 1

            if index < len(styles):

                save_image(
                    styles[index]
                )


# --------------------------------------------------
# PROGRAMDAN ÇIKIŞ
# --------------------------------------------------

def quit_program(event=None):

    save_progress()
    root.destroy()


# --------------------------------------------------
# GUI
# --------------------------------------------------

root.deiconify()

root.title(
    "Shoe Dataset Labeler"
)

root.geometry(
    "1000x800"
)


image_label = tk.Label(root)
image_label.pack(pady=10)


progress_label = tk.Label(
    root,
    text="",
    font=("Arial", 12)
)

progress_label.pack()


category_label = tk.Label(
    root,
    text="Kategori seç:",
    font=("Arial", 16)
)

category_label.pack(pady=10)


category_frame = tk.Frame(root)
category_frame.pack()


# Kategori butonları

for index, category in enumerate(
    CATEGORY_STYLES,
    start=1
):

    button = tk.Button(
        category_frame,
        text=f"{index} - {category}",
        width=15,
        command=lambda c=category:
            choose_category(c)
    )

    button.pack(
        side=tk.LEFT,
        padx=3
    )


style_frame = tk.Frame(root)
style_frame.pack(pady=20)


# Klavye eventleri

root.bind(
    "<Key>",
    key_pressed
)

root.bind(
    "<Escape>",
    quit_program
)


# İlk fotoğraf

if images:
    show_image()

else:
    progress_label.config(
        text="Fotoğraf bulunamadı!"
    )


root.mainloop()