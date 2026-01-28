"""Tests for the Nipoppy MCP Server."""

import json
import os
from pathlib import Path
import pytest

# Set up test dataset path
TEST_DATASET = Path(__file__).parent.parent / "examples" / "nipoppy_dataset"


def test_dataset_exists():
    """Test that the example dataset exists."""
    assert TEST_DATASET.exists()
    assert (TEST_DATASET / "global_config.json").exists()
    assert (TEST_DATASET / "manifest.tsv").exists()


def test_import_server():
    """Test that the server module can be imported."""
    from nipoppy_mcp import server
    assert hasattr(server, 'mcp')
    assert hasattr(server, 'get_dataset_info')
    assert hasattr(server, 'get_manifest')
    assert hasattr(server, 'list_pipelines')


def test_get_dataset_info():
    """Test the get_dataset_info tool."""
    from nipoppy_mcp.server import get_dataset_info
    
    result = get_dataset_info(str(TEST_DATASET))
    
    assert "dataset_root" in result
    assert "config" in result
    assert result["config"]["DATASET_NAME"] == "example_nipoppy_dataset"


def test_get_manifest():
    """Test the get_manifest tool."""
    from nipoppy_mcp.server import get_manifest
    
    result = get_manifest(str(TEST_DATASET))
    
    assert "dataset_root" in result
    assert "content" in result
    assert "sub-001" in result["content"]


def test_list_pipelines():
    """Test the list_pipelines tool."""
    from nipoppy_mcp.server import list_pipelines
    
    result = list_pipelines(str(TEST_DATASET))
    
    assert "pipelines" in result
    assert len(result["pipelines"]) >= 2
    pipeline_names = [p["name"] for p in result["pipelines"]]
    assert "fmriprep-20.2.7" in pipeline_names
    assert "freesurfer-7.1.1" in pipeline_names


def test_get_pipeline_config():
    """Test the get_pipeline_config tool."""
    from nipoppy_mcp.server import get_pipeline_config
    
    result = get_pipeline_config("fmriprep-20.2.7", "config.json", str(TEST_DATASET))
    
    assert "config" in result
    assert result["config"]["pipeline"] == "fmriprep"
    assert result["config"]["version"] == "20.2.7"


def test_list_subjects():
    """Test the list_subjects tool."""
    from nipoppy_mcp.server import list_subjects
    
    result = list_subjects(str(TEST_DATASET), "bids")
    
    assert "subjects" in result
    assert len(result["subjects"]) >= 2
    subject_ids = [s["subject_id"] for s in result["subjects"]]
    assert "sub-001" in subject_ids
    assert "sub-002" in subject_ids


def test_get_directory_structure():
    """Test the get_directory_structure tool."""
    from nipoppy_mcp.server import get_directory_structure
    
    result = get_directory_structure(str(TEST_DATASET), max_depth=2)
    
    assert "structure" in result
    assert result["structure"]["type"] == "directory"


def test_list_files_in_directory():
    """Test the list_files_in_directory tool."""
    from nipoppy_mcp.server import list_files_in_directory
    
    result = list_files_in_directory(str(TEST_DATASET), "pipelines")
    
    assert "items" in result
    assert len(result["items"]) >= 2


def test_read_file():
    """Test the read_file tool."""
    from nipoppy_mcp.server import read_file
    
    result = read_file("global_config.json", str(TEST_DATASET))
    
    assert "content" in result
    assert result["content"]["DATASET_NAME"] == "example_nipoppy_dataset"


def test_missing_dataset():
    """Test behavior with missing dataset."""
    from nipoppy_mcp.server import get_dataset_info
    
    result = get_dataset_info("/nonexistent/path")
    
    assert "error" in result
