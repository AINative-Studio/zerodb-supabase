"""
Tests for zerodb-supabase Client and create_client.

Uses mocked HTTP responses -- no real API calls.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

# Prevent auto-provisioning during tests
os.environ.setdefault("ZERODB_API_KEY", "test-key-000")
os.environ.setdefault("ZERODB_PROJECT_ID", "test-project-000")

from zerodb_supabase import create_client, Client
from zerodb_supabase.provision import resolve_credentials, ZERODB_API_BASE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    """Patch requests.Session so no HTTP calls are made."""
    with patch("zerodb_supabase.client.requests.Session") as MockSession:
        session = MagicMock()
        MockSession.return_value = session
        yield session


@pytest.fixture
def client(mock_session):
    """Return a Client instance with mocked HTTP."""
    return Client(api_key="test-key", project_id="test-project")


# ---------------------------------------------------------------------------
# create_client()
# ---------------------------------------------------------------------------

class TestCreateClient:
    def test_create_client_no_args(self, mock_session):
        c = create_client()
        assert isinstance(c, Client)

    def test_create_client_with_supabase_key(self, mock_session):
        c = create_client(supabase_url="https://ignored.supabase.co", supabase_key="sk", project_id="sp")
        assert c._api_key == "sk"
        assert c._project_id == "sp"

    def test_create_client_with_zerodb_args(self, mock_session):
        c = create_client(api_key="zk", project_id="zp")
        assert c._api_key == "zk"
        assert c._project_id == "zp"

    def test_create_client_with_custom_base_url(self, mock_session):
        c = create_client(api_key="k", project_id="p", base_url="http://localhost:9000")
        assert c._base_url == "http://localhost:9000"


# ---------------------------------------------------------------------------
# Client properties
# ---------------------------------------------------------------------------

class TestClientProperties:
    def test_default_headers(self, mock_session):
        c = Client(api_key="k", project_id="p")
        headers = mock_session.headers.update.call_args[0][0]
        assert headers["Authorization"] == "Bearer k"
        assert headers["X-Project-ID"] == "p"

    def test_table_returns_query_builder(self, client):
        from zerodb_supabase.query import QueryBuilder
        qb = client.table("users")
        assert isinstance(qb, QueryBuilder)

    def test_from_is_alias_for_table(self, client):
        from zerodb_supabase.query import QueryBuilder
        qb = client.from_("users")
        assert isinstance(qb, QueryBuilder)

    def test_storage_property(self, client):
        from zerodb_supabase.storage import StorageClient
        assert isinstance(client.storage, StorageClient)

    def test_storage_singleton(self, client):
        s1 = client.storage
        s2 = client.storage
        assert s1 is s2

    def test_functions_property(self, client):
        from zerodb_supabase.functions import FunctionsClient
        assert isinstance(client.functions, FunctionsClient)

    def test_functions_singleton(self, client):
        f1 = client.functions
        f2 = client.functions
        assert f1 is f2


# ---------------------------------------------------------------------------
# Provisioning
# ---------------------------------------------------------------------------

class TestProvisioning:
    def test_explicit_credentials(self):
        key, project, base = resolve_credentials(
            api_key="explicit-key",
            project_id="explicit-project",
        )
        assert key == "explicit-key"
        assert project == "explicit-project"
        assert base == ZERODB_API_BASE

    def test_env_credentials(self):
        with patch.dict(os.environ, {
            "ZERODB_API_KEY": "env-key",
            "ZERODB_PROJECT_ID": "env-project",
        }):
            key, project, base = resolve_credentials()
            assert key == "env-key"
            assert project == "env-project"

    def test_custom_base_url_env(self):
        with patch.dict(os.environ, {
            "ZERODB_API_KEY": "k",
            "ZERODB_PROJECT_ID": "p",
            "ZERODB_BASE_URL": "http://localhost:8000",
        }):
            _, _, base = resolve_credentials()
            assert base == "http://localhost:8000"

    @patch("zerodb_supabase.provision._load_config_file")
    def test_config_file_fallback(self, mock_load):
        mock_load.return_value = ("file-key", "file-project")
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ZERODB_API_KEY", None)
            os.environ.pop("ZERODB_PROJECT_ID", None)
            key, project, _ = resolve_credentials()
            assert key == "file-key"
            assert project == "file-project"

    @patch("zerodb_supabase.provision._load_config_file")
    @patch("zerodb_supabase.provision._auto_provision")
    def test_auto_provision_fallback(self, mock_provision, mock_load):
        mock_load.return_value = (None, None)
        mock_provision.return_value = ("auto-key", "auto-project")
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ZERODB_API_KEY", None)
            os.environ.pop("ZERODB_PROJECT_ID", None)
            key, project, _ = resolve_credentials()
            assert key == "auto-key"
            assert project == "auto-project"
            mock_provision.assert_called_once()
