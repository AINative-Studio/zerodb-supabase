"""
FunctionsClient -- Supabase Edge Functions-compatible interface backed by ZeroDB hooks API.

    result = client.functions.invoke('process-upload', {'file_id': '123'})
"""


class FunctionResponse:
    """Response wrapper for function invocations."""

    def __init__(self, data=None, status_code=200):
        self.data = data
        self.status_code = status_code

    def __repr__(self):
        return f"FunctionResponse(data={self.data!r})"


class FunctionsClient:
    """Supabase FunctionsClient-compatible interface backed by ZeroDB hooks API.

    Maps Supabase Edge Functions to ZeroDB's hooks/functions system.
    """

    def __init__(self, session, hooks_url):
        self._session = session
        self._hooks_url = hooks_url

    def invoke(self, function_name, invoke_options=None):
        """Invoke a serverless function.

        Args:
            function_name: Name of the function to invoke.
            invoke_options: Dict with body, headers, method, etc.
                Compatible with Supabase invoke options.

        Returns:
            FunctionResponse with the result.
        """
        options = invoke_options or {}

        # Supabase supports body as dict or the options dict itself
        body = options.get("body", options) if isinstance(options, dict) else options

        # Build request
        headers = {}
        if isinstance(options, dict) and "headers" in options:
            headers = options["headers"]

        method = "POST"
        if isinstance(options, dict) and "method" in options:
            method = options["method"].upper()

        resp = self._session.request(
            method,
            f"{self._hooks_url}/invoke/{function_name}",
            json=body if method in ("POST", "PUT", "PATCH") else None,
            params=body if method == "GET" else None,
            headers=headers,
        )
        resp.raise_for_status()

        try:
            data = resp.json()
        except ValueError:
            data = resp.text

        return FunctionResponse(data=data, status_code=resp.status_code)

    def list(self):
        """List all available functions.

        Returns:
            list of function info dicts.
        """
        resp = self._session.get(f"{self._hooks_url}/list")
        resp.raise_for_status()
        return resp.json()

    def get(self, function_name):
        """Get info about a specific function.

        Args:
            function_name: Function name.

        Returns:
            dict with function info.
        """
        resp = self._session.get(f"{self._hooks_url}/{function_name}")
        resp.raise_for_status()
        return resp.json()

    def create(self, function_name, body=None):
        """Create/deploy a new function.

        Args:
            function_name: Function name.
            body: Dict with function code/config.

        Returns:
            dict with created function info.
        """
        payload = {"name": function_name}
        if body:
            payload.update(body)
        resp = self._session.post(f"{self._hooks_url}/create", json=payload)
        resp.raise_for_status()
        return resp.json()

    def delete(self, function_name):
        """Delete a function.

        Args:
            function_name: Function name.

        Returns:
            dict with result.
        """
        resp = self._session.delete(f"{self._hooks_url}/{function_name}")
        resp.raise_for_status()
        return resp.json()
