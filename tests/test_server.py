"""Tests for the Nipoppy MCP Server."""

import os
from pathlib import Path

import tempfile


def test_import_server():
    """Test that the server module can be imported."""
    from nipoppy_mcp import server

    assert hasattr(server, "mcp")
    assert hasattr(server, "list_files")


def test_list_files_basic():
    """Test the list_files tool with a basic directory."""
    from nipoppy_mcp.server import list_files

    # Create a temporary directory with some files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        test_file1 = Path(tmpdir) / "test1.txt"
        test_file2 = Path(tmpdir) / "test2.json"
        test_file1.write_text("test content 1")
        test_file2.write_text('{"test": "content"}')

        # Also create a subdirectory (should not be included)
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()

        result = list_files(tmpdir)

        # Should only return files, not directories
        assert "test1.txt" in result
        assert "test2.json" in result
        assert "subdir" not in result
        assert len(result) == 2


def test_list_files_nonexistent_directory():
    """Test list_files with a non-existent directory."""
    from nipoppy_mcp.server import list_files

    result = list_files("/nonexistent/path/to/directory")

    assert len(result) == 1
    assert "Error: Directory not found" in result[0]


def test_list_files_not_a_directory():
    """Test list_files with a path that is not a directory."""
    from nipoppy_mcp.server import list_files

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        tmpfile.write(b"test content")
        tmpfile_path = tmpfile.name

    try:
        result = list_files(tmpfile_path)

        assert len(result) == 1
        assert "Error: Path is not a directory" in result[0]
    finally:
        os.unlink(tmpfile_path)


def test_list_files_empty_directory():
    """Test list_files with an empty directory."""
    from nipoppy_mcp.server import list_files

    with tempfile.TemporaryDirectory() as tmpdir:
        result = list_files(tmpdir)

        assert result == []
