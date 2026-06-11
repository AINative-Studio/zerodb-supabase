"""
QueryBuilder -- Supabase-compatible query builder for ZeroDB tables.

Supports the Supabase chaining pattern:

    client.table('users').select('*').eq('active', True).limit(10).execute()
"""


class APIResponse:
    """Response wrapper matching Supabase APIResponse."""

    def __init__(self, data, count=None, status_code=200):
        self.data = data
        self.count = count
        self.status_code = status_code

    def __repr__(self):
        return f"APIResponse(data={self.data!r}, count={self.count})"


class QueryBuilder:
    """Chainable query builder that maps Supabase query API to ZeroDB.

    Usage:
        qb = QueryBuilder(session, base_url, 'users')
        result = qb.select('*').eq('active', True).execute()
    """

    def __init__(self, session, tables_url, table_name):
        self._session = session
        self._tables_url = tables_url
        self._table = table_name
        self._operation = None  # 'select', 'insert', 'update', 'upsert', 'delete'
        self._columns = "*"
        self._filters = []
        self._order_col = None
        self._order_asc = True
        self._limit_val = None
        self._offset_val = None
        self._data = None
        self._count_mode = None
        self._single = False

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def select(self, columns="*", count=None):
        """Select columns from the table.

        Args:
            columns: Column names (comma-separated string or '*').
            count: Count mode ('exact', 'planned', 'estimated') or None.

        Returns:
            self for chaining.
        """
        self._operation = "select"
        self._columns = columns
        self._count_mode = count
        return self

    def insert(self, data, count=None):
        """Insert row(s) into the table.

        Args:
            data: Dict (single row) or list of dicts (multiple rows).
            count: Count mode or None.

        Returns:
            self for chaining.
        """
        self._operation = "insert"
        self._data = data if isinstance(data, list) else [data]
        self._count_mode = count
        return self

    def update(self, data, count=None):
        """Update rows matching filters.

        Args:
            data: Dict of columns to update.
            count: Count mode or None.

        Returns:
            self for chaining.
        """
        self._operation = "update"
        self._data = data
        self._count_mode = count
        return self

    def upsert(self, data, count=None):
        """Insert or update row(s).

        Args:
            data: Dict or list of dicts.
            count: Count mode or None.

        Returns:
            self for chaining.
        """
        self._operation = "upsert"
        self._data = data if isinstance(data, list) else [data]
        self._count_mode = count
        return self

    def delete(self, count=None):
        """Delete rows matching filters.

        Args:
            count: Count mode or None.

        Returns:
            self for chaining.
        """
        self._operation = "delete"
        self._count_mode = count
        return self

    # ------------------------------------------------------------------
    # Filters (PostgREST-compatible)
    # ------------------------------------------------------------------

    def eq(self, column, value):
        """Equal to."""
        self._filters.append({"column": column, "op": "eq", "value": value})
        return self

    def neq(self, column, value):
        """Not equal to."""
        self._filters.append({"column": column, "op": "neq", "value": value})
        return self

    def gt(self, column, value):
        """Greater than."""
        self._filters.append({"column": column, "op": "gt", "value": value})
        return self

    def gte(self, column, value):
        """Greater than or equal to."""
        self._filters.append({"column": column, "op": "gte", "value": value})
        return self

    def lt(self, column, value):
        """Less than."""
        self._filters.append({"column": column, "op": "lt", "value": value})
        return self

    def lte(self, column, value):
        """Less than or equal to."""
        self._filters.append({"column": column, "op": "lte", "value": value})
        return self

    def like(self, column, pattern):
        """LIKE pattern match."""
        self._filters.append({"column": column, "op": "like", "value": pattern})
        return self

    def ilike(self, column, pattern):
        """Case-insensitive LIKE pattern match."""
        self._filters.append({"column": column, "op": "ilike", "value": pattern})
        return self

    def is_(self, column, value):
        """IS check (for null/true/false)."""
        self._filters.append({"column": column, "op": "is", "value": value})
        return self

    def in_(self, column, values):
        """IN check (value in list)."""
        self._filters.append({"column": column, "op": "in", "value": values})
        return self

    def contains(self, column, value):
        """Contains (for arrays/JSON)."""
        self._filters.append({"column": column, "op": "cs", "value": value})
        return self

    def contained_by(self, column, value):
        """Contained by (for arrays/JSON)."""
        self._filters.append({"column": column, "op": "cd", "value": value})
        return self

    def not_(self, column, op, value):
        """Negate a filter."""
        self._filters.append({"column": column, "op": f"not.{op}", "value": value})
        return self

    def or_(self, *filters):
        """OR filter (comma-separated PostgREST conditions)."""
        self._filters.append({"op": "or", "value": filters})
        return self

    def filter(self, column, op, value):
        """Generic filter."""
        self._filters.append({"column": column, "op": op, "value": value})
        return self

    # ------------------------------------------------------------------
    # Modifiers
    # ------------------------------------------------------------------

    def order(self, column, desc=False):
        """Order results by column.

        Args:
            column: Column name.
            desc: If True, order descending.

        Returns:
            self for chaining.
        """
        self._order_col = column
        self._order_asc = not desc
        return self

    def limit(self, count):
        """Limit number of results.

        Args:
            count: Maximum number of rows.

        Returns:
            self for chaining.
        """
        self._limit_val = count
        return self

    def offset(self, count):
        """Skip first N results (for pagination).

        Args:
            count: Number of rows to skip.

        Returns:
            self for chaining.
        """
        self._offset_val = count
        return self

    def range(self, start, end):
        """Limit to a range of rows.

        Args:
            start: Start index.
            end: End index (inclusive).

        Returns:
            self for chaining.
        """
        self._offset_val = start
        self._limit_val = end - start + 1
        return self

    def single(self):
        """Return a single row instead of a list.

        Returns:
            self for chaining.
        """
        self._single = True
        self._limit_val = 1
        return self

    def maybe_single(self):
        """Return a single row or None.

        Returns:
            self for chaining.
        """
        self._single = True
        self._limit_val = 1
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def _build_query_body(self):
        """Build the request body for ZeroDB tables API."""
        body = {"table": self._table}

        if self._filters:
            body["filters"] = self._filters

        if self._columns != "*":
            body["columns"] = [c.strip() for c in self._columns.split(",")]

        if self._order_col:
            body["order_by"] = {
                "column": self._order_col,
                "ascending": self._order_asc,
            }

        if self._limit_val is not None:
            body["limit"] = self._limit_val

        if self._offset_val is not None:
            body["offset"] = self._offset_val

        return body

    def execute(self):
        """Execute the query and return an APIResponse.

        Returns:
            APIResponse with data and optional count.
        """
        if self._operation == "select":
            return self._execute_select()
        elif self._operation == "insert":
            return self._execute_insert()
        elif self._operation == "update":
            return self._execute_update()
        elif self._operation == "upsert":
            return self._execute_upsert()
        elif self._operation == "delete":
            return self._execute_delete()
        else:
            raise ValueError(
                "No operation specified. Call select(), insert(), update(), "
                "upsert(), or delete() before execute()."
            )

    def _execute_select(self):
        """Execute a SELECT query via ZeroDB tables API."""
        body = self._build_query_body()
        body["operation"] = "query"

        resp = self._session.post(f"{self._tables_url}/query", json=body)
        resp.raise_for_status()
        result = resp.json()

        rows = result.get("rows", result.get("data", result))
        if isinstance(rows, dict):
            rows = rows.get("rows", [rows])

        count = result.get("count") if self._count_mode else None

        if self._single:
            rows = rows[0] if rows else None

        return APIResponse(data=rows, count=count, status_code=resp.status_code)

    def _execute_insert(self):
        """Execute an INSERT via ZeroDB tables API."""
        body = {
            "table": self._table,
            "operation": "insert",
            "rows": self._data,
        }

        resp = self._session.post(f"{self._tables_url}/insert", json=body)
        resp.raise_for_status()
        result = resp.json()

        inserted = result.get("rows", result.get("data", self._data))
        return APIResponse(data=inserted, status_code=resp.status_code)

    def _execute_update(self):
        """Execute an UPDATE via ZeroDB tables API."""
        body = {
            "table": self._table,
            "operation": "update",
            "data": self._data,
            "filters": self._filters,
        }

        resp = self._session.post(f"{self._tables_url}/update", json=body)
        resp.raise_for_status()
        result = resp.json()

        updated = result.get("rows", result.get("data", []))
        return APIResponse(data=updated, status_code=resp.status_code)

    def _execute_upsert(self):
        """Execute an UPSERT via ZeroDB tables API."""
        body = {
            "table": self._table,
            "operation": "upsert",
            "rows": self._data,
        }

        resp = self._session.post(f"{self._tables_url}/upsert", json=body)
        resp.raise_for_status()
        result = resp.json()

        upserted = result.get("rows", result.get("data", self._data))
        return APIResponse(data=upserted, status_code=resp.status_code)

    def _execute_delete(self):
        """Execute a DELETE via ZeroDB tables API."""
        body = {
            "table": self._table,
            "operation": "delete",
            "filters": self._filters,
        }

        resp = self._session.post(f"{self._tables_url}/delete", json=body)
        resp.raise_for_status()
        result = resp.json()

        deleted = result.get("rows", result.get("data", []))
        count = result.get("count")
        return APIResponse(data=deleted, count=count, status_code=resp.status_code)
