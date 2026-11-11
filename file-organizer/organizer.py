from pathlib import Path

CATEGORIES = {
    ".jpg": "Gambar",
    ".png": "Gambar",
    ".pdf": "Dokumen",
    ".txt": "Dokumen",
    ".mp3": "Audio",
}


def list_files(folder: Path) -> list[Path]:
    return [p for p in folder.iterdir() if p.is_file()]


def get_category(file: Path) -> str:
    return CATEGORIES.get(file.suffix.lower(), "Lainnya")


if __name__ == "__main__":
    for f in list_files(Path("test_folder")):
        print(f"{f.name} -> {get_category(f)}")
