import csv
import json
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


# ============================================================
# AYARLAR
# ============================================================

CATEGORIES = {
    "ayakkabi": ["klasik", "loafer", "casual", "comfort", "topuklu"],
    "terlik": ["klasik", "topuklu", "casual", "comfort", "platform"],
    "sandalet": ["klasik", "topuklu", "casual", "comfort", "platform"],
    "basanojki": ["klasik", "topuklu", "comfort"],
    "tufli": ["klasik", "comfort", "topuklu"],
    "babet": ["klasik", "comfort", "casual"],
    "bot": ["klasik", "topuklu", "casual"],
    "cizme": ["klasik", "topuklu", "yarim_cizme"],
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".JPG",
    ".JPEG",
    ".PNG",
}

CONFIDENCE_THRESHOLD = 0.70


# ============================================================
# GLOBAL DEĞİŞKENLER
# ============================================================

dataset_root = None
review_dir = None
processed_dir = None

review_csv = None
label_progress_file = None
review_progress_file = None

images = []
reviewed = {}

current_index = 0

selected_category = None

photo_image = None


# ============================================================
# DOSYA / KLASÖR YARDIMCILARI
# ============================================================

def find_dataset():
    """
    Kullanıcıdan dataset ana klasörünü seçmesini ister.
    """

    global dataset_root
    global review_dir
    global processed_dir
    global review_csv
    global label_progress_file
    global review_progress_file

    from tkinter import filedialog

    folder = filedialog.askdirectory(
        title="Dataset klasörünü seç"
    )

    if not folder:
        return False

    dataset_root = Path(folder)

    review_dir = dataset_root / "review"
    processed_dir = dataset_root / "processed"

    review_csv = review_dir / "review.csv"

    label_progress_file = (
        dataset_root / ".shoe_labeler_progress.json"
    )

    review_progress_file = (
        review_dir / ".review_progress.json"
    )

    if not review_csv.exists():
        messagebox.showerror(
            "Hata",
            f"review.csv bulunamadı:\n\n{review_csv}"
        )
        return False

    if not processed_dir.exists():
        processed_dir.mkdir(parents=True)

    return True


def load_review_csv():
    """
    review.csv dosyasını okur.
    """

    global images

    images = []

    with open(
        review_csv,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            filename = row["filename"]

            try:
                confidence = float(row["confidence"])
            except (ValueError, TypeError):
                confidence = 0.0

            images.append({
                "filename": filename,
                "prediction": row["prediction"],
                "confidence": confidence,
            })


def load_review_progress():
    """
    Review sırasında tamamlanan fotoğrafları yükler.
    """

    global reviewed
    global current_index

    if not review_progress_file.exists():
        reviewed = {}
        current_index = 0
        return

    try:
        with open(
            review_progress_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        reviewed = data.get("reviewed", {})
        current_index = data.get("current_index", 0)

    except (json.JSONDecodeError, OSError):
        reviewed = {}
        current_index = 0


def save_review_progress():
    """
    Review ilerlemesini kaydeder.
    """

    data = {
        "current_index": current_index,
        "reviewed": reviewed,
    }

    with open(
        review_progress_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


def load_original_labels():
    """
    İlk labeler'ın progress dosyasını okur.

    Böylece bir fotoğrafın daha önce manuel olarak
    hangi kategori/stile konduğunu biliyoruz.
    """

    if not label_progress_file.exists():
        return {}

    try:
        with open(
            label_progress_file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


# ============================================================
# ETİKET YARDIMCILARI
# ============================================================

def get_original_label(filename):
    """
    İlk labeler'daki mevcut etiketi bulur.

    Dönen değer:
        ("category", "style")
    veya
        None
    """

    progress = load_original_labels()

    entry = progress.get(filename)

    if not entry:
        return None

    category = entry.get("category")
    style = entry.get("style")

    if category and style:
        return category, style

    return None


def find_existing_processed_file(filename):
    """
    processed klasörünün altında bu dosyanın mevcut
    kopyasını bulur.

    Çünkü fotoğraf daha önce manuel olarak etiketlenmiş
    olabilir.
    """

    if not processed_dir.exists():
        return None

    for path in processed_dir.rglob("*"):

        if not path.is_file():
            continue

        if path.name == filename:
            return path

    return None


def remove_old_processed_copy(filename):
    """
    Fotoğrafın processed içindeki eski kopyasını siler.

    Raw ve review dosyasına DOKUNMAZ.
    """

    old_file = find_existing_processed_file(filename)

    if old_file is None:
        return

    try:
        old_file.unlink()

    except OSError as e:
        messagebox.showwarning(
            "Dosya silinemedi",
            f"Eski processed dosyası silinemedi:\n\n"
            f"{old_file}\n\n{e}"
        )
        return

    # Boş klasörleri temizle
    folder = old_file.parent

    while folder != processed_dir:

        try:
            folder.rmdir()
        except OSError:
            break

        folder = folder.parent


def save_processed_label(filename, category, style):
    """
    Fotoğrafı doğru category/style klasörüne kopyalar.
    """

    destination_dir = (
        processed_dir
        / category
        / style
    )

    destination_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    source = review_dir / filename
    destination = destination_dir / filename

    if not source.exists():
        messagebox.showerror(
            "Dosya bulunamadı",
            f"Review dosyası bulunamadı:\n\n{source}"
        )
        return False

    try:
        shutil.copy2(
            source,
            destination
        )

    except OSError as e:
        messagebox.showerror(
            "Kopyalama hatası",
            str(e)
        )
        return False

    return True


def update_original_progress(filename, category, style):
    """
    İlk labeler'ın progress dosyasını da günceller.

    Böylece iki labeler'ın kayıtları çelişmez.
    """

    progress = load_original_labels()

    if filename not in progress:
        progress[filename] = {}

    progress[filename]["category"] = category
    progress[filename]["style"] = style
    progress[filename]["action"] = "labeled"

    progress[filename]["destination"] = str(
        processed_dir / category / style / filename
    )

    with open(
        label_progress_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            progress,
            f,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# FOTOĞRAF NAVİGASYONU
# ============================================================

def get_next_unreviewed(start_index):
    """
    start_index'ten sonraki tamamlanmamış fotoğrafı bulur.
    """

    for i in range(
        start_index + 1,
        len(images)
    ):

        filename = images[i]["filename"]

        if filename not in reviewed:
            return i

    return None


def get_previous_unreviewed(start_index):
    """
    start_index'ten önceki tamamlanmamış fotoğrafı bulur.
    """

    for i in range(
        start_index - 1,
        -1,
        -1
    ):

        filename = images[i]["filename"]

        if filename not in reviewed:
            return i

    return None


def find_first_unreviewed():
    """
    İlk tamamlanmamış fotoğrafı bulur.
    """

    for i, image in enumerate(images):

        if image["filename"] not in reviewed:
            return i

    return None


def show_current_image():
    """
    Mevcut fotoğrafı GUI'de gösterir.
    """

    global photo_image
    global selected_category

    if current_index < 0:
        return

    if current_index >= len(images):
        return

    data = images[current_index]

    filename = data["filename"]

    image_path = review_dir / filename

    if not image_path.exists():

        messagebox.showerror(
            "Dosya bulunamadı",
            f"Fotoğraf bulunamadı:\n\n{image_path}"
        )

        return

    try:

        image = Image.open(image_path)

        image.thumbnail((900, 650))

        photo_image = ImageTk.PhotoImage(image)

        image_label.config(
            image=photo_image,
            text=""
        )

    except Exception as e:

        image_label.config(
            image="",
            text=f"Fotoğraf açılamadı:\n{e}"
        )

    # Bilgiler
    prediction = data["prediction"]
    confidence = data["confidence"]

    prediction_label.config(
        text=f"AI tahmini: {prediction}"
    )

    confidence_label.config(
        text=f"Güven: {confidence:.2%}"
    )

    filename_label.config(
        text=f"{current_index + 1} / {len(images)}\n{filename}"
    )

    original = get_original_label(filename)

    if original:

        category, style = original

        original_label.config(
            text=f"Mevcut etiket: {category} / {style}"
        )

    else:

        original_label.config(
            text="Mevcut etiket: bulunamadı"
        )

    selected_category = None

    clear_style_buttons()

    update_status()


def next_image():
    """
    N:
    Sonraki tamamlanmamış fotoğrafa geç.
    """

    global current_index

    index = get_next_unreviewed(current_index)

    if index is None:

        messagebox.showinfo(
            "Review tamamlandı",
            "Kontrol edilecek başka fotoğraf kalmadı."
        )

        return

    current_index = index

    save_review_progress()

    show_current_image()


def previous_image():
    """
    P:
    Önceki tamamlanmamış fotoğrafa geç.
    """

    global current_index

    index = get_previous_unreviewed(current_index)

    if index is None:

        messagebox.showinfo(
            "İlk fotoğraf",
            "Daha önce kontrol edilmemiş başka fotoğraf yok."
        )

        return

    current_index = index

    save_review_progress()

    show_current_image()


# ============================================================
# ETİKETLEME
# ============================================================

def select_category(category):
    """
    Kategori seçildikten sonra stil butonlarını gösterir.
    """

    global selected_category

    selected_category = category

    category_label.config(
        text=f"Kategori: {category}"
    )

    clear_style_buttons()

    styles = CATEGORIES[category]

    for i, style in enumerate(styles):

        button = tk.Button(
            style_frame,
            text=f"{i + 1} - {style}",
            width=15,
            command=lambda s=style: select_style(s)
        )

        button.pack(
            side=tk.LEFT,
            padx=3
        )


def clear_style_buttons():

    for widget in style_frame.winfo_children():
        widget.destroy()

    category_label.config(
        text="Kategori seçilmedi"
    )


def select_style(style):
    """
    Kategori + stil seçildiğinde etiketi kaydeder.
    """

    if selected_category is None:
        return

    filename = images[current_index]["filename"]

    category = selected_category

    # Eski processed kopyasını kaldır
    remove_old_processed_copy(filename)

    # Yeni doğru yere kopyala
    success = save_processed_label(
        filename,
        category,
        style
    )

    if not success:
        return

    # Eski labeler progress'ini güncelle
    update_original_progress(
        filename,
        category,
        style
    )

    # Review tamamlandı
    reviewed[filename] = {
        "category": category,
        "style": style,
        "prediction": images[current_index]["prediction"],
        "confidence": images[current_index]["confidence"],
    }

    save_review_progress()

    # Sonraki fotoğrafa geç
    go_to_next_after_label()


def accept_ai_prediction():
    """
    Enter:
    AI tahminini kabul eder.
    """

    if current_index >= len(images):
        return

    prediction = images[current_index]["prediction"]

    if "_" not in prediction:

        messagebox.showwarning(
            "Tahmin formatı",
            f"AI tahmini beklenen formatta değil:\n\n{prediction}"
        )

        return

    category, style = prediction.split(
        "_",
        1
    )

    if category not in CATEGORIES:

        messagebox.showwarning(
            "Geçersiz kategori",
            f"Kategori bulunamadı:\n\n{category}"
        )

        return

    if style not in CATEGORIES[category]:

        messagebox.showwarning(
            "Geçersiz stil",
            f"{category} altında '{style}' stili yok."
        )

        return

    select_style(style)


def go_to_next_after_label():
    """
    Etiketleme bittikten sonra otomatik olarak
    sonraki tamamlanmamış fotoğrafa geç.
    """

    global current_index

    index = get_next_unreviewed(current_index)

    if index is None:

        update_status()

        messagebox.showinfo(
            "Tamamlandı",
            "Tüm düşük güvenli fotoğraflar kontrol edildi."
        )

        return

    current_index = index

    show_current_image()


# ============================================================
# KLAVYE
# ============================================================

def key_pressed(event):

    key = event.keysym.lower()

    # Enter = AI tahminini kabul et
    if key == "return":

        accept_ai_prediction()
        return

    # N = sonraki
    if key == "n":

        next_image()
        return

    # P = önceki
    if key == "p":

        previous_image()
        return

    # Kategori 1-8
    if key in [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
    ]:

        index = int(key) - 1

        categories = list(
            CATEGORIES.keys()
        )

        if index < len(categories):

            select_category(
                categories[index]
            )

        return

    # Stil 1-5
    if key in [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]:

        # Bu bölüm kategori seçiminden sonra
        # teorik olarak çalışır.
        #
        # Ancak aynı rakam hem kategori hem stil
        # olduğu için burada stil işlemini ayrı
        # bir tuş sistemiyle yapıyoruz.
        #
        # Stil seçimi için şu an buton kullanılabilir.

        return


# ============================================================
# DURUM
# ============================================================

def update_status():

    total = len(images)

    done = len(reviewed)

    remaining = total - done

    if current_index < total:

        current = current_index + 1

    else:

        current = total

    status_label.config(
        text=(
            f"İlerleme: {done}/{total} "
            f"| Kalan: {remaining} "
            f"| Fotoğraf: {current}/{total}"
        )
    )


# ============================================================
# GUI
# ============================================================

root = tk.Tk()

root.title(
    "Shoe Classifier - Review"
)

root.geometry(
    "1200x900"
)

root.minsize(
    1000,
    750
)

# ------------------------------------------------------------
# Dataset seç
# ------------------------------------------------------------

if not find_dataset():

    root.destroy()
    raise SystemExit


load_review_csv()

load_review_progress()


# ------------------------------------------------------------
# GUI elemanları
# ------------------------------------------------------------

top_frame = tk.Frame(root)

top_frame.pack(
    fill=tk.X,
    padx=10,
    pady=10
)


filename_label = tk.Label(
    top_frame,
    text="",
    font=("Arial", 12, "bold")
)

filename_label.pack()


prediction_label = tk.Label(
    top_frame,
    text="AI tahmini:",
    font=("Arial", 14)
)

prediction_label.pack()


confidence_label = tk.Label(
    top_frame,
    text="Güven:",
    font=("Arial", 12)
)

confidence_label.pack()


original_label = tk.Label(
    top_frame,
    text="Mevcut etiket:",
    font=("Arial", 11)
)

original_label.pack()


# ------------------------------------------------------------
# Fotoğraf
# ------------------------------------------------------------

image_label = tk.Label(
    root,
    text="Fotoğraf",
    bg="gray90"
)

image_label.pack(
    expand=True,
    fill=tk.BOTH,
    padx=10,
    pady=10
)


# ------------------------------------------------------------
# Kategori
# ------------------------------------------------------------

category_title = tk.Label(
    root,
    text="Kategori seç:",
    font=("Arial", 12, "bold")
)

category_title.pack()


category_frame = tk.Frame(root)

category_frame.pack(
    pady=5
)


categories = list(
    CATEGORIES.keys()
)

for i, category in enumerate(categories):

    button = tk.Button(
        category_frame,
        text=f"{i + 1} - {category}",
        width=15,
        command=lambda c=category: select_category(c)
    )

    button.pack(
        side=tk.LEFT,
        padx=3
    )


category_label = tk.Label(
    root,
    text="Kategori seçilmedi"
)

category_label.pack(
    pady=3
)


# ------------------------------------------------------------
# Stil
# ------------------------------------------------------------

style_frame = tk.Frame(root)

style_frame.pack(
    pady=5
)


# ------------------------------------------------------------
# Kontroller
# ------------------------------------------------------------

control_frame = tk.Frame(root)

control_frame.pack(
    pady=10
)


previous_button = tk.Button(
    control_frame,
    text="← Önceki (P)",
    width=15,
    command=previous_image
)

previous_button.pack(
    side=tk.LEFT,
    padx=5
)


accept_button = tk.Button(
    control_frame,
    text="✓ AI Tahminini Kabul Et (Enter)",
    width=25,
    command=accept_ai_prediction
)

accept_button.pack(
    side=tk.LEFT,
    padx=5
)


next_button = tk.Button(
    control_frame,
    text="Sonraki (N) →",
    width=15,
    command=next_image
)

next_button.pack(
    side=tk.LEFT,
    padx=5
)


# ------------------------------------------------------------
# Status
# ------------------------------------------------------------

status_label = tk.Label(
    root,
    text="",
    font=("Arial", 10)
)

status_label.pack(
    pady=5
)


# ------------------------------------------------------------
# Klavye
# ------------------------------------------------------------

root.bind(
    "<Key>",
    key_pressed
)

root.focus_force()


# ------------------------------------------------------------
# İlk fotoğraf
# ------------------------------------------------------------

first = find_first_unreviewed()

if first is None:

    messagebox.showinfo(
        "Tamamlandı",
        "Bütün review fotoğrafları zaten kontrol edilmiş."
    )

else:

    current_index = first

    show_current_image()


# ------------------------------------------------------------
# Başlat
# ------------------------------------------------------------

root.mainloop()
