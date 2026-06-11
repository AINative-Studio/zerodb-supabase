"""
Client -- Supabase-compatible client backed by ZeroDB.

Drop-in replacement: same interface as supabase.Client.

    from zerodb_supabase import create_client

    client = create_client()
    data = client.table('users').select('*').execute()
"""

import requests

from zerodb_supabase.provision import resolve_credentials
from zerodb_supabase.query import QueryBuilder
from zerodb_supabase.storage import StorageClient
from zerodb_supabase.functions import FunctionsClient


def create_client(supabase_url=None, supabase_key=None, **kwargs):
    """Create a Supabase-compatible client backed by ZeroDB.

    Supabase-compatible signature. If no URL/key provided, auto-provisions
    a free ZeroDB project.

    Args:
        supabase_url: Ignored (kept for Supabase API compatibility).
            Use ZERODB_BASE_URL env var to override the ZeroDB endpoint.
        supabase_key: Used as ZeroDB API key if provided.
        **kwargs: Extra options (api_key, project_id, base_url).

    Returns:
        Client instance.
    """
    api_key = kwargs.get("api_key") or supabase_key
    project_id = kwargs.get("project_id")
    base_url = kwargs.get("base_url")
    return Client(api_key=api_key, project_id=project_id, base_url=base_url)


class Client:
    """Supabase-compatible client backed by ZeroDB.

    Provides:
      - table(name) -> QueryBuilder for CRUD operations
      - storage -> StorageClient for file operations
      - functions -> FunctionsClient for serverless functions
    """

    def __init__(self, api_key=None, project_id=None, base_url=None):
        self._api_key, self._project_id, self._base_url = resolve_credentials(
            api_key=api_key,
            project_id=project_id,
        )
        if base_url:
            self._base_url = base_url

        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "X-Project-ID": self._project_id,
        })

        self._tables_url = f"{self._base_url}/api/v1/public/tables"
        self._files_url = f"{self._base_url}/api/v1/public/files"
        self._hooks_url = f"{self._base_url}/api/v1/public/hooks"

        self._storage = None
        self._functions = None

    @property
    def storage(self):
        """Access storage operations (S3-compatible via ZeroDB files API)."""
        if self._storage is None:
            self._storage = StorageClient(self._session, self._files_url)
        return self._storage

    @property
    def functions(self):
        """Access serverless functions (ZeroDB hooks API)."""
        if self._functions is None:
            self._functions = FunctionsClient(self._session, self._hooks_url)
        return self._functions

    def table(self, table_name):
        """Start a query on a table. Returns a QueryBuilder.

        Args:
            table_name: Name of the table to query.

        Returns:
            QueryBuilder instance for chaining operations.
        """
        return QueryBuilder(self._session, self._tables_url, table_name)

    def from_(self, table_name):
        """Alias for table(). Matches supabase-py's from_() method."""
        return self.table(table_name)

    def rpc(self, function_name, params=None):
        """Call a stored procedure / RPC function.

        Maps to ZeroDB hooks API.

        Args:
            function_name: Name of the function.
            params: Dict of parameters to pass.

        Returns:
            APIResponse with the result.
        """
        return self.functions.invoke(function_name, params or {})
