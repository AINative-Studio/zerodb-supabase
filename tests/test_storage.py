"""
Tests for zerodb-supabase StorageClient and StorageBucket.

Uses mocked HTTP responses -- no real API calls.
"""

import os
from unittest.mock import MagicMock, patch, call

import pytest

os.environ.setdefault("ZERODB_API_KEY", "test-key-000")
os.environ.setdefault("ZERODB_PROJECT_ID", "test-project-000")

from zerodb_supabase.storage import StorageClient, StorageBucket, StorageFileResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    session = MagicMock()
    session.headers = MagicMock()
    # Make dict() work on headers
    session.headers.__iter__ = MagicMock(return_value=iter([]))
    session.headers.items = MagicMock(return_value=[
        ("Content-Type", "application/json"),
        ("Authorization", "Bearer test-key"),
    ])
    return session


@pytest.fixture
def storage(mock_session):
    return StorageClient(mock_session, "https://api.test/files")


@pytest.fixture
def bucket(mock_session):
    return StorageBucket(mock_session, "https://api.test/files", "avatars")


# ---------------------------------------------------------------------------
# StorageFileResponse
# ---------------------------------------------------------------------------

class TestStorageFileResponse:
    def test_response_fields(self):
        r = StorageFileResponse(data={"key": "val"}, path="test/file.txt", status_code=200)
        assert r.data == {"key": "val"}
        assert r.path == "test/file.txt"
        assert r.status_code == 200

    def test_response_repr(self):
        r = StorageFileResponse(path="test.txt")
        assert "test.txt" in repr(r)


# ---------------------------------------------------------------------------
# StorageBucket
# ---------------------------------------------------------------------------

class TestStorageBucket:
    def test_file_path_prefixed(self, bucket):
        assert bucket._file_path("photo.png") == "avatars/photo.png"

    def test_upload(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"path": "avatars/photo.png", "size": 1024}
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = bucket.upload("photo.png", b"fake-image-data")
        assert result.path == "avatars/photo.png"
        assert result.status_code == 200

    def test_download(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.content = b"file-content"
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        data = bucket.download("photo.png")
        assert data == b"file-content"
        mock_session.get.assert_called_once()

    def test_get_public_url(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"url": "https://cdn.test/avatars/photo.png"}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        url = bucket.get_public_url("photo.png")
        assert url == "https://cdn.test/avatars/photo.png"

    def test_create_signed_url(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"url": "https://cdn.test/signed/avatars/photo.png"}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = bucket.create_signed_url("photo.png", expires_in=7200)
        assert "signedURL" in result
        body = mock_session.post.call_args[1]["json"]
        assert body["expires_in"] == 7200

    def test_remove(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"deleted": 2}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        bucket.remove(["photo1.png", "photo2.png"])
        body = mock_session.post.call_args[1]["json"]
        assert body["paths"] == ["avatars/photo1.png", "avatars/photo2.png"]

    def test_list(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"files": [{"name": "photo.png"}]}
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        files = bucket.list()
        assert len(files) == 1
        assert files[0]["name"] == "photo.png"

    def test_move(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"moved": True}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        bucket.move("old.png", "new.png")
        body = mock_session.post.call_args[1]["json"]
        assert body["from"] == "avatars/old.png"
        assert body["to"] == "avatars/new.png"

    def test_copy(self, bucket, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"copied": True}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        bucket.copy("original.png", "backup.png")
        body = mock_session.post.call_args[1]["json"]
        assert body["from"] == "avatars/original.png"
        assert body["to"] == "avatars/backup.png"


# ---------------------------------------------------------------------------
# StorageClient
# ---------------------------------------------------------------------------

class TestStorageClient:
    def test_from_returns_bucket(self, storage):
        bucket = storage.from_("uploads")
        assert isinstance(bucket, StorageBucket)

    def test_list_buckets(self, storage, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": "avatars"}, {"name": "uploads"}]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        buckets = storage.list_buckets()
        assert len(buckets) == 2

    def test_create_bucket(self, storage, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"name": "new-bucket"}
        mock_resp.raise_for_status = MagicMock()
        mock_session.post.return_value = mock_resp

        result = storage.create_bucket("new-bucket")
        body = mock_session.post.call_args[1]["json"]
        assert body["name"] == "new-bucket"

    def test_delete_bucket(self, storage, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"deleted": True}
        mock_resp.raise_for_status = MagicMock()
        mock_session.delete.return_value = mock_resp

        storage.delete_bucket("old-bucket")
        mock_session.delete.assert_called_once()
