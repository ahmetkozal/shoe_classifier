import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from PIL import Image, ImageTk
import shutil
import json


# --------------------------------------------------
# KATEGORİ VE STİLLER
# --------------------------------------------------

CATEGORY_STYLES = {
    "ayakkabi": ["klasik", "loafer", "casual", "comfort","topuklu"],
    "terlik": ["klasik", "topuklu", "casual", "comfort","platform"],
    "sandalet": ["klasik", "topuklu", "casual", "comfort","platform"],
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
    file
    for file in source_dir.iterdir()
    if file.is_file()
    and file.suffix.lower() in [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]
]

images.sort(key=lambda x: x.name.lower())

if not images:
    print("Fotoğraf bulunamadı.")
    root.destroy()
    exit()


# --------------------------------------------------
# PROGRESS DOSYASI
# --------------------------------------------------

progress_file = (
    source_dir / ".shoe_labeler_progress.json"
)


# --------------------------------------------------
# DURUM VERİSİ
#
# Her fotoğraf için:
#
# {
#     "action": "labeled",
#     "category": "sandalet",
#     "style": "topuklu",
#     "destination": "..."
# }
#
# veya:
#
# {
#     "action": "skipped"
# }
#
# --------------------------------------------------

image_states = {}

current_index = 0


# --------------------------------------------------
# ESKİ PROGRESS DOSYASINI YÜKLE
# --------------------------------------------------

if progress_file.exists():

    try:

        with open(
            progress_file,
            "r",
            encoding="utf-8"
        ) as f:

            progress = json.load(f)


        # Yeni format

        if "image_states" in progress:

            image_states = progress.get(
                "image_states",
                {}
            )

            current_index = progress.get(
                "current_index",
                0
            )


        # Eski format
        #
        # Eski sürümde sadece current_index vardı.
        # Eski progress'i tamamen kaybetmemek için
        # mevcut processed klasörlerinden etiketleri
        # bulmaya çalışıyoruz.

        else:

            current_index = progress.get(
                "current_index",
                0
            )


    except (
        json.JSONDecodeError,
        OSError
    ):

        image_states = {}
        current_index = 0


# --------------------------------------------------
# PROCESSED KLASÖRÜNDEN MEVCUT ETİKETLERİ BUL
# --------------------------------------------------
#
# Yeni progress dosyasında olmayan ama processed
# içinde bulunan fotoğrafları da tespit ediyoruz.
#
# Böylece program yeniden başlatıldığında daha önce
# etiketlenmiş fotoğraflar kaybolmuyor.
#
# --------------------------------------------------

for category, styles in CATEGORY_STYLES.items():

    for style in styles:

        folder = (
            processed_dir
            / category
            / style
        )

        if not folder.exists():
            continue

        for image_path in folder.iterdir():

            if not image_path.is_file():
                continue

            filename = image_path.name

            # Eğer zaten kayıtlı değilse ekle

            if filename not in image_states:

                image_states[filename] = {
                    "action": "labeled",
                    "category": category,
                    "style": style,
                    "destination": str(
                        image_path
                    )
                }


# --------------------------------------------------
# ESKİ PROGRESS İÇİN ATLANANLARI TAHMİN ET
# --------------------------------------------------
#
# Eski sistemde current_index'e kadar gelen fakat
# processed içinde bulunmayan fotoğraflar büyük
# ihtimalle skip edilmişti.
#
# --------------------------------------------------

for i in range(
    min(current_index, len(images))
):

    filename = images[i].name

    if filename not in image_states:

        image_states[filename] = {
            "action": "skipped"
        }


# --------------------------------------------------
# INDEX SINIRLARI
# --------------------------------------------------

if current_index < 0:
    current_index = 0

if current_index >= len(images):
    current_index = max(
        0,
        len(images) - 1
    )


# --------------------------------------------------
# SEÇİMLER
# --------------------------------------------------

selected_category = None


# --------------------------------------------------
# UNDO HISTORY
# --------------------------------------------------

history = []


# --------------------------------------------------
# PROGRESS KAYDET
# --------------------------------------------------

def save_progress():

    data = {
        "current_index": current_index,
        "image_states": image_states
    }

    with open(
        progress_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# --------------------------------------------------
# SAYILARI HESAPLA
# --------------------------------------------------

def get_counts():

    labeled = 0
    skipped = 0

    for state in image_states.values():

        if state.get("action") == "labeled":
            labeled += 1

        elif state.get("action") == "skipped":
            skipped += 1

    total = len(images)

    remaining = (
        total
        - labeled
        - skipped
    )

    return labeled, skipped, remaining, total


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

title_label.pack(
    pady=(10, 5)
)


# --------------------------------------------------
# İLERLEME
# --------------------------------------------------

progress_label = tk.Label(
    root,
    text="",
    font=("Arial", 13, "bold")
)

progress_label.pack(
    pady=5
)


# --------------------------------------------------
# FOTOĞRAF
# --------------------------------------------------

image_label = tk.Label(root)

image_label.pack(
    pady=10
)


# --------------------------------------------------
# KISAYOLLAR
# --------------------------------------------------

shortcut_label = tk.Label(
    root,
    text=(
        "1-7: Kategori  |  "
        "1-4: Stil  |  "
        "← →: Fotoğraf  |  "
        "U: Geri Al  |  "
        "S: Atla  |  "
        "N: Sonraki Atlanan  |  "
        "P: Önceki Atlanan  |  "
        "ESC: Çıkış"
    ),
    font=("Arial", 11, "bold")
)

shortcut_label.pack(
    pady=(0, 8)
)


# --------------------------------------------------
# DURUM
# --------------------------------------------------

status_label = tk.Label(
    root,
    text="",
    font=("Arial", 14, "bold")
)

status_label.pack(
    pady=5
)


# --------------------------------------------------
# KATEGORİ BUTONLARI
# --------------------------------------------------

category_frame = tk.Frame(root)

category_frame.pack(
    pady=5
)

category_buttons = {}

categories = list(
    CATEGORY_STYLES.keys()
)


for i, category in enumerate(
    categories,
    start=1
):

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

style_frame.pack(
    pady=5
)

style_buttons = []


# --------------------------------------------------
# İLERLEME GÜNCELLE
# --------------------------------------------------

def update_progress():

    labeled, skipped, remaining, total = (
        get_counts()
    )

    progress_label.config(
        text=(
            f"Etiketlenen: {labeled}    |    "
            f"Atlanan: {skipped}    |    "
            f"Kalan: {remaining}    |    "
            f"Toplam: {total}"
        )
    )


# --------------------------------------------------
# FOTOĞRAF DURUMUNU GÖSTER
# --------------------------------------------------

def update_status():

    if current_index >= len(images):
        return

    image_path = images[
        current_index
    ]

    filename = image_path.name

    state = image_states.get(
        filename
    )


    if state is None:

        status_label.config(
            text=(
                f"{filename}    |    "
                "Durum: ETİKETLENMEDİ"
            )
        )

        return


    action = state.get(
        "action"
    )


    if action == "labeled":

        category = state.get(
            "category",
            "?"
        )

        style = state.get(
            "style",
            "?"
        )

        status_label.config(
            text=(
                f"{filename}    |    "
                f"Etiket: {category} / {style}"
            )
        )


    elif action == "skipped":

        status_label.config(
            text=(
                f"{filename}    |    "
                "Durum: ATLANDI"
            )
        )


# --------------------------------------------------
# FOTOĞRAFI GÖSTER
# --------------------------------------------------

def show_image():

    global current_index

    update_progress()


    if not images:

        return


    if current_index < 0:
        current_index = 0


    if current_index >= len(images):

        current_index = len(images) - 1


    image_path = images[
        current_index
    ]


    try:

        image = Image.open(
            image_path
        )

        image.thumbnail(
            (800, 500)
        )

        photo = ImageTk.PhotoImage(
            image
        )

        image_label.config(
            image=photo
        )

        image_label.image = photo

    except Exception as e:

        image_label.config(
            image=""
        )

        image_label.image = None

        status_label.config(
            text=f"Fotoğraf açılamadı: {e}"
        )

        return


    update_status()


# --------------------------------------------------
# KATEGORİ SEÇ
# --------------------------------------------------

def select_category(category):

    global selected_category

    selected_category = category

    status_label.config(
        text=(
            f"{category} seçildi → "
            "stil seç"
        )
    )


    # Eski stil butonlarını temizle

    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    # Yeni stil butonları

    styles = CATEGORY_STYLES[
        category
    ]


    for i, style in enumerate(
        styles,
        start=1
    ):

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

        style_buttons.append(
            button
        )


# --------------------------------------------------
# FOTOĞRAFI ETİKETLE
# --------------------------------------------------

def save_image(style):

    global current_index
    global selected_category


    if selected_category is None:
        return


    if current_index >= len(images):
        return


    image_path = images[
        current_index
    ]

    filename = image_path.name


    # --------------------------------------------------
    # ESKİ DURUM
    # --------------------------------------------------

    old_state = image_states.get(
        filename
    )


    old_destination = None


    if old_state:

        if old_state.get(
            "action"
        ) == "labeled":

            old_destination = old_state.get(
                "destination"
            )


    # --------------------------------------------------
    # YENİ HEDEF
    # --------------------------------------------------

    destination_dir = (
        processed_dir
        / selected_category
        / style
    )


    destination_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    new_destination = (
        destination_dir
        / filename
    )


    # --------------------------------------------------
    # ESKİ KOPYAYI SİL
    # --------------------------------------------------

    if (
        old_destination
        and old_destination != str(
            new_destination
        )
    ):

        old_path = Path(
            old_destination
        )

        if old_path.exists():

            old_path.unlink()


    # --------------------------------------------------
    # FOTOĞRAFI KOPYALA
    # --------------------------------------------------

    shutil.copy2(
        image_path,
        new_destination
    )


    # --------------------------------------------------
    # UNDO İÇİN ESKİ DURUMU KAYDET
    # --------------------------------------------------

    history.append(
        {
            "filename": filename,
            "old_state": old_state
        }
    )


    # --------------------------------------------------
    # YENİ DURUMU KAYDET
    # --------------------------------------------------

    image_states[filename] = {
        "action": "labeled",
        "category": selected_category,
        "style": style,
        "destination": str(
            new_destination
        )
    }


    selected_category = None


    # --------------------------------------------------
    # STİL BUTONLARINI TEMİZLE
    # --------------------------------------------------

    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    # --------------------------------------------------
    # SONRAKİ FOTOĞRAFA GEÇ
    # --------------------------------------------------

    if current_index < len(images) - 1:

        current_index += 1


    # --------------------------------------------------
    # PROGRESS KAYDET
    # --------------------------------------------------

    save_progress()


    # --------------------------------------------------
    # YENİ FOTOĞRAFI GÖSTER
    # --------------------------------------------------

    show_image()


# --------------------------------------------------
# FOTOĞRAFI ATLA
# --------------------------------------------------

def skip_image():

    global current_index
    global selected_category


    if current_index >= len(images):
        return


    image_path = images[
        current_index
    ]

    filename = image_path.name


    old_state = image_states.get(
        filename
    )


    # Undo için eski durumu kaydet

    history.append(
        {
            "filename": filename,
            "old_state": old_state
        }
    )


    # Skip olarak işaretle

    image_states[filename] = {
        "action": "skipped"
    }


    selected_category = None


    save_progress()


    # Sonraki fotoğrafa geç

    if current_index < len(images) - 1:

        current_index += 1


    # Stil butonlarını temizle

    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    show_image()


# --------------------------------------------------
# ÖNCEKİ FOTOĞRAF
# --------------------------------------------------

def previous_image():

    global current_index
    global selected_category


    selected_category = None


    if current_index > 0:

        current_index -= 1


    # Stil butonlarını temizle

    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    show_image()


# --------------------------------------------------
# SONRAKİ FOTOĞRAF
# --------------------------------------------------

def next_image():

    global current_index
    global selected_category


    selected_category = None


    if current_index < len(images) - 1:

        current_index += 1


    # Stil butonlarını temizle

    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    show_image()

def find_skipped_index(start_index, direction):

    index = start_index

    while True:

        index += direction

        if index < 0 or index >= len(images):
            return None

        filename = images[index].name

        state = image_states.get(
            filename
        )

        if (
            state
            and state.get("action") == "skipped"
        ):
            return index

def next_skipped():

    global current_index
    global selected_category

    index = find_skipped_index(
        current_index,
        1
    )

    if index is None:

        status_label.config(
            text="Sonraki atlanmış fotoğraf bulunamadı."
        )

        return


    current_index = index

    selected_category = None


    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    show_image()

def previous_skipped():

    global current_index
    global selected_category

    index = find_skipped_index(
        current_index,
        -1
    )

    if index is None:

        status_label.config(
            text="Önceki atlanmış fotoğraf bulunamadı."
        )

        return


    current_index = index

    selected_category = None


    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    show_image()


# --------------------------------------------------
# GERİ AL
# --------------------------------------------------

def undo():

    global selected_category


    if not history:

        status_label.config(
            text="Geri alınacak işlem yok."
        )

        return


    last_action = history.pop()


    filename = last_action[
        "filename"
    ]

    old_state = last_action[
        "old_state"
    ]


    # Şu anki durumu al

    current_state = image_states.get(
        filename
    )


    # Eğer şu anki durum etiketliyse
    # oluşturulan dosyayı sil

    if current_state:

        if current_state.get(
            "action"
        ) == "labeled":

            destination = current_state.get(
                "destination"
            )

            if destination:

                destination_path = Path(
                    destination
                )

                if destination_path.exists():

                    destination_path.unlink()


    # Eski duruma geri dön

    if old_state is None:

        image_states.pop(
            filename,
            None
        )

    else:

        image_states[filename] = (
            old_state
        )


        # Eski etiketli dosya yoksa
        # yeniden oluştur

        if (
            old_state.get("action")
            == "labeled"
        ):

            category = old_state.get(
                "category"
            )

            style = old_state.get(
                "style"
            )

            if category and style:

                source_image = (
                    source_dir / filename
                )

                destination_dir = (
                    processed_dir
                    / category
                    / style
                )

                destination_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                destination = (
                    destination_dir
                    / filename
                )

                if source_image.exists():

                    shutil.copy2(
                        source_image,
                        destination
                    )

                    image_states[
                        filename
                    ]["destination"] = str(
                        destination
                    )


    selected_category = None


    save_progress()


    # Stil butonlarını temizle

    for button in style_buttons:

        button.destroy()

    style_buttons.clear()


    show_image()


# --------------------------------------------------
# KLAVYE
# --------------------------------------------------

def key_pressed(event):

    key = event.keysym.lower()


    # --------------------------------------------------
    # U = UNDO
    # --------------------------------------------------

    if key == "u":

        undo()


    # --------------------------------------------------
    # S = SKIP
    # --------------------------------------------------

    elif key == "s":

        skip_image()

    elif key == "n":
    
            next_skipped()

    elif key == "p":
    
            previous_skipped()


    # --------------------------------------------------
    # SOL OK = ÖNCEKİ
    # --------------------------------------------------

    elif key == "left":

        previous_image()


    # --------------------------------------------------
    # SAĞ OK = SONRAKİ
    # --------------------------------------------------

    elif key == "right":

        next_image()


    # --------------------------------------------------
    # ESC = ÇIKIŞ
    # --------------------------------------------------

    elif key == "escape":

        save_progress()

        root.destroy()


    # --------------------------------------------------
    # KATEGORİ SEÇİLMİŞSE
    # 1-4 = STİL
    # --------------------------------------------------

    elif (
        selected_category is not None
        and key in [
            "1",
            "2",
            "3",
            "4",
            "5"
        ]
    ):

        number = int(key)

        styles = CATEGORY_STYLES[
            selected_category
        ]


        if number <= len(styles):

            save_image(
                styles[number - 1]
            )


    # --------------------------------------------------
    # KATEGORİ SEÇİLMEMİŞSE
    # 1-7 = KATEGORİ
    # --------------------------------------------------

    elif (
        selected_category is None
        and key in [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7"
        ]
    ):

        number = int(key)


        if number <= len(categories):

            select_category(
                categories[number - 1]
            )


# --------------------------------------------------
# KLAVYEYİ BAĞLA
# --------------------------------------------------

root.bind(
    "<Key>",
    key_pressed
)


# --------------------------------------------------
# BAŞLAT
# --------------------------------------------------

show_image()

root.mainloop()