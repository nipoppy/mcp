# Nipoppy MCP Server

A Model Context Protocol (MCP) interface for the [Nipoppy](https://github.com/nipoppy/nipoppy) neuroimaging dataset framework. This server exposes a simple tool through MCP, allowing AI agents to list files in directories.

## What is Nipoppy?

Nipoppy is a lightweight framework for standardized organization and processing of neuroimaging-clinical datasets. It follows the Brain Imaging Data Structure (BIDS) standard and provides tools for managing datasets and processing pipelines.

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that allows AI applications (LLMs) to access external tools and resources through a consistent interface. This server exposes a file listing tool as an MCP tool.

## Features

This MCP server provides comprehensive access to Nipoppy neuroimaging datasets through both **tools** and **resources**:

### MCP Resources (Automatic Context)
Context information automatically available to AI agents without function calls:

- **`nipoppy://config`** - Global dataset configuration and metadata
- **`nipoppy://manifest`** - Dataset structure manifest (participants/sessions/datatypes)
- **`nipoppy://status/curation`** - Data availability at different curation stages
- **`nipoppy://status/processing`** - Pipeline completion status across participants/sessions
- **`nipoppy://pipelines/{pipeline_name}/{version}/config`** - Individual pipeline configuration
- **`nipoppy://pipelines/{pipeline_name}/{version}/descriptor`** - Boutiques pipeline descriptor
- **`nipoppy://demographics`** - De-identified participant demographic information
- **`nipoppy://bids/description`** - BIDS dataset description and metadata

### MCP Tools (On-demand Functions)

#### Primary Tools (Refactored & Enhanced)
- **`get_participants_sessions`** - Unified participant/session query with filtering by data stage
- **`get_dataset_info`** - Enhanced dataset overview with configurable detail levels  
- **`navigate_dataset`** - File path and configuration access with smart path resolution

#### Legacy Tools (Deprecated)
- **`list_manifest_participants_sessions`** - Use `get_participants_sessions(data_stage="all")` instead
- **`list_manifest_imaging_participants_sessions`** - Use `get_participants_sessions(data_stage="imaging")` instead
- **`get_pre_reorg_participants_sessions`** - Use `get_participants_sessions(data_stage="downloaded")` instead
- **`get_post_reorg_participants_sessions`** - Use `get_participants_sessions(data_stage="organized")` instead
- **`get_bids_participants_sessions`** - Use `get_participants_sessions(data_stage="bidsified")` instead
- **`list_processed_participants_sessions`** - Use `get_participants_sessions(data_stage="processed", ...)` instead

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

### Using the Tools and Resources

Once connected to an MCP-compatible client, you can access Nipoppy dataset information through both automatic context and explicit tool calls.

**Setting the Dataset Root:**
The server requires the `NIPOPPY_DATASET_ROOT` environment variable to be set for resources to work:

```bash
export NIPOPPY_DATASET_ROOT=/path/to/your/nipoppy/dataset
```

**Example Queries:**

#### Dataset Overview (using tools)
- "Get information about this dataset"
- "How many participants and sessions are in this dataset?"
- "What pipelines are installed and what's their status?"

#### Participant/Session Queries (using tools)
- "List all participants and sessions in the dataset"
- "Show me participants with imaging data"
- "Which participants have completed fMRIPrep processing?"
- "Get participants with BIDS-converted data"

#### Navigation and Configuration (using tools)  
- "Navigate to the fMRIPrep output directory"
- "Show me the configuration for the latest MRIQC pipeline"
- "Get the path to the derivatives directory"

#### Context Access (using resources)
- The server automatically provides context through resources, so you can ask about:
  - "What's the global configuration of this dataset?"
  - "Show me the dataset manifest"
  - "What's the curation status of the data?"
  - "Get the BIDS dataset description"

#### Pipeline Information (using resources)
- "Get the configuration for fMRIPrep version 23.2.0"
- "Show me the Boutiques descriptor for the MRIQC pipeline"

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Or run basic import tests
python -c "from nipoppy_mcp.server import mcp; print('✅ MCP server imports successfully')"
```

### Testing Implementation

The refactored implementation includes comprehensive error handling and validation. Test with:

```bash
# Test basic functionality
python -c "
from nipoppy_mcp.server import get_participants_sessions, get_dataset_info, navigate_dataset
print('✅ Refactored tools imported successfully')

# Test validation (these should raise appropriate errors)
get_participants_sessions('/fake/path', data_stage='invalid_stage')
navigate_dataset('/fake/path', path_type='invalid_type')
"

# Test resource functions
python -c "
from nipoppy_mcp.server import get_dataset_config, get_dataset_manifest
print('✅ Resource functions imported successfully')
"
```

### Project Structure

```
nipoppy-mcp/
├── nipoppy_mcp/
│   ├── __init__.py
│   └── server.py          # Main MCP server implementation
│                          # - 8 MCP resources (automatic context)
│                          # - 3 refactored tools (unified interface) 
│                          # - 7 deprecated tools (backward compatibility)
├── tests/                 # Test files
├── pyproject.toml        # Project configuration
└── README.md
```

### Implementation Details

The refactored server provides:

- **8 MCP Resources**: Automatic context loading of dataset metadata, configuration, and status
- **3 Unified Tools**: Replace 7 previous specialized tools with a unified interface
- **7 Deprecated Tools**: Maintained for backward compatibility with deprecation warnings
- **Strict Validation**: Comprehensive error handling and parameter validation
- **Type Safety**: Full type hints and structured data returns

### Migration Guide

For existing users migrating from the old tools:

| Old Tool | New Tool Call |
|-----------|---------------|
| `list_manifest_participants_sessions()` | `get_participants_sessions(data_stage="all")` |
| `list_manifest_imaging_participants_sessions()` | `get_participants_sessions(data_stage="imaging")` |
| `get_pre_reorg_participants_sessions()` | `get_participants_sessions(data_stage="downloaded")` |
| `get_post_reorg_participants_sessions()` | `get_participants_sessions(data_stage="organized")` |
| `get_bids_participants_sessions()` | `get_participants_sessions(data_stage="bidsified")` |
| `list_processed_participants_sessions(name, ver, step)` | `get_participants_sessions(data_stage="processed", pipeline_name=name, pipeline_version=ver, pipeline_step=step)` |

### Example Usage

The repository includes `example_usage.py` to demonstrate the refactored functionality:

```bash
# Set your dataset path
export NIPOPPY_DATASET_ROOT=/path/to/your/nipoppy/dataset

# Run the example
python example_usage.py
```

This script demonstrates:
- Enhanced dataset information retrieval
- Unified participant/session filtering by data stage
- Dataset navigation and path resolution
- Error handling and validation

### Quick Start with Resources

For immediate access to dataset information (requires NIPOPPY_DATASET_ROOT):

```python
import os
os.environ['NIPOPPY_DATASET_ROOT'] = '/path/to/dataset'

from nipoppy_mcp.server import get_dataset_config

# Resources are available as direct function calls
config = get_dataset_config()  # Auto-loads from environment variable
print(f"Dataset has {len(config['installed_pipelines'])} pipelines")
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
