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

Memilih tokenizer:

    uv run counter.py ~/proyek --encoding o200k_base

## Yang diabaikan

- Folder: `.git`, `node_modules`, `__pycache__`, `.venv` (tidak ditelusuri sama sekali)
- File: `uv.lock`, `package-lock.json`, `.env`
- Symlink, file biner, dan file lebih besar dari 1 MB

## Keterbatasan

- **Angka ini estimasi.** Program memakai tokenizer OpenAI lewat `tiktoken`
  (`cl100k_base` secara bawaan). Tiap model punya tokenizer sendiri, jadi hitungan
  sebenarnya untuk Claude, Gemini, atau model lain bisa berbeda.
- Teks seperti `<|endoftext|>` dihitung sebagai teks biasa, bukan token khusus.
- Penggunaan pertama tiap tokenizer mengunduh datanya, jadi butuh internet sekali.
- File yang bukan UTF-8 dibaca dengan karakter rusak diabaikan, sehingga hitungannya
  bisa sedikit meleset.
- Jangan dipakai untuk menghitung tagihan. Pakai untuk gambaran kasar saja.

## Tes

    uv run pytest
    uv run ruff check .

Test memakai hitung kata sebagai pengganti tokenizer, jadi tidak butuh internet.
