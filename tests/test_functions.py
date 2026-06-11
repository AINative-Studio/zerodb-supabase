"""
Tests for zerodb-supabase FunctionsClient.

Uses mocked HTTP responses -- no real API calls.
"""

import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("ZERODB_API_KEY", "test-key-000")
os.environ.setdefault("ZERODB_PROJECT_ID", "test-project-000")

from zerodb_supabase.functions import FunctionsClient, FunctionResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def functions(mock_session):
    return FunctionsClient(mock_session, "https://api.test/hooks")


# ---------------------------------------------------------------------------
# FunctionResponse
# ---------------------------------------------------------------------------

class TestFunctionResponse:
    def test_response_fields(self):
        r = FunctionResponse(data={"result": "ok"}, status_code=200)
        assert r.data == {"result": "ok"}
        assert r.status_code == 200

    def test_response_repr(self):
        r = FunctionResponse(data={"x": 1})
        assert "FunctionResponse" in repr(r)


# ---------------------------------------------------------------------------
# invoke()
# ---------------------------------------------------------------------------

class TestInvoke:
    def test_invoke_basic(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "processed"}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.request.return_value = mock_resp

        result = functions.invoke("process-upload", {"file_id": "123"})
        assert result.data == {"result": "processed"}
        assert result.status_code == 200

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "invoke/process-upload" in call_args[0][1]

    def test_invoke_with_body_key(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.request.return_value = mock_resp

        functions.invoke("my-func", {"body": {"key": "value"}})
        call_args = mock_session.request.call_args
        # Should extract body from options
        assert call_args[1]["json"] == {"key": "value"}

    def test_invoke_with_custom_method(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.request.return_value = mock_resp

        functions.invoke("my-func", {"method": "GET"})
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"

    def test_invoke_no_options(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.request.return_value = mock_resp

        result = functions.invoke("my-func")
        assert result.status_code == 200

    def test_invoke_text_response(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("not json")
        mock_resp.text = "plain text result"
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.request.return_value = mock_resp

        result = functions.invoke("my-func")
        assert result.data == "plain text result"


# ---------------------------------------------------------------------------
# list / get / create / delete
# ---------------------------------------------------------------------------

class TestFunctionManagement:
    def test_list(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": "func1"}, {"name": "func2"}]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        result = functions.list()
        assert len(result) == 2

    def test_get(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "func1", "status": "active"}
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        result = functions.get("func1")
        assert result["name"] == "func1"

    def test_create(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "new-func", "created": True}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = functions.create("new-func", {"runtime": "python3.12"})
        body = mock_session.post.call_args[1]["json"]
        assert body["name"] == "new-func"
        assert body["runtime"] == "python3.12"

    def test_delete(self, functions, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"deleted": True}
        mock_resp.raise_for_status = MagicMock()
        mock_session.delete.return_value = mock_resp

        functions.delete("old-func")
        mock_session.delete.assert_called_once()
