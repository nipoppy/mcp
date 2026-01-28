# Nipoppy MCP Server

A Model Context Protocol (MCP) interface for the [Nipoppy](https://github.com/nipoppy/nipoppy) neuroimaging dataset framework. This server exposes a simple tool through MCP, allowing AI agents to list files in directories.

## What is Nipoppy?

Nipoppy is a lightweight framework for standardized organization and processing of neuroimaging-clinical datasets. It follows the Brain Imaging Data Structure (BIDS) standard and provides tools for managing datasets and processing pipelines.

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that allows AI applications (LLMs) to access external tools and resources through a consistent interface. This server exposes a file listing tool as an MCP tool.

## Features

This MCP server provides the following tool:

- **`list_files`**: List files in a given directory

## Installation

### Prerequisites

- Python 3.8 or higher

### Install the package

```bash
# Clone the repository
git clone https://github.com/nipoppy/mcp.git
cd mcp

# Install dependencies
pip install -e .
```

## Usage

### Running the MCP Server

The server can be run in different modes depending on your use case:

#### 1. STDIO Mode (for local desktop apps like Claude Desktop)

```bash
# Set the dataset root (optional, defaults to current directory)
export NIPOPPY_DATASET_ROOT=/path/to/your/nipoppy/dataset

# Run the server
python -m nipoppy_mcp.server
```bash
# Run the server
python -m nipoppy_mcp.server
```

#### 2. Configure with Claude Desktop

Add to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

### Using the Tool

Once connected to an MCP-compatible client, you can use natural language to list files in directories:

**Example queries:**
- "List files in /path/to/directory"
- "What files are in my home directory?"

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
mcp/
├── nipoppy_mcp/
│   ├── __init__.py
│   └── server.py          # Main MCP server implementation
├── tests/                 # Test files
├── pyproject.toml        # Project configuration
└── README.md
```

## Contributing

Contributions are welcome! This is a Brainhack 2026 project. Please feel free to submit issues and pull requests.

## License

MIT License - see LICENSE file for details.

## Resources

- [Nipoppy Documentation](https://nipoppy.readthedocs.io/)
- [Nipoppy GitHub](https://github.com/nipoppy/nipoppy)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
