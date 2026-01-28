# Quick Start Guide

This guide will help you get started with the Nipoppy MCP Server quickly.

## Installation

```bash
# Clone the repository
git clone https://github.com/nipoppy/mcp.git
cd mcp

# Install the package
pip install -e .
```

## Basic Usage

### 1. Start the Server

```bash
# Run the server
python -m nipoppy_mcp.server
```

### 2. Use with Claude Desktop

Add this to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nipoppy": {
      "command": "python",
      "args": ["-m", "nipoppy_mcp.server"]
    }
  }
}
```

## Available Tool

Once connected to an MCP client, you can list files in directories:

### List Files
- "List files in /home/user/documents"
- "What files are in /tmp?"

## Example Usage

The `list_files` tool takes a directory path and returns a list of file names (not subdirectories).

**Query:** "List files in /home/user/data"
- Uses: `list_files`
- Returns: List of file names in the directory

## Next Steps

- Read the full [README.md](README.md) for detailed information
- Run the test suite: `pytest tests/`
- Explore the [Nipoppy documentation](https://nipoppy.readthedocs.io/)

## Support

For issues or questions:
- Open an issue on GitHub
- Check the [Nipoppy documentation](https://nipoppy.readthedocs.io/)
- Review the [MCP documentation](https://modelcontextprotocol.io/)
