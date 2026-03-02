"""Tests for the SQLite data-access layer."""

from frozen_hero import db


class TestGetAllEntries:
    def test_empty_db_returns_empty_list(self, tmp_db):
        assert db.get_all_entries() == []

    def test_returns_inserted_entry(self, tmp_db):
        db.add_entry("Lasagne", "vegan", "selfstuff", "2025-01-15")
        entries = db.get_all_entries()
        assert len(entries) == 1
        assert entries[0]["row_one"] == "Lasagne"
        assert entries[0]["row_two"] == "vegan"
        assert entries[0]["category"] == "selfstuff"
        assert entries[0]["date"] == "2025-01-15"

    def test_entries_ordered_by_date(self, tmp_db):
        db.add_entry("Later", "", "", "2025-06-01")
        db.add_entry("Earlier", "", "", "2024-01-01")
        entries = db.get_all_entries()
        assert entries[0]["row_one"] == "Earlier"
        assert entries[1]["row_one"] == "Later"


class TestAddEntry:
    def test_returns_integer_id(self, tmp_db):
        entry_id = db.add_entry("Soup", "", "food", "2025-03-01")
        assert isinstance(entry_id, int)
        assert entry_id > 0

    def test_sequential_ids_are_unique(self, tmp_db):
        id1 = db.add_entry("A", "", "", "2025-01-01")
        id2 = db.add_entry("B", "", "", "2025-01-02")
        assert id1 != id2

    def test_id_matches_entry_in_list(self, tmp_db):
        entry_id = db.add_entry("Stew", "beef", "meat", "2025-04-01")
        entries = db.get_all_entries()
        assert entries[0]["id"] == entry_id


class TestDeleteEntry:
    def test_delete_existing_returns_true(self, tmp_db):
        entry_id = db.add_entry("X", "", "", "2025-01-01")
        assert db.delete_entry(entry_id) is True

    def test_deleted_entry_no_longer_returned(self, tmp_db):
        entry_id = db.add_entry("X", "", "", "2025-01-01")
        db.delete_entry(entry_id)
        assert db.get_all_entries() == []

    def test_delete_nonexistent_returns_false(self, tmp_db):
        assert db.delete_entry(99999) is False

    def test_delete_only_removes_target_entry(self, tmp_db):
        id1 = db.add_entry("Keep", "", "", "2025-01-01")
        id2 = db.add_entry("Remove", "", "", "2025-01-02")
        db.delete_entry(id2)
        entries = db.get_all_entries()
        assert len(entries) == 1
        assert entries[0]["id"] == id1
