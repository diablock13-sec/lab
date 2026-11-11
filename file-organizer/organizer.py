import shutil
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


def organize(folder: Path, dry_run: bool = True) -> None:
    for f in list_files(folder):
        target_dir = folder / get_category(f)
        if dry_run:
            print(f"[DRY RUN] {f.name} -> {target_dir.name}/")
        else:
            target_dir.mkdir(exist_ok=True)
            shutil.move(str(f), str(target_dir / f.name))
            print(f"{f.name} -> {target_dir.name}/")


if __name__ == "__main__":
    organize(Path("test_folder"), dry_run=True)
