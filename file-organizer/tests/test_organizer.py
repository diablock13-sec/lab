import json
from pathlib import Path

import pytest

import organizer


def make(folder: Path, *names: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_text(name)


def test_category_is_case_insensitive():
    assert organizer.get_category(Path("e.JPG")) == "Gambar"
    assert organizer.get_category(Path("f.xyz")) == "Lainnya"


def test_moves_files_into_categories(tmp_path):
    make(tmp_path, "a.jpg", "b.pdf", "e.JPG", "f.xyz")
    moves, errors = organizer.organize(tmp_path, dry_run=False)
    assert errors == 0
    assert len(moves) == 4
    assert (tmp_path / "Gambar" / "a.jpg").read_text() == "a.jpg"
    assert (tmp_path / "Gambar" / "e.JPG").exists()
    assert (tmp_path / "Dokumen" / "b.pdf").exists()
    assert (tmp_path / "Lainnya" / "f.xyz").exists()
    assert not (tmp_path / "a.jpg").exists()


def test_collision_never_overwrites(tmp_path):
    (tmp_path / "Gambar").mkdir()
    (tmp_path / "Gambar" / "a.jpg").write_text("lama")
    (tmp_path / "a.jpg").write_text("baru")
    organizer.organize(tmp_path, dry_run=False)
    assert (tmp_path / "Gambar" / "a.jpg").read_text() == "lama"
    assert (tmp_path / "Gambar" / "a_1.jpg").read_text() == "baru"


def test_collision_numbers_increase(tmp_path):
    (tmp_path / "Gambar").mkdir()
    (tmp_path / "Gambar" / "a.jpg").write_text("1")
    (tmp_path / "Gambar" / "a_1.jpg").write_text("2")
    (tmp_path / "a.jpg").write_text("3")
    organizer.organize(tmp_path, dry_run=False)
    assert (tmp_path / "Gambar" / "a_2.jpg").read_text() == "3"


def test_dry_run_changes_nothing(tmp_path, capsys):
    make(tmp_path, "a.jpg", "b.pdf")
    moves, _ = organizer.organize(tmp_path, dry_run=True)
    assert len(moves) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.jpg", "b.pdf"]
    assert "[DRY RUN]" in capsys.readouterr().out


def test_skips_hidden_files_and_symlinks(tmp_path):
    folder = tmp_path / "isi"
    outside = tmp_path / "luar"
    make(folder, ".rahasia.jpg", "a.jpg")
    make(outside, "x.jpg")
    (folder / "link.jpg").symlink_to(outside / "x.jpg")
    organizer.organize(folder, dry_run=False)
    assert (folder / ".rahasia.jpg").exists()
    assert (folder / "link.jpg").is_symlink()
    assert (outside / "x.jpg").exists()
    assert (folder / "Gambar" / "a.jpg").exists()


def test_undo_restores_everything(tmp_path):
    make(tmp_path, "a.jpg", "b.pdf")
    organizer.organize(tmp_path, dry_run=False)
    moves, errors = organizer.undo(tmp_path, dry_run=False)
    assert errors == 0
    assert len(moves) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.jpg", "b.pdf"]


def test_undo_never_overwrites_new_file(tmp_path):
    make(tmp_path, "a.jpg")
    organizer.organize(tmp_path, dry_run=False)
    (tmp_path / "a.jpg").write_text("baru")
    moves, errors = organizer.undo(tmp_path, dry_run=False)
    assert errors == 1
    assert moves == []
    assert (tmp_path / "a.jpg").read_text() == "baru"
    assert (tmp_path / "Gambar" / "a.jpg").read_text() == "a.jpg"
    assert (tmp_path / organizer.LOG_NAME).exists()


def test_undo_without_log(tmp_path, capsys):
    moves, errors = organizer.undo(tmp_path, dry_run=False)
    assert moves == []
    assert errors == 1
    assert "tidak ada log" in capsys.readouterr().err


def test_undo_rejects_paths_outside_folder(tmp_path):
    folder = tmp_path / "isi"
    folder.mkdir()
    (tmp_path / "luar.txt").write_text("rahasia")
    log = [{"from": "../baru.txt", "to": "../luar.txt"}]
    (folder / organizer.LOG_NAME).write_text(json.dumps(log))
    moves, errors = organizer.undo(folder, dry_run=False)
    assert moves == []
    assert errors == 1
    assert (tmp_path / "luar.txt").exists()
    assert not (tmp_path / "baru.txt").exists()


def test_undo_corrupt_log(tmp_path):
    (tmp_path / organizer.LOG_NAME).write_text("bukan json")
    moves, errors = organizer.undo(tmp_path, dry_run=False)
    assert moves == []
    assert errors == 1


def test_undo_wrong_shape_log(tmp_path):
    (tmp_path / organizer.LOG_NAME).write_text('{"a": 1}')
    moves, errors = organizer.undo(tmp_path, dry_run=False)
    assert moves == []
    assert errors == 1


def test_main_dry_run_exit_zero(tmp_path):
    make(tmp_path, "a.jpg")
    assert organizer.main([str(tmp_path), "--dry-run"]) == 0
    assert (tmp_path / "a.jpg").exists()


def test_main_missing_folder_exits(tmp_path):
    with pytest.raises(SystemExit):
        organizer.main([str(tmp_path / "tidak-ada")])


def test_main_refuses_home_and_root():
    # --dry-run sengaja dipasang: kalau penjagaan gagal, tidak ada yang berubah
    for target in (str(Path.home()), "/"):
        with pytest.raises(SystemExit):
            organizer.main([target, "--dry-run"])


def test_main_undo_roundtrip(tmp_path):
    make(tmp_path, "a.jpg")
    assert organizer.main([str(tmp_path)]) == 0
    assert (tmp_path / "Gambar" / "a.jpg").exists()
    assert organizer.main([str(tmp_path), "--undo"]) == 0
    assert (tmp_path / "a.jpg").exists()
