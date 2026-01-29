"""
Nipoppy MCP Server

This server exposes a simple tool through the Model Context Protocol.
"""

import json

import pandas as pd
from mcp.server.fastmcp import FastMCP
from nipoppy.env import PipelineTypeEnum
from nipoppy.layout import DatasetLayout
from nipoppy.study import Study
from nipoppy.config.pipeline import (
    BasePipelineConfig,
    BIDSificationPipelineConfig,
    ExtractionPipelineConfig,
    ProcessingPipelineConfig,
)
from nipoppy.workflows.pipeline_store.list import PipelineListWorkflow


# Initialize the MCP server
mcp = FastMCP("Nipoppy Dataset Server", log_level="DEBUG")

PIPELINE_TYPE_TO_CONFIG_CLASS = {
    PipelineTypeEnum.BIDSIFICATION: BIDSificationPipelineConfig,
    PipelineTypeEnum.PROCESSING: ProcessingPipelineConfig,
    PipelineTypeEnum.EXTRACTION: ExtractionPipelineConfig,
}


def _get_study(nipoppy_root: str) -> Study:
    """Helper function to get a Study instance."""
    return Study(layout=DatasetLayout(nipoppy_root))


def _get_installed_pipelines(nipoppy_root: str) -> list[tuple[str, str, str]]:
    """
    Get installed Nipoppy pipelines (type, name, version).
    """

    workflow = PipelineListWorkflow(dpath_root=nipoppy_root)
    pipeline_info_list = []
    pipeline_info_map = workflow._get_pipeline_info_map()
    for pipeline_type in pipeline_info_map:
        for pipeline_name in pipeline_info_map[pipeline_type]:
            for pipeline_version in pipeline_info_map[pipeline_type][pipeline_name]:
                pipeline_info_list.append(
                    (pipeline_type.value, pipeline_name, pipeline_version)
                )
    return pipeline_info_list


def _get_pipeline_config(
    nipoppy_root: str, pipeline_type: str, pipeline_name: str, pipeline_version: str
) -> BasePipelineConfig:
    """Helper function to get a pipeline configuration."""
    study = _get_study(nipoppy_root)
    pipeline_config_class = PIPELINE_TYPE_TO_CONFIG_CLASS[pipeline_type]
    pipeline_config_path = (
        study.layout.get_dpath_pipeline_bundle(
            pipeline_type, pipeline_name, pipeline_version
        )
        / study.layout.fname_pipeline_config
    )
    return pipeline_config_class(**json.loads(pipeline_config_path.read_text()))


def _get_pipeline_steps(
    nipoppy_root: str, pipeline_type: str, pipeline_name: str, pipeline_version: str
) -> list[str]:
    """Helper function to get the steps defined in a pipeline configuration."""
    pipeline_config = _get_pipeline_config(
        nipoppy_root, pipeline_type, pipeline_name, pipeline_version
    )
    return [step.NAME for step in pipeline_config.STEPS]


@mcp.tool()
def get_dataset_info(nipoppy_root: str) -> dict:
    """
    Get basic information about the Nipoppy dataset.

    When using a tool, if a pipeline's version is not specified, the latest version
    should be used. If a pipeline's step is not specified, the first step should be used.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A dictionary containing dataset information:
            - n_participants: Number of participants in the dataset.
            - n_sessions: Number of sessions in the dataset.
            - installed_pipelines: A dictionary mapping pipeline (pipeline type, pipeline name, pipeline version) to their defined steps.
    """
    df_participants_sessions = pd.DataFrame(
        (list_manifest_participants_sessions(nipoppy_root))
    )
    installed_pipelines = {
        pipeline_info: _get_pipeline_steps(nipoppy_root, *pipeline_info)
        for pipeline_info in _get_installed_pipelines(nipoppy_root)
    }

    info = {
        "n_participants": len(df_participants_sessions["participant_id"].unique()),
        "n_sessions": len(df_participants_sessions["session_id"].unique()),
        "installed_pipelines": installed_pipelines,
    }
    return info


@mcp.tool()
def list_manifest_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
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
    nipoppy_root: str,
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
def get_pre_reorg_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
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
def get_post_reorg_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
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
def get_bids_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
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
    nipoppy_root: str, pipeline_name: str, pipeline_version: str, pipeline_step: str
) -> list[tuple[str, str]]:
    """
    Get completed participants and sessions for a given processing pipeline.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        pipeline_name: Name of the pipeline.
        pipeline_version: Version of the pipeline.
        pipeline_step: Step of the pipeline.
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
            pipeline_step=pipeline_step,
        )
    )


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
