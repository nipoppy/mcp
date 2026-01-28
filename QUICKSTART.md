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
# Set your dataset path (optional)
export NIPOPPY_DATASET_ROOT=/path/to/your/nipoppy/dataset

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
      "args": ["-m", "nipoppy_mcp.server"],
      "env": {
        "NIPOPPY_DATASET_ROOT": "/path/to/your/nipoppy/dataset"
      }
    }
  }
}
```

### 3. Test with Example Dataset

```bash
# Use the included example dataset
cd mcp
export NIPOPPY_DATASET_ROOT=$(pwd)/examples/nipoppy_dataset

# Test the tools
python examples/test_tools.py
```

## Available Tools

Once connected to an MCP client, you can query your dataset using natural language:

### Dataset Configuration
- "What's the dataset name and description?"
- "Show me the global configuration"

### Subjects and Sessions
- "List all subjects in the BIDS directory"
- "How many subjects are in the dataset?"
- "Which subjects have multiple sessions?"

### Pipelines
- "What pipelines are available?"
- "Show me the fmriprep configuration"
- "List all pipeline configuration files"

### File System
- "What's the directory structure?"
- "List files in the pipelines directory"
- "Read the manifest file"

### Manifest Data
- "Show me the first 20 rows of the manifest"
- "What's in the manifest?"

## Example Queries

Here are some example interactions you might have with Claude Desktop using the Nipoppy MCP server:

**Query:** "What is this Nipoppy dataset about?"
- Uses: `get_dataset_info`
- Returns: Dataset name, description, version, paths, etc.

**Query:** "List all subjects and their sessions"
- Uses: `list_subjects`
- Returns: Subject IDs with their associated sessions

**Query:** "What processing pipelines are configured?"
- Uses: `list_pipelines`
- Returns: List of pipeline directories and their config files

**Query:** "Show me the fmriprep settings"
- Uses: `get_pipeline_config`
- Returns: Full pipeline configuration including container, arguments, resources

## Troubleshooting

### Server won't start
- Make sure you've installed the dependencies: `pip install -e .`
- Check that Python 3.8+ is installed: `python --version`

### Can't find dataset
- Set the `NIPOPPY_DATASET_ROOT` environment variable
- Or pass `dataset_root` parameter to each tool
- Or run the server from within your dataset directory

### Tools return errors
- Verify your dataset has the expected structure (bids/, pipelines/, global_config.json, etc.)
- Check file permissions
- Look for typos in file or directory names

## Next Steps

- Read the full [README.md](README.md) for detailed information
- Check out [examples/test_tools.py](examples/test_tools.py) for Python API usage
- Run the test suite: `pytest tests/`
- Explore the [Nipoppy documentation](https://nipoppy.readthedocs.io/)

## Support

For issues or questions:
- Open an issue on GitHub
- Check the [Nipoppy documentation](https://nipoppy.readthedocs.io/)
- Review the [MCP documentation](https://modelcontextprotocol.io/)
