"""
Nipoppy MCP Server

This server exposes a simple tool through the Model Context Protocol.
"""

from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

from nipoppy.layout import DatasetLayout
from nipoppy.study import Study

# Initialize the MCP server
mcp = FastMCP("Nipoppy Dataset Server", log_level="DEBUG")


def _get_study(nipoppy_root: Path) -> Study:
    """Helper function to get a Study instance."""
    return Study(layout=DatasetLayout(nipoppy_root))


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
def list_manifest_participants_sessions(nipoppy_root: Path) -> list[tuple[str, str]]:
    """
    Get participants and sessions from the manifest.

    Note: This function uses the full manifest. To filter for imaging data only, use
    `list_manifest_imaging_participants_sessions`.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    study = _get_study(nipoppy_root)
    return list(study.manifest.get_participants_sessions())


@mcp.tool()
def list_manifest_imaging_participants_sessions(
    nipoppy_root: Path,
) -> list[tuple[str, str]]:
    """
    Get participants and sessions with imaging data from the manifest.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    study = _get_study(nipoppy_root)
    return list(study.manifest.get_imaging_subset().get_participants_sessions())


@mcp.tool()
def get_pre_reorg_participants_sessions(nipoppy_root: Path) -> list[tuple[str, str]]:
    """
    Get participants and sessions with source imaging data at the pre-reorg curation stage.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    study = _get_study(nipoppy_root)
    return list(study.curation_status_table.get_downloaded_participants_sessions())


@mcp.tool()
def get_post_reorg_participants_sessions(nipoppy_root: Path) -> list[tuple[str, str]]:
    """
    Get participants and sessions with source imaging data at the post-reorg curation stage.
    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    study = _get_study(nipoppy_root)
    return list(study.curation_status_table.get_organized_participants_sessions())


@mcp.tool()
def get_bids_participants_sessions(nipoppy_root: Path) -> list[tuple[str, str]]:
    """
    Get participants and sessions with raw BIDS imaging data.
    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    study = _get_study(nipoppy_root)
    return list(study.curation_status_table.get_bidsified_participants_sessions())


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
    return list(
        study.processing_status_table.get_completed_participants_sessions(
            pipeline_name=pipeline_name,
            pipeline_version=pipeline_version,
            pipeline_step="default",
        )
    )


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
