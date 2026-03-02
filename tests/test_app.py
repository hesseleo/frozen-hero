"""Tests for the Flask API routes."""

import frozen_hero.label as label_mod


class TestIndex:
    def test_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"frozen-hero" in resp.data


class TestGetData:
    def test_empty_db_returns_empty_list(self, client):
        resp = client.get("/getData")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_entries_after_insert(self, client):
        client.post(
            "/add2freezer",
            json={"row1": "Soup", "row2": "", "category": "selfstuff", "date": "2025-01-01"},
        )
        resp = client.get("/getData")
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["row_one"] == "Soup"


class TestAdd2Freezer:
    def test_success_returns_201_with_entry(self, client):
        resp = client.post(
            "/add2freezer",
            json={
                "row1": "Lasagne",
                "row2": "vegan",
                "category": "selfstuff",
                "date": "2025-03-01",
            },
        )
        assert resp.status_code == 201
        result = resp.get_json()["result"]
        assert result["dec1"] == "Lasagne"
        assert result["dec2"] == "vegan"
        assert isinstance(result["id"], int)

    def test_missing_row1_returns_400(self, client):
        resp = client.post(
            "/add2freezer",
            json={"row1": "", "row2": "x", "category": "", "date": "2025-01-01"},
        )
        assert resp.status_code == 400

    def test_missing_date_returns_400(self, client):
        resp = client.post(
            "/add2freezer",
            json={"row1": "Soup", "row2": "", "category": "", "date": ""},
        )
        assert resp.status_code == 400

    def test_invalid_date_format_returns_400(self, client):
        resp = client.post(
            "/add2freezer",
            json={"row1": "Soup", "row2": "", "category": "", "date": "15.01.2025"},
        )
        assert resp.status_code == 400

    def test_no_json_body_returns_4xx(self, client):
        # Flask 3 returns 415 Unsupported Media Type for non-JSON content;
        # either way the request is correctly rejected.
        resp = client.post("/add2freezer", data="plain text", content_type="text/plain")
        assert resp.status_code in (400, 415)

    def test_label_print_failure_is_nonfatal(self, client):
        label_mod.print_label.side_effect = RuntimeError("printer offline")
        try:
            resp = client.post(
                "/add2freezer",
                json={"row1": "Soup", "row2": "", "category": "", "date": "2025-01-01"},
            )
            assert resp.status_code == 201
        finally:
            label_mod.print_label.side_effect = None

    def test_print_label_called_with_correct_args(self, client):
        label_mod.print_label.reset_mock()
        client.post(
            "/add2freezer",
            json={"row1": "Stew", "row2": "beef", "category": "meat", "date": "2025-06-01"},
        )
        label_mod.print_label.assert_called_once()
        args = label_mod.print_label.call_args[0]
        assert args[0] == "Stew"
        assert args[1] == "beef"
        assert args[2] == "2025-06-01"


class TestDelEntry:
    def _add(self, client):
        resp = client.post(
            "/add2freezer",
            json={"row1": "X", "row2": "", "category": "", "date": "2025-01-01"},
        )
        return resp.get_json()["result"]["id"]

    def test_success_returns_200(self, client):
        entry_id = self._add(client)
        resp = client.post("/delEntry", json={"id": entry_id})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_entry_gone_after_delete(self, client):
        entry_id = self._add(client)
        client.post("/delEntry", json={"id": entry_id})
        assert client.get("/getData").get_json() == []

    def test_nonexistent_id_returns_404(self, client):
        resp = client.post("/delEntry", json={"id": 99999})
        assert resp.status_code == 404

    def test_invalid_id_type_returns_400(self, client):
        resp = client.post("/delEntry", json={"id": "not-an-int"})
        assert resp.status_code == 400

    def test_no_json_body_returns_4xx(self, client):
        resp = client.post("/delEntry", data="x", content_type="text/plain")
        assert resp.status_code in (400, 415)
