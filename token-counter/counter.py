from functools import cache
from pathlib import Path
from typing import Annotated

import tiktoken
import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
MAX_BYTES = 1_000_000  # file lebih besar dari ini dilewati
IGNORE_FILES = {"uv.lock", "package-lock.json", ".env"}

console = Console()


@cache
def get_encoder():
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(get_encoder().encode(text))


def read_text_file(path: Path) -> str | None:
    """Kembalikan isi file, atau None kalau file biner/terlalu besar/tak terbaca."""
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:1024]:  # tanda file biner
        return None
    return data.decode("utf-8", errors="ignore")


def iter_files(folder: Path):
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        if p.is_file() and p.name not in IGNORE_FILES:
            yield p


def count_folder(folder: Path) -> tuple[list[tuple[Path, int, int]], int]:
    rows = []
    skipped = 0
    for p in iter_files(folder):
        text = read_text_file(p)
        if text is None:
            skipped += 1
            continue
        rows.append((p, len(text), count_tokens(text)))
    return rows, skipped


def main(
    path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            help="file atau folder yang akan dihitung token-nya",
        ),
    ],
    top: Annotated[int, typer.Option(help="tampilkan N file terbesar")] = 20,
) -> None:
    if path.is_file():
        text = read_text_file(path)
        if text is None:
            console.print("File biner atau terlalu besar, dilewati.")
            raise typer.Exit(code=1)
        print(f"{path.name}: {len(text)} karakter, sekitar {count_tokens(text)} token (estimasi)")
        return

    rows, skipped = count_folder(path)
    rows.sort(key=lambda r: r[2], reverse=True)
    total = sum(r[2] for r in rows)

    table = Table(title=f"Token per file di {escape(str(path))}")
    table.add_column("No", justify="right")
    table.add_column("File")
    table.add_column("Karakter", justify="right")
    table.add_column("Token", justify="right")
    for i, (p, chars, tokens) in enumerate(rows[:top], start=1):
        table.add_row(str(i), escape(str(p.relative_to(path))), f"{chars:,}", f"{tokens:,}")
    console.print(table)

    console.print(
        f"Total: {len(rows)} file, {total:,} token (estimasi). Dilewati: {skipped}."
    )
    if len(rows) > top:
        console.print(f"(hanya {top} file teratas ditampilkan)")


if __name__ == "__main__":
    typer.run(main)
