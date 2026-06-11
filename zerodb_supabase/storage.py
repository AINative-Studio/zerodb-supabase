"""
StorageClient -- Supabase Storage-compatible interface backed by ZeroDB files API.

    client.storage.from_('avatars').upload('avatar.png', file_data)
    url = client.storage.from_('avatars').get_public_url('avatar.png')
    client.storage.from_('avatars').download('avatar.png')
"""


class StorageFileResponse:
    """Response wrapper for storage operations."""

    def __init__(self, data=None, path=None, status_code=200):
        self.data = data
        self.path = path
        self.status_code = status_code

    def __repr__(self):
        return f"StorageFileResponse(path={self.path!r})"


class StorageBucket:
    """Supabase StorageBucket-compatible interface for a single bucket.

    Maps to ZeroDB files API with bucket prefix as directory.
    """

    def __init__(self, session, files_url, bucket_name):
        self._session = session
        self._files_url = files_url
        self._bucket = bucket_name

    def _file_path(self, path):
        """Build full file path with bucket prefix."""
        return f"{self._bucket}/{path}"

    def upload(self, path, file_data, file_options=None):
        """Upload a file to the bucket.

        Args:
            path: File path within the bucket.
            file_data: File content (bytes or file-like object).
            file_options: Optional dict with content_type, cache_control, etc.

        Returns:
            StorageFileResponse with upload result.
        """
        full_path = self._file_path(path)
        content_type = "application/octet-stream"
        if file_options and "content_type" in file_options:
            content_type = file_options["content_type"]
        elif file_options and "contentType" in file_options:
            content_type = file_options["contentType"]

        # Use multipart upload for ZeroDB files API
        files = {"file": (path, file_data, content_type)}
        data = {"path": full_path}

        # Temporarily remove JSON content-type for multipart
        headers = dict(self._session.headers)
        headers.pop("Content-Type", None)

        resp = self._session.post(
            f"{self._files_url}/upload",
            files=files,
            data=data,
            headers=headers,
        )
        resp.raise_for_status()
        result = resp.json()

        return StorageFileResponse(
            data=result,
            path=full_path,
            status_code=resp.status_code,
        )

    def download(self, path):
        """Download a file from the bucket.

        Args:
            path: File path within the bucket.

        Returns:
            bytes -- file content.
        """
        full_path = self._file_path(path)
        resp = self._session.get(
            f"{self._files_url}/download",
            params={"path": full_path},
        )
        resp.raise_for_status()
        return resp.content

    def get_public_url(self, path):
        """Get a public URL for a file.

        Args:
            path: File path within the bucket.

        Returns:
            str -- public URL.
        """
        full_path = self._file_path(path)
        resp = self._session.post(
            f"{self._files_url}/url",
            json={"path": full_path},
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("url", result.get("public_url", ""))

    def create_signed_url(self, path, expires_in=3600):
        """Create a signed URL for temporary access.

        Args:
            path: File path within the bucket.
            expires_in: Seconds until expiration (default 1 hour).

        Returns:
            dict with signedURL.
        """
        full_path = self._file_path(path)
        resp = self._session.post(
            f"{self._files_url}/url",
            json={"path": full_path, "expires_in": expires_in},
        )
        resp.raise_for_status()
        result = resp.json()
        return {"signedURL": result.get("url", result.get("signed_url", ""))}

    def remove(self, paths):
        """Remove file(s) from the bucket.

        Args:
            paths: List of file paths to remove.

        Returns:
            list of removed file info.
        """
        full_paths = [self._file_path(p) for p in paths]
        resp = self._session.post(
            f"{self._files_url}/delete",
            json={"paths": full_paths},
        )
        resp.raise_for_status()
        return resp.json()

    def list(self, path="", limit=100, offset=0, sort_by=None):
        """List files in the bucket.

        Args:
            path: Directory path prefix.
            limit: Max results.
            offset: Pagination offset.
            sort_by: Dict with column and order.

        Returns:
            list of file metadata dicts.
        """
        prefix = self._file_path(path) if path else self._bucket
        resp = self._session.get(
            f"{self._files_url}/list",
            params={"prefix": prefix, "limit": limit, "offset": offset},
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("files", result if isinstance(result, list) else [])

    def move(self, from_path, to_path):
        """Move/rename a file within the bucket.

        Args:
            from_path: Source file path.
            to_path: Destination file path.

        Returns:
            dict with result.
        """
        resp = self._session.post(
            f"{self._files_url}/move",
            json={
                "from": self._file_path(from_path),
                "to": self._file_path(to_path),
            },
        )
        resp.raise_for_status()
        return resp.json()

    def copy(self, from_path, to_path):
        """Copy a file within the bucket.

        Args:
            from_path: Source file path.
            to_path: Destination file path.

        Returns:
            dict with result.
        """
        resp = self._session.post(
            f"{self._files_url}/copy",
            json={
                "from": self._file_path(from_path),
                "to": self._file_path(to_path),
            },
        )
        resp.raise_for_status()
        return resp.json()


class StorageClient:
    """Supabase StorageClient-compatible interface.

    Usage:
        client.storage.from_('bucket-name').upload(...)
    """

    def __init__(self, session, files_url):
        self._session = session
        self._files_url = files_url

    def from_(self, bucket_name):
        """Get a StorageBucket instance for the named bucket.

        Args:
            bucket_name: Name of the storage bucket.

        Returns:
            StorageBucket instance.
        """
        return StorageBucket(self._session, self._files_url, bucket_name)

    def list_buckets(self):
        """List all buckets.

        Returns:
            list of bucket info dicts.
        """
        resp = self._session.get(f"{self._files_url}/buckets")
        resp.raise_for_status()
        return resp.json()

    def get_bucket(self, bucket_id):
        """Get bucket info by ID.

        Args:
            bucket_id: Bucket name/ID.

        Returns:
            dict with bucket info.
        """
        resp = self._session.get(f"{self._files_url}/buckets/{bucket_id}")
        resp.raise_for_status()
        return resp.json()

    def create_bucket(self, bucket_id, options=None):
        """Create a new bucket.

        Args:
            bucket_id: Bucket name.
            options: Optional dict with public, file_size_limit, etc.

        Returns:
            dict with created bucket info.
        """
        body = {"name": bucket_id}
        if options:
            body.update(options)
        resp = self._session.post(f"{self._files_url}/buckets", json=body)
        resp.raise_for_status()
        return resp.json()

    def delete_bucket(self, bucket_id):
        """Delete a bucket.

        Args:
            bucket_id: Bucket name/ID.

        Returns:
            dict with result.
        """
        resp = self._session.delete(f"{self._files_url}/buckets/{bucket_id}")
        resp.raise_for_status()
        return resp.json()

    def empty_bucket(self, bucket_id):
        """Empty all files in a bucket.

        Args:
            bucket_id: Bucket name/ID.

        Returns:
            dict with result.
        """
        resp = self._session.post(
            f"{self._files_url}/buckets/{bucket_id}/empty"
        )
        resp.raise_for_status()
        return resp.json()
