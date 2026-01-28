"""Tests for the Nipoppy MCP Server."""


def test_import_server():
    """Test that the server module can be imported."""
    from nipoppy_mcp import server

    assert hasattr(server, "mcp")
