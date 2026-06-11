"""
Tests for zerodb-supabase QueryBuilder.

Uses mocked HTTP responses -- no real API calls.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("ZERODB_API_KEY", "test-key-000")
os.environ.setdefault("ZERODB_PROJECT_ID", "test-project-000")

from zerodb_supabase.query import QueryBuilder, APIResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    session = MagicMock()
    return session


@pytest.fixture
def qb(mock_session):
    return QueryBuilder(mock_session, "https://api.test/tables", "users")


# ---------------------------------------------------------------------------
# APIResponse
# ---------------------------------------------------------------------------

class TestAPIResponse:
    def test_response_data(self):
        r = APIResponse(data=[{"id": 1}], count=1, status_code=200)
        assert r.data == [{"id": 1}]
        assert r.count == 1
        assert r.status_code == 200

    def test_response_repr(self):
        r = APIResponse(data=[], count=0)
        assert "APIResponse" in repr(r)


# ---------------------------------------------------------------------------
# SELECT
# ---------------------------------------------------------------------------

class TestSelect:
    def test_select_all(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [{"id": 1, "name": "Alice"}]}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = qb.select("*").execute()
        assert result.data == [{"id": 1, "name": "Alice"}]

        body = mock_session.post.call_args[1]["json"]
        assert body["table"] == "users"
        assert body["operation"] == "query"

    def test_select_specific_columns(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": []}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        qb.select("id, name, email").execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["columns"] == ["id", "name", "email"]

    def test_select_with_eq_filter(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [{"id": 1}]}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        qb.select("*").eq("active", True).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["filters"] == [{"column": "active", "op": "eq", "value": True}]

    def test_select_with_multiple_filters(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": []}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        qb.select("*").eq("active", True).gt("age", 18).execute()
        body = mock_session.post.call_args[1]["json"]
        assert len(body["filters"]) == 2
        assert body["filters"][0]["op"] == "eq"
        assert body["filters"][1]["op"] == "gt"

    def test_select_with_order(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": []}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        qb.select("*").order("created_at", desc=True).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["order_by"]["column"] == "created_at"
        assert body["order_by"]["ascending"] is False

    def test_select_with_limit(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": []}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        qb.select("*").limit(10).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["limit"] == 10

    def test_select_with_offset(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": []}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        qb.select("*").offset(20).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["offset"] == 20

    def test_select_single(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [{"id": 1, "name": "Alice"}]}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = qb.select("*").eq("id", 1).single().execute()
        assert result.data == {"id": 1, "name": "Alice"}

    def test_select_single_empty(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": []}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = qb.select("*").eq("id", 999).single().execute()
        assert result.data is None

    def test_select_range(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": []}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        qb.select("*").range(10, 19).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["offset"] == 10
        assert body["limit"] == 10


# ---------------------------------------------------------------------------
# INSERT
# ---------------------------------------------------------------------------

class TestInsert:
    def test_insert_single_row(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [{"id": 1, "name": "Alice"}]}
        mock_resp.status_code = 201
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = qb.insert({"name": "Alice", "email": "alice@example.com"}).execute()
        assert result.data == [{"id": 1, "name": "Alice"}]

        body = mock_session.post.call_args[1]["json"]
        assert body["table"] == "users"
        assert body["operation"] == "insert"
        assert len(body["rows"]) == 1

    def test_insert_multiple_rows(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [{"id": 1}, {"id": 2}]}
        mock_resp.status_code = 201
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        rows = [{"name": "Alice"}, {"name": "Bob"}]
        result = qb.insert(rows).execute()
        body = mock_session.post.call_args[1]["json"]
        assert len(body["rows"]) == 2


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_update_with_filter(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [{"id": 1, "name": "Alice Updated"}]}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = qb.update({"name": "Alice Updated"}).eq("id", 1).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["operation"] == "update"
        assert body["data"] == {"name": "Alice Updated"}
        assert body["filters"][0]["column"] == "id"


# ---------------------------------------------------------------------------
# UPSERT
# ---------------------------------------------------------------------------

class TestUpsert:
    def test_upsert(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [{"id": 1}]}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = qb.upsert({"id": 1, "name": "Alice"}).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["operation"] == "upsert"
        assert len(body["rows"]) == 1


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_with_filter(self, qb, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"rows": [], "count": 1}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = qb.delete().eq("id", 1).execute()
        body = mock_session.post.call_args[1]["json"]
        assert body["operation"] == "delete"
        assert body["filters"][0]["column"] == "id"


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

class TestFilters:
    def test_neq(self, qb):
        qb.neq("status", "deleted")
        assert qb._filters[-1] == {"column": "status", "op": "neq", "value": "deleted"}

    def test_gt(self, qb):
        qb.gt("age", 18)
        assert qb._filters[-1] == {"column": "age", "op": "gt", "value": 18}

    def test_gte(self, qb):
        qb.gte("score", 90)
        assert qb._filters[-1] == {"column": "score", "op": "gte", "value": 90}

    def test_lt(self, qb):
        qb.lt("price", 100)
        assert qb._filters[-1] == {"column": "price", "op": "lt", "value": 100}

    def test_lte(self, qb):
        qb.lte("count", 5)
        assert qb._filters[-1] == {"column": "count", "op": "lte", "value": 5}

    def test_like(self, qb):
        qb.like("name", "%alice%")
        assert qb._filters[-1] == {"column": "name", "op": "like", "value": "%alice%"}

    def test_ilike(self, qb):
        qb.ilike("name", "%ALICE%")
        assert qb._filters[-1] == {"column": "name", "op": "ilike", "value": "%ALICE%"}

    def test_is_(self, qb):
        qb.is_("deleted_at", None)
        assert qb._filters[-1] == {"column": "deleted_at", "op": "is", "value": None}

    def test_in_(self, qb):
        qb.in_("status", ["active", "pending"])
        assert qb._filters[-1] == {"column": "status", "op": "in", "value": ["active", "pending"]}

    def test_contains(self, qb):
        qb.contains("tags", ["python"])
        assert qb._filters[-1] == {"column": "tags", "op": "cs", "value": ["python"]}

    def test_not_(self, qb):
        qb.not_("status", "eq", "deleted")
        assert qb._filters[-1] == {"column": "status", "op": "not.eq", "value": "deleted"}

    def test_generic_filter(self, qb):
        qb.filter("col", "custom_op", "val")
        assert qb._filters[-1] == {"column": "col", "op": "custom_op", "value": "val"}


# ---------------------------------------------------------------------------
# No operation error
# ---------------------------------------------------------------------------

class TestNoOperation:
    def test_execute_without_operation_raises(self, qb):
        with pytest.raises(ValueError, match="No operation specified"):
            qb.execute()
