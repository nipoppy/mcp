# Nipoppy MCP Server

A Model Context Protocol (MCP) interface for the [Nipoppy](https://github.com/nipoppy/nipoppy) neuroimaging dataset framework. This server exposes Nipoppy dataset information through MCP, allowing AI agents to query dataset configurations, manifests, pipelines, and structure.

## What is Nipoppy?

Nipoppy is a lightweight framework for standardized organization and processing of neuroimaging-clinical datasets. It follows the Brain Imaging Data Structure (BIDS) standard and provides tools for managing datasets and processing pipelines.

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that allows AI applications (LLMs) to access external tools and resources through a consistent interface. This server exposes Nipoppy dataset information as MCP tools.

## Features

This MCP server provides the following tools to query Nipoppy datasets:

- **`get_dataset_info`**: Read the global_config.json configuration file
- **`get_manifest`**: Read the manifest.csv or manifest.tsv file
- **`list_pipelines`**: List all available processing pipelines
- **`get_pipeline_config`**: Read configuration for a specific pipeline
- **`list_subjects`**: List subjects in BIDS or derivatives directories
- **`get_directory_structure`**: View the dataset directory structure
- **`list_files_in_directory`**: List files in a specific directory
- **`read_file`**: Read any file within the dataset

## Installation

### Prerequisites

- Python 3.8 or higher
- A Nipoppy dataset (or create a test dataset)

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
```

#### 2. Configure with Claude Desktop

Add to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "nipoppy": {
      "command": "python",
      "args": ["-m", "nipoppy_mcp.server"],
      "env": {
        "NIPOPPY_DATASET_ROOT": "/path/to/your/nipoppy/dataset"
      }
    }
  }
}
```

### Using the Tools

Once connected to an MCP-compatible client, you can use natural language to query your Nipoppy dataset:

**Example queries:**
- "What's in the global configuration?"
- "List all subjects in the BIDS directory"
- "Show me the available pipelines"
- "What's the structure of the dataset?"
- "Read the fmriprep configuration"

### Dataset Root Configuration

The server determines the dataset root in the following order:

1. `dataset_root` parameter passed to tool functions
2. `NIPOPPY_DATASET_ROOT` environment variable
3. Current working directory

## Example Nipoppy Dataset Structure

A typical Nipoppy dataset has this structure:

```
nipoppy_dataset/
├── global_config.json      # Main configuration file
├── manifest.tsv            # Subject/session tracking
├── bids/                   # BIDS-compliant raw data
│   ├── sub-001/
│   ├── sub-002/
│   └── ...
├── derivatives/            # Processed data outputs
├── pipelines/              # Pipeline configurations
│   ├── fmriprep-20.2.7/
│   ├── freesurfer-7.1.1/
│   └── ...
├── sourcedata/            # Original raw data
├── logs/                  # Processing logs
└── scratch/               # Temporary files
```

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
