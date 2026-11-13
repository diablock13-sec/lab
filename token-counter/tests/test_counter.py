import pytest
import typer
from typer.testing import CliRunner

import counter

app = typer.Typer()
app.command()(counter.main)
runner = CliRunner()


def fake_count(text, encoding=counter.DEFAULT_ENCODING):
    return len(text.split())


@pytest.fixture(autouse=True)
def no_real_tokenizer(monkeypatch):
    """Test tidak boleh mengunduh data tokenizer: ganti dengan hitung kata."""
    monkeypatch.setattr(counter, "count_tokens", fake_count)


def test_read_text_file_normal(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("halo dunia")
    assert counter.read_text_file(f) == "halo dunia"


def test_read_text_file_binary_is_none(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"abc\0def")
    assert counter.read_text_file(f) is None


def test_read_text_file_too_big_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(counter, "MAX_BYTES", 10)
    f = tmp_path / "big.txt"
    f.write_text("x" * 100)
    assert counter.read_text_file(f) is None


def test_iter_files_prunes_ignored_and_symlinks(tmp_path):
    for rel in [
        "a.txt",
        "sub/b.txt",
        ".git/x",
        "node_modules/x.js",
        "__pycache__/y.pyc",
        ".venv/z.py",
        "uv.lock",
        ".env",
    ]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    (tmp_path / "link.txt").symlink_to(tmp_path / "a.txt")
    found = {p.relative_to(tmp_path).as_posix() for p in counter.iter_files(tmp_path)}
    assert found == {"a.txt", "sub/b.txt"}


def test_count_folder_counts_and_skips(tmp_path):
    (tmp_path / "a.txt").write_text("satu dua tiga")
    (tmp_path / "b.bin").write_bytes(b"\0\0\0")
    rows, skipped = counter.count_folder(tmp_path)
    assert skipped == 1
    assert [(p.name, tokens) for p, _, tokens in rows] == [("a.txt", 3)]


def test_real_count_tokens_allows_special_text(monkeypatch):
    seen = {}

    class FakeEncoder:
        def encode(self, text, **kwargs):
            seen.update(kwargs)
            return [1, 2, 3]

    monkeypatch.setattr(counter, "get_encoder", lambda name: FakeEncoder())
    monkeypatch.undo()  # kembalikan count_tokens asli, tapi get_encoder harus palsu
    monkeypatch.setattr(counter, "get_encoder", lambda name: FakeEncoder())
    assert counter.count_tokens("<|endoftext|>") == 3
    assert seen == {"disallowed_special": ()}


def test_cli_folder_sorted_largest_first(tmp_path):
    (tmp_path / "small.txt").write_text("a")
    (tmp_path / "big.txt").write_text("a b c d e")
    result = runner.invoke(app, [str(tmp_path)])
    assert result.exit_code == 0
    assert result.output.index("big.txt") < result.output.index("small.txt")
    assert "Total: 2 file, 6 token" in result.output


def test_cli_top_limits_rows(tmp_path):
    for name in ("a", "b", "c"):
        (tmp_path / f"{name}.txt").write_text("x y")
    result = runner.invoke(app, [str(tmp_path), "--top", "1"])
    assert result.exit_code == 0
    assert "hanya 1 file teratas ditampilkan" in result.output


def test_cli_single_file(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("satu dua")
    result = runner.invoke(app, [str(f)])
    assert result.exit_code == 0
    assert "a.txt: 8 karakter, sekitar 2 token" in result.output


def test_cli_binary_file_exits_1(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"\0\0")
    result = runner.invoke(app, [str(f)])
    assert result.exit_code == 1


def test_cli_unknown_encoding_fails(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    result = runner.invoke(app, [str(tmp_path), "--encoding", "bukan-tokenizer"])
    assert result.exit_code != 0
