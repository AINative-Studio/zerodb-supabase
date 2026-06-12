# zerodb-supabase

**Drop-in replacement for [supabase-py](https://pypi.org/project/supabase/) backed by ZeroDB.**

Same API. Free cloud database. No Supabase account needed.

[![PyPI](https://img.shields.io/pypi/v/zerodb-supabase)](https://pypi.org/project/zerodb-supabase/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why switch?

| | supabase-py | zerodb-supabase |
|---|---|---|
| **Database** | Supabase Cloud (paid after free tier) | ZeroDB (free tier) |
| **Storage** | Supabase Storage (limited) | ZeroDB S3-compatible (generous) |
| **Functions** | Edge Functions (Deno only) | ZeroDB Functions (Python, JS, TS) |
| **Provisioning** | Manual dashboard setup | Auto-provision on first use |
| **Vectors** | pgvector extension | Built-in vector search |
| **AI Memory** | Not available | ZeroMemory cognitive memory |
| **License** | Apache-2.0 | MIT |

## Installation

```bash
pip install zerodb-supabase
```

## Migration (30 seconds)

Change one import:

```python
# Before
from supabase import create_client

# After
from zerodb_supabase import create_client
```

That's it. Every method works the same.

## Quick Start

```python
from zerodb_supabase import create_client

# Auto-provisions a free ZeroDB project on first use
client = create_client()

# Query data
data = client.table('users').select('*').eq('active', True).execute()
print(data.data)  # [{'id': 1, 'name': 'Alice', 'active': True}, ...]

# Insert data
client.table('users').insert({
    'name': 'Alice',
    'email': 'alice@example.com'
}).execute()

# Update data
client.table('users').update({
    'name': 'Alice Updated'
}).eq('id', 1).execute()

# Delete data
client.table('users').delete().eq('id', 1).execute()

# Storage (S3-compatible)
client.storage.from_('avatars').upload('avatar.png', open('avatar.png', 'rb'))
url = client.storage.from_('avatars').get_public_url('avatar.png')

# Functions (ZeroDB Functions)
result = client.functions.invoke('process-upload', {'file_id': '123'})
print(result.data)
```

## API Reference

### `create_client(supabase_url=None, supabase_key=None, **kwargs)`

Create a client. Credentials resolved in order:
1. Constructor arguments (`api_key`, `project_id`)
2. Supabase-compatible args (`supabase_key` used as API key)
3. Environment variables (`ZERODB_API_KEY`, `ZERODB_PROJECT_ID`)
4. Config file (`~/.zerodb/config.json`)
5. Auto-provision (free, no signup)

### Query Builder

| Method | Description |
|--------|-------------|
| `table(name).select('*')` | Select rows |
| `table(name).insert(data)` | Insert row(s) |
| `table(name).update(data)` | Update rows |
| `table(name).upsert(data)` | Insert or update |
| `table(name).delete()` | Delete rows |

### Filters (Chainable)

| Method | SQL Equivalent |
|--------|---------------|
| `.eq(col, val)` | `WHERE col = val` |
| `.neq(col, val)` | `WHERE col != val` |
| `.gt(col, val)` | `WHERE col > val` |
| `.gte(col, val)` | `WHERE col >= val` |
| `.lt(col, val)` | `WHERE col < val` |
| `.lte(col, val)` | `WHERE col <= val` |
| `.like(col, pattern)` | `WHERE col LIKE pattern` |
| `.ilike(col, pattern)` | `WHERE col ILIKE pattern` |
| `.is_(col, val)` | `WHERE col IS val` |
| `.in_(col, list)` | `WHERE col IN (list)` |
| `.contains(col, val)` | `WHERE col @> val` |
| `.not_(col, op, val)` | Negate filter |

### Modifiers

| Method | Description |
|--------|-------------|
| `.order(col, desc=False)` | Order results |
| `.limit(n)` | Limit results |
| `.offset(n)` | Skip rows |
| `.range(start, end)` | Row range |
| `.single()` | Return one row |
| `.maybe_single()` | Return one or None |

### Storage

```python
bucket = client.storage.from_('bucket-name')
bucket.upload('path/file.png', file_data)
bucket.download('path/file.png')
bucket.get_public_url('path/file.png')
bucket.create_signed_url('path/file.png', expires_in=3600)
bucket.remove(['file1.png', 'file2.png'])
bucket.list()
bucket.move('old.png', 'new.png')
bucket.copy('src.png', 'dst.png')
```

### Functions

```python
# Invoke a function
result = client.functions.invoke('function-name', {'key': 'value'})

# List functions
functions = client.functions.list()

# RPC shorthand
result = client.rpc('function-name', {'param': 'value'})
```

## Configuration

### Environment Variables

```bash
export ZERODB_API_KEY="your-api-key"
export ZERODB_PROJECT_ID="your-project-id"
# Optional: custom endpoint
export ZERODB_BASE_URL="https://api.ainative.studio"
```

### Config File

```json
// ~/.zerodb/config.json
{
  "api_key": "your-api-key",
  "project_id": "your-project-id"
}
```

### Auto-Provisioning

If no credentials are found, `zerodb-supabase` automatically creates a free ZeroDB project. Credentials are saved to `~/.zerodb/config.json` for future use.

## Supabase Migration Guide

### 1. Install

```bash
pip uninstall supabase
pip install zerodb-supabase
```

### 2. Update imports

```python
# Before
from supabase import create_client, Client

# After
from zerodb_supabase import create_client, Client
```

### 3. Remove Supabase config

No more `SUPABASE_URL` or `SUPABASE_KEY` environment variables needed. ZeroDB auto-provisions.

### 4. That's it

All your queries, storage calls, and function invocations work unchanged.

---

**Built by [AINative Studio](https://ainative.studio)**

Free database for AI agents. Auto-provisions in 200ms.

[Get started](https://ainative.studio) | [Documentation](https://docs.ainative.studio) | [GitHub](https://github.com/AINative-Studio/zerodb-supabase)

## License

MIT

---

## Zero-Config Auto-Provisioning

**No account needed to start.** On first run, this package automatically:

1. Provisions a **free ZeroDB instance** (~800ms)
2. Saves credentials locally (`.env`, `.mcp.json`)
3. Prints a **claim link** in your terminal

### The 72-Hour Window

Your auto-provisioned instance is **free for 72 hours**. To keep your data permanently, visit the **claim URL** printed in your terminal.

### For AI Agents

If a coding agent (Claude Code, Cursor, Windsurf) installs this package:
- Auto-provisions without human intervention
- The **claim URL** appears in agent output — visit it to take ownership
- `.claude/CLAUDE.md` instructs agents to surface the claim link to you
- Check `.env` or `~/.ainative/config.json` for your project ID if you miss it
