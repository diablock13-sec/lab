import argparse
import json
import os
import shutil
import sys
from pathlib import Path

CATEGORIES = {
    ".jpg": "Gambar",
    ".png": "Gambar",
    ".pdf": "Dokumen",
    ".txt": "Dokumen",
    ".mp3": "Audio",
}
LOG_NAME = ".organizer-log.json"

Move = tuple[Path, Path]


def get_category(file: Path) -> str:
    return CATEGORIES.get(file.suffix.lower(), "Lainnya")


def list_files(folder: Path) -> list[Path]:
    """File biasa saja: lewati file tersembunyi dan symlink."""
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and not p.is_symlink() and not p.name.startswith(".")
    )


def unique_target(target: Path) -> Path:
    """Kalau nama sudah dipakai, pakai a_1.jpg, a_2.jpg, dst. Tidak pernah menimpa."""
    if not target.exists() and not target.is_symlink():
        return target
    n = 1
    while True:
        candidate = target.with_name(f"{target.stem}_{n}{target.suffix}")
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        n += 1


def write_log(folder: Path, moves: list[Move]) -> None:
    data = [
        {"from": str(src.relative_to(folder)), "to": str(dst.relative_to(folder))}
        for src, dst in moves
    ]
    tmp = folder / (LOG_NAME + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, folder / LOG_NAME)


def read_log(path: Path) -> list[tuple[str, str]] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        pairs = []
        for item in data:
            src, dst = item["from"], item["to"]
            if not isinstance(src, str) or not isinstance(dst, str):
                raise TypeError("isi log tidak valid")
            pairs.append((src, dst))
        return pairs
    except (OSError, ValueError, KeyError, TypeError):
        return None


def organize(folder: Path, dry_run: bool = True) -> tuple[list[Move], int]:
    moves: list[Move] = []
    errors = 0
    for f in list_files(folder):
        target_dir = folder / get_category(f)
        target = unique_target(target_dir / f.name)
        shown = target.relative_to(folder)
        if dry_run:
            print(f"[DRY RUN] {f.name} -> {shown}")
            moves.append((f, target))
            continue
        try:
            target_dir.mkdir(exist_ok=True)
            shutil.move(str(f), str(target))
        except OSError as e:
            print(f"GAGAL {f.name}: {e}", file=sys.stderr)
            errors += 1
            continue
        print(f"{f.name} -> {shown}")
        moves.append((f, target))
    if moves and not dry_run:
        write_log(folder, moves)
    return moves, errors


def _inside(root: Path, path: Path) -> bool:
    return path.resolve().is_relative_to(root)


def undo(folder: Path, dry_run: bool = True) -> tuple[list[Move], int]:
    """Batalkan pemindahan terakhir berdasarkan log. Tidak pernah menimpa file."""
    log_path = folder / LOG_NAME
    if not log_path.is_file():
        print("tidak ada log untuk dibatalkan", file=sys.stderr)
        return [], 1
    pairs = read_log(log_path)
    if pairs is None:
        print("log rusak, tidak bisa dibatalkan", file=sys.stderr)
        return [], 1

    root = folder.resolve()
    restored: list[Move] = []
    errors = 0
    for rel_from, rel_to in reversed(pairs):
        original = folder / rel_from
        current = folder / rel_to
        if not (_inside(root, original) and _inside(root, current)):
            print(f"LEWATI (di luar folder): {rel_to}", file=sys.stderr)
            errors += 1
            continue
        if not current.is_file():
            print(f"LEWATI (file tidak ada): {rel_to}", file=sys.stderr)
            errors += 1
            continue
        if original.exists() or original.is_symlink():
            print(f"LEWATI (tempat asal sudah terisi): {rel_from}", file=sys.stderr)
            errors += 1
            continue
        if dry_run:
            print(f"[DRY RUN] {rel_to} -> {rel_from}")
        else:
            try:
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current), str(original))
            except OSError as e:
                print(f"GAGAL {rel_to}: {e}", file=sys.stderr)
                errors += 1
                continue
            print(f"{rel_to} -> {rel_from}")
        restored.append((current, original))

    if not dry_run:
        for current, _ in restored:
            if current.parent != folder:
                try:
                    current.parent.rmdir()  # hanya berhasil kalau kosong
                except OSError:
                    pass
        if errors == 0:
            log_path.unlink()
    return restored, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rapikan file di sebuah folder berdasarkan ekstensi."
    )
    parser.add_argument("folder", help="folder yang dirapikan")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="hanya cetak rencana, tanpa memindah file",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="batalkan pemindahan terakhir (dari log di dalam folder)",
    )
    args = parser.parse_args(argv)

    folder = Path(args.folder)
    if not folder.is_dir():
        parser.error(f"folder tidak ditemukan: {folder}")
    if folder.resolve() in {Path("/"), Path.home().resolve()}:
        parser.error("menolak merapikan folder root atau home")

    if args.undo:
        moves, errors = undo(folder, dry_run=args.dry_run)
        verb = "akan dikembalikan" if args.dry_run else "dikembalikan"
    else:
        moves, errors = organize(folder, dry_run=args.dry_run)
        verb = "akan dipindah" if args.dry_run else "dipindah"
    print(f"{len(moves)} file {verb}, {errors} masalah")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
