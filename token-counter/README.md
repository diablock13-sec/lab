# token-counter

CLI kecil untuk memperkirakan jumlah token di sebuah file atau folder teks.
Berguna untuk tahu seberapa besar sebuah proyek sebelum dikirim ke model AI.

## Pasang

    git clone https://github.com/diablock13-sec/lab.git
    cd lab/token-counter
    uv sync

## Pakai

Satu file:

    uv run counter.py README.md

Satu folder, urut dari token terbanyak:

    uv run counter.py ~/proyek --top 10

## Yang diabaikan

- Folder: `.git`, `node_modules`, `__pycache__`, `.venv`
- File: `uv.lock`, `package-lock.json`, `.env`
- File biner dan file lebih besar dari 1 MB

## Keterbatasan

- **Angka ini estimasi.** Program memakai tokenizer `cl100k_base` milik OpenAI lewat
  `tiktoken`. Tiap model punya tokenizer sendiri, jadi hitungan sebenarnya untuk Claude,
  Gemini, atau model lain bisa berbeda.
- File yang bukan UTF-8 dibaca dengan karakter rusak diabaikan, sehingga hitungannya
  bisa sedikit meleset.
- Jangan dipakai untuk menghitung tagihan. Pakai untuk gambaran kasar saja.
