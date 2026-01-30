# Nipoppy MCP Server

A Model Context Protocol (MCP) interface for the
[Nipoppy](https://github.com/nipoppy/nipoppy) neuroimaging dataset
framework. This server exposes tools through MCP that allow AI Agents
to interact with in a more deliberate way with Nipoppy studies.

## What is Nipoppy?

Nipoppy is a lightweight framework for standardized organization and
processing of neuroimaging-clinical datasets. It follows the Brain
Imaging Data Structure (BIDS) standard and provides tools for managing
datasets and processing pipelines.

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that
allows AI applications (LLMs) to access external tools and resources
through a consistent interface. This server exposes tools for
summarizing the current processing status of a Nipoppy study.

## Features

This MCP server provides the following tools:

- **`get_dataset_info`**: aggregate top level information for use
- add others after refactor...

## Installation

### Prerequisites

- Python 3.10 or higher

### Option 1: Install the package

```bash
# Clone the repository
git clone https://github.com/nipoppy/mcp.git
cd mcp

# Install dependencies
pip install -e .
```

### [PENDING RELEASE] Option 2: Docker Container

You can also use the pre-built Docker container from GitHub Container Registry:

```bash
# Pull the latest version
docker pull ghcr.io/bcmcpher/nipoppy-mcp:latest

# Pull a specific version
docker pull ghcr.io/bcmcpher/nipoppy-mcp:v0.1.0
```

## Usage

### Running the MCP Server

The server can be run in different modes depending on your use case:

#### 1. STDIO Mode (for local desktop apps like Claude Desktop)

```bash
# Set the dataset root (optional, defaults to current directory)

# Run the server
python -m nipoppy_mcp.server
```

#### [PENDING] 2. Docker Mode

```bash
# Run with local dataset mounted
docker run -v /path/to/your/nipoppy/dataset:/data ghcr.io/bcmcpher/nipoppy-mcp:latest

# Run with specific version and custom dataset path
docker run \
  -v /path/to/dataset:/data \
  -e NIPOPPY_DATASET_ROOT=/data \
  ghcr.io/bcmcpher/nipoppy-mcp:v0.1.0
```

#### 2. Configure with Claude Desktop / OpenCode

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
- "What pipelines are installed in my Nipoppy study (/path/to/nipoppy_dataset_root)"
- "How many participants have both Freesurfer 7.3.2 and MRIQC completed?"

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

## Docker Image Information

The Docker container is automatically built and published to GitHub Container Registry (GHCR) when a new release is tagged:

- **Registry**: `ghcr.io/bcmcpher/nipoppy-mcp`
- **Architecture**: Multi-platform (linux/amd64, linux/arm64)
- **Tags**:
  - `latest` - Points to the most recent release
  - `v0.1.0` - Full semantic version
  - `v0.1` - Minor version
  - `v0` - Major version

### Building from Source

```bash
# Build the Docker image locally
docker build -t nipoppy-mcp .

# Run the locally built image
docker run -v /path/to/dataset:/data nipoppy-mcp
```

## Resources

- [Nipoppy Documentation](https://nipoppy.readthedocs.io/)
- [Nipoppy GitHub](https://github.com/nipoppy/nipoppy)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
