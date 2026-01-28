"""
Nipoppy MCP Server

This server exposes a simple tool through the Model Context Protocol.
"""

from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Nipoppy Dataset Server", log_level="DEBUG")


@mcp.tool()
def get_installed_pipelines(nipoppy_root: Path) -> dict[str, dict[str, list[str]]]:
    """
    Get installed Nipoppy pipelines.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A dictionary mapping pipeline types to pipeline names and their versions.
    """

    from nipoppy.workflows.pipeline_store.list import PipelineListWorkflow

    workflow = PipelineListWorkflow(dpath_root=nipoppy_root)
    pipeline_info_map = {
        k.value: v for k, v in workflow._get_pipeline_info_map().items()
    }

    return pipeline_info_map


@mcp.tool()
def list_processed_participants_sessions(
    nipoppy_root: Path, pipeline_name: str, pipeline_version: str
) -> list[tuple[str, str]]:
    """
    Get completed participants and sessions for a given processing pipeline.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        pipeline_name: Name of the pipeline.
        pipeline_version: Version of the pipeline.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    from nipoppy.study import Study
    from nipoppy.layout import DatasetLayout

    study = Study(layout=DatasetLayout(nipoppy_root))
    return [
        tuple(participant_status)
        for participant_status in study.processing_status_table.get_completed_participants_sessions(
            pipeline_name=pipeline_name,
            pipeline_version=pipeline_version,
            pipeline_step="default",
        )
    ]


@mcp.tool()
def list_files(directory_path: str) -> List[str]:
    """
    List files in a directory.

    Args:
        directory_path: Path to the directory to list files from.

    Returns:
        List of file names in the directory.
    """
    path = Path(directory_path)

    if not path.exists():
        return [f"Error: Directory not found: {directory_path}"]

    if not path.is_dir():
        return [f"Error: Path is not a directory: {directory_path}"]

    try:
        files = [item.name for item in path.iterdir() if item.is_file()]
        return files
    except (PermissionError, OSError) as e:
        return [f"Error: Failed to list directory: {e}"]


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
