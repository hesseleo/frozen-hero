"""Tests for label generation helpers."""

from datetime import datetime
from unittest.mock import patch

import pytest

from frozen_hero import config
from frozen_hero.label import _check_for_linebreak, _make_label_name, print_label


class TestMakeLabelName:
    _date = datetime(2025, 3, 15)

    def test_basic_ascii(self):
        assert _make_label_name("Soup", self._date) == "Soup_20250315"

    def test_lowercase_umlauts_stripped(self):
        name = _make_label_name("Möhren", self._date)
        assert "ö" not in name
        assert name.startswith("Mohren")

    def test_uppercase_umlauts_stripped(self):
        name = _make_label_name("Ölsardinen", self._date)
        assert "Ö" not in name
        assert name.startswith("Olsardinen")

    def test_spaces_removed(self):
        name = _make_label_name("Chicken Soup", self._date)
        assert " " not in name
        assert name == "ChickenSoup_20250315"

    def test_special_chars_removed(self):
        name = _make_label_name("Mama's (best)", self._date)
        assert "'" not in name
        assert "(" not in name
        assert ")" not in name

    def test_date_suffix_format(self):
        d = datetime(2024, 12, 31)
        assert _make_label_name("X", d).endswith("_20241231")


class TestCheckForLinebreak:
    def test_short_text_no_break(self):
        two_rows, text = _check_for_linebreak("short")
        assert two_rows is False
        assert text == "short"

    def test_long_multiword_flags_two_rows_but_unchanged(self):
        long_text = "w " * (config.MAX_SUBTITLE_LEN // 2 + 1)
        two_rows, text = _check_for_linebreak(long_text)
        assert two_rows is True
        assert text == long_text  # multi-word: not split, just flagged

    def test_long_single_word_is_split_with_space(self):
        long_word = "A" * (config.MAX_SUBTITLE_LEN + 5)
        two_rows, text = _check_for_linebreak(long_word)
        assert two_rows is True
        assert " " in text
        parts = text.split(" ")
        assert len(parts) == 2
        assert len(parts[0]) == config.MAX_SUBTITLE_LEN


class TestPrintLabel:
    def test_calls_convert_qrencode_and_brother_ql(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "TMP_DIR", tmp_path)

        with patch("frozen_hero.label.subprocess.run") as mock_run:
            print_label("Soup", "vegan", "2025-01-01", 42)

        commands = [c[0][0][0] for c in mock_run.call_args_list]
        assert commands.count("convert") == 3  # render text + compose + border
        assert commands.count("qrencode") == 1
        assert commands.count("brother_ql") == 1

    def test_entry_id_passed_to_qrencode(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "TMP_DIR", tmp_path)

        with patch("frozen_hero.label.subprocess.run") as mock_run:
            print_label("X", "", "2025-01-01", 99)

        qrencode_call = next(c for c in mock_run.call_args_list if c[0][0][0] == "qrencode")
        assert "99" in qrencode_call[0][0]

    def test_cleanup_runs_even_if_subprocess_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "TMP_DIR", tmp_path)

        # Create a dummy file so cleanup has something to delete
        dummy = tmp_path / "Soup_20250101_text.png"
        dummy.write_bytes(b"")

        with (
            patch("frozen_hero.label.subprocess.run", side_effect=OSError("fail")),
            pytest.raises(OSError),
        ):
            print_label("Soup", "", "2025-01-01", 1)

        # The finally block should have tried to unlink temp files
        assert not dummy.exists()
