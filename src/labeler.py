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
processed_dir.mkdir(exist_ok=True)


# --------------------------------------------------
# FOTOĞRAFLARI BUL
# --------------------------------------------------

images = [
    file for file in source_dir.iterdir()
    if file.is_file()
    and file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
]

images.sort(key=lambda x: x.name.lower())

if not images:
    print("Fotoğraf bulunamadı.")
    root.destroy()
    exit()


# --------------------------------------------------
# PROGRESS DOSYASI
# --------------------------------------------------

progress_file = source_dir / ".shoe_labeler_progress.json"

current_index = 0

if progress_file.exists():
    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            progress = json.load(f)

        current_index = progress.get("current_index", 0)

    except (json.JSONDecodeError, OSError):
        current_index = 0


# --------------------------------------------------
# DEĞİŞKENLER
# --------------------------------------------------

selected_category = None
history = []


# --------------------------------------------------
# PROGRESS KAYDET
# --------------------------------------------------

def save_progress():
    data = {
        "current_index": current_index
    }

    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(data, f)


# --------------------------------------------------
# GUI
# --------------------------------------------------

root.deiconify()
root.title("Shoe Labeler")
root.geometry("1000x800")


# --------------------------------------------------
# BAŞLIK
# --------------------------------------------------

title_label = tk.Label(
    root,
    text="Shoe Image Labeler",
    font=("Arial", 20, "bold")
)

title_label.pack(pady=(10, 5))


# --------------------------------------------------
# İLERLEME BİLGİSİ
# --------------------------------------------------

progress_label = tk.Label(
    root,
    text="",
    font=("Arial", 13)
)

progress_label.pack(pady=5)


# --------------------------------------------------
# FOTOĞRAF
# --------------------------------------------------

image_label = tk.Label(root)
image_label.pack(pady=10)


# --------------------------------------------------
# DURUM
# --------------------------------------------------

status_label = tk.Label(
    root,
    text="Kategori seç",
    font=("Arial", 14, "bold")
)

status_label.pack(pady=5)


# --------------------------------------------------
# KATEGORİ BUTONLARI
# --------------------------------------------------

category_frame = tk.Frame(root)
category_frame.pack(pady=5)

category_buttons = {}

categories = list(CATEGORY_STYLES.keys())

for i, category in enumerate(categories, start=1):

    button = tk.Button(
        category_frame,
        text=f"{i} - {category}",
        width=15,
        command=lambda c=category: select_category(c)
    )

    button.grid(
        row=(i - 1) // 4,
        column=(i - 1) % 4,
        padx=4,
        pady=4
    )

    category_buttons[category] = button


# --------------------------------------------------
# STİL BUTONLARI
# --------------------------------------------------

style_frame = tk.Frame(root)
style_frame.pack(pady=5)

style_buttons = []


# --------------------------------------------------
# KLAVYE BİLGİSİ
# --------------------------------------------------

shortcut_label = tk.Label(
    root,
    text="1-7: Kategori    |    Stil numarası: Stil seç    |    U: Geri al    |    S: Atla    |    ESC: Çıkış",
    font=("Arial", 11)
)

shortcut_label.pack(pady=15)


# --------------------------------------------------
# İLERLEME GÜNCELLE
# --------------------------------------------------

def update_progress():

    labeled = current_index
    total = len(images)
    remaining = total - current_index

    if remaining < 0:
        remaining = 0

    progress_label.config(
        text=f"Etiketlenen: {labeled}    |    Kalan: {remaining}    |    Toplam: {total}"
    )


# --------------------------------------------------
# FOTOĞRAFI GÖSTER
# --------------------------------------------------

def show_image():

    global current_index

    update_progress()

    if current_index >= len(images):

        image_label.config(image="")
        image_label.image = None

        status_label.config(
            text="TÜM FOTOĞRAFLAR TAMAMLANDI!"
        )

        return

    image_path = images[current_index]

    try:
        image = Image.open(image_path)

        image.thumbnail((800, 550))

        photo = ImageTk.PhotoImage(image)

        image_label.config(image=photo)
        image_label.image = photo

        status_label.config(
            text=f"{image_path.name}"
        )

    except Exception as e:

        status_label.config(
            text=f"Fotoğraf açılamadı: {e}"
        )


# --------------------------------------------------
# KATEGORİ SEÇ
# --------------------------------------------------

def select_category(category):

    global selected_category

    selected_category = category

    status_label.config(
        text=f"{category} seçildi → stil seç"
    )

    # Eski stil butonlarını temizle
    for button in style_buttons:
        button.destroy()

    style_buttons.clear()

    styles = CATEGORY_STYLES[category]

    for i, style in enumerate(styles, start=1):

        button = tk.Button(
            style_frame,
            text=f"{i} - {style}",
            width=15,
            command=lambda s=style: save_image(s)
        )

        button.grid(
            row=0,
            column=i - 1,
            padx=4
        )

        style_buttons.append(button)


# --------------------------------------------------
# FOTOĞRAFI KAYDET
# --------------------------------------------------

def save_image(style):

    global current_index
    global selected_category

    if selected_category is None:
        return

    image_path = images[current_index]

    destination_dir = (
        processed_dir
        / selected_category
        / style
    )

    destination_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = destination_dir / image_path.name

    shutil.copy2(
        image_path,
        destination
    )

    # Undo için kaydet
    history.append(
        {
            "index": current_index,
            "destination": str(destination)
        }
    )

    current_index += 1

    selected_category = None

    save_progress()

    # Stil butonlarını temizle
    for button in style_buttons:
        button.destroy()

    style_buttons.clear()

    show_image()


# --------------------------------------------------
# FOTOĞRAFI ATLA
# --------------------------------------------------

def skip_image():

    global current_index
    global selected_category

    if current_index >= len(images):
        return

    history.append(
        {
            "index": current_index,
            "destination": None
        }
    )

    current_index += 1
    selected_category = None

    save_progress()

    for button in style_buttons:
        button.destroy()

    style_buttons.clear()

    show_image()


# --------------------------------------------------
# GERİ AL
# --------------------------------------------------

def undo():

    global current_index
    global selected_category

    if not history:
        status_label.config(
            text="Geri alınacak işlem yok."
        )
        return

    last_action = history.pop()

    current_index = last_action["index"]

    destination = last_action["destination"]

    if destination:

        destination_path = Path(destination)

        if destination_path.exists():
            destination_path.unlink()

    selected_category = None

    save_progress()

    for button in style_buttons:
        button.destroy()

    style_buttons.clear()

    show_image()


# --------------------------------------------------
# KLAVYE
# --------------------------------------------------

def key_pressed(event):

    key = event.keysym.lower()

    # U = Undo
    if key == "u":
        undo()

    # S = Skip
    elif key == "s":
        skip_image()

    # ESC = Çıkış
    elif key == "escape":
        save_progress()
        root.destroy()

    # Eğer kategori seçilmişse:
    # 1-4 artık stil seçmek için kullanılır
    elif selected_category is not None and key in ["1", "2", "3", "4"]:

        number = int(key)

        styles = CATEGORY_STYLES[selected_category]

        if number <= len(styles):
            save_image(styles[number - 1])

    # Kategori henüz seçilmemişse:
    # 1-7 kategori seçmek için kullanılır
    elif selected_category is None and key in [
        "1", "2", "3", "4", "5", "6", "7"
    ]:

        number = int(key)

        if number <= len(categories):
            select_category(categories[number - 1])

root.bind("<Key>", key_pressed)


# --------------------------------------------------
# BAŞLAT
# --------------------------------------------------

show_image()

root.mainloop()