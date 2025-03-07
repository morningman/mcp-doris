# Apache Doris MCP Server

[![smithery badge](https://smithery.ai/badge/@morningman/mcp-doris)](https://smithery.ai/server/@morningman/mcp-doris)

An [MCP server](https://modelcontextprotocol.io/introduction) for [Apache Doris](https://doris.apache.org/).

![Demo](mcp-doris-demo.gif)

## Usage

### Cursor

```
Name: doris
Type: command
Command: DORIS_HOST=<doris-host> DORIS_PORT=<port> DORIS_USER=<doris-user> DORIS_PASSWORD=<doris-pwd> uv run --with mcp-doris --python 3.13 mcp-doris
```

## Development

### Prerequest

- install [uv](https://docs.astral.sh/uv)

### Run MCP Inspector

```sql
cd /path/to/mcp-doris
uv sync
source .venv/bin/activate
export PYTHONPATH=/path/to/mcp-doris:$PYTHONPATH
env DORIS_HOST=<doris-host> DORIS_PORT=<port> DORIS_USER=<doris-user> DORIS_PASSWORD=<doris-pwd> mcp dev mcp_doris/mcp_server.py
```

Then visit `http://localhost:5173` in web browser.

## Publish

```
uv build
uv publish
```
