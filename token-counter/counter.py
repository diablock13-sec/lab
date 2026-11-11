from pathlib import Path
from typing import Annotated

import tiktoken
import typer


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def main(
    file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="file teks yang akan dihitung token-nya",
        ),
    ],
) -> None:
    text = file.read_text(encoding="utf-8", errors="ignore")
    total = count_tokens(text)
    print(f"{file.name}: {len(text)} karakter, sekitar {total} token (estimasi)")


if __name__ == "__main__":
    typer.run(main)
