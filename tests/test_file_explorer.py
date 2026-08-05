"""Tests for file explorer bookmarks."""

import tempfile
from pathlib import Path

from omnilauncher.services.file_explorer import (
    list_files,
    get_bookmarks,
    create_folder,
    delete_path,
    rename_path,
)


def test_get_bookmarks():
    with tempfile.TemporaryDirectory() as tmp:
        bms = get_bookmarks(tmp)
        assert len(bms) == 8  # 8 bookmarks defined
        names = [b["name"] for b in bms]
        assert "Saves" in names
        assert "Mods" in names
        assert "Screenshots" in names
        for bm in bms:
            assert "icon" in bm
            assert "path" in bm
            assert "exists" in bm


def test_list_files_empty():
    with tempfile.TemporaryDirectory() as tmp:
        files = list_files(tmp)
        assert isinstance(files, list)
        assert len(files) == 0


def test_list_files_with_content():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "test.txt").write_text("hello")
        (Path(tmp) / "subdir").mkdir()
        files = list_files(tmp)
        assert len(files) == 2
        # dirs first due to sorting (is_file False first)
        names = [f["name"] for f in files]
        assert "subdir" in names
        assert "test.txt" in names
        for f in files:
            assert "is_dir" in f
            assert "size" in f
            assert "path" in f


def test_create_and_delete_folder():
    with tempfile.TemporaryDirectory() as tmp:
        new_folder = create_folder(tmp, "my_new_folder")
        assert Path(new_folder).exists()
        assert Path(new_folder).is_dir()
        delete_path(new_folder)
        assert not Path(new_folder).exists()


def test_create_and_delete_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "file.txt"
        p.write_text("content")
        assert p.exists()
        delete_path(str(p))
        assert not p.exists()


def test_rename_path():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "old.txt"
        p.write_text("content")
        new_path = rename_path(str(p), "new.txt")
        assert Path(new_path).exists()
        assert not p.exists()
        assert Path(new_path).name == "new.txt"


def test_list_files_nonexistent():
    files = list_files("/nonexistent/path/that/does/not/exist")
    assert files == []
