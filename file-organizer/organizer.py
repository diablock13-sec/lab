from pathlib import Path


def list_files(folder: Path) -> list[Path]:
    return [p for p in folder.iterdir() if p.is_file()]


if __name__ == "__main__":
    for f in list_files(Path("test_folder")):
        print(f.name, f.suffix)
