"""
zerodb-supabase -- Drop-in Supabase Python client replacement backed by ZeroDB.

Change one import, keep the same API:

    # Before (supabase-py)
    from supabase import create_client

    # After (zerodb-supabase)
    from zerodb_supabase import create_client

Free cloud database. No Supabase account needed.
Auto-provisions on first use.
"""

from zerodb_supabase.client import Client, create_client  # noqa: F401
from zerodb_supabase.query import QueryBuilder  # noqa: F401
from zerodb_supabase.storage import StorageClient, StorageBucket  # noqa: F401
from zerodb_supabase.functions import FunctionsClient  # noqa: F401

__version__ = "0.1.0"
__all__ = [
    "Client",
    "create_client",
    "QueryBuilder",
    "StorageClient",
    "StorageBucket",
    "FunctionsClient",
]
