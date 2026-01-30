"""
Nipoppy MCP Server

This server exposes tools and resources for interacting with Nipoppy datasets through the Model Context Protocol.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for dataset root - needed for resources
_current_dataset_root = os.environ.get("NIPOPPY_DATASET_ROOT", "")

PIPELINE_TYPE_TO_CONFIG_CLASS = {
    PipelineTypeEnum.BIDSIFICATION: BIDSificationPipelineConfig,
    PipelineTypeEnum.PROCESSING: ProcessingPipelineConfig,
    PipelineTypeEnum.EXTRACTION: ExtractionPipelineConfig,
}

# Valid data stages for filtering
VALID_DATA_STAGES = ["all", "imaging", "downloaded", "organized", "bidsified", "processed"]

# Valid path types for navigation
VALID_PATH_TYPES = [
    "pipeline_output", "config", "directory", "pipeline_work", 
    "pipeline_idp", "bids_db", "dataset_root"
]


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


# Enhanced helper functions for MCP resources and refactored tools

def _read_config_file(file_path: Path) -> Dict[str, Any]:
    """
    Safely read a JSON configuration file with strict validation.
    
    Args:
        file_path: Path to the JSON configuration file.
        
    Returns:
        Dictionary containing the parsed JSON data.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Required configuration file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in configuration file {file_path}: {str(e)}", 
                                 e.doc, e.pos)


def _read_tsv_file(file_path: Path) -> str:
    """
    Safely read a TSV file with strict validation.
    
    Args:
        file_path: Path to the TSV file.
        
    Returns:
        String containing the TSV content.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Required TSV file not found: {file_path}")
    
    return file_path.read_text(encoding='utf-8')


def _validate_pipeline_exists(
    nipoppy_root: str, pipeline_name: str, pipeline_version: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Validate that a pipeline exists and return the latest version if not specified.
    
    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        pipeline_name: Name of the pipeline to validate.
        pipeline_version: Optional version of the pipeline. If None, uses latest.
        
    Returns:
        Tuple of (pipeline_type, resolved_version).
        
    Raises:
        ValueError: If the pipeline doesn't exist or version is invalid.
    """
    installed_pipelines = _get_installed_pipelines(nipoppy_root)
    
    # Find all versions of this pipeline
    pipeline_versions = []
    pipeline_type = None
    
    for p_type, p_name, p_version in installed_pipelines:
        if p_name == pipeline_name:
            pipeline_type = p_type
            pipeline_versions.append(p_version)
    
    if not pipeline_versions:
        raise ValueError(f"Pipeline '{pipeline_name}' not found in dataset")
    
    if pipeline_version:
        if pipeline_version not in pipeline_versions:
            raise ValueError(f"Pipeline '{pipeline_name}' version '{pipeline_version}' not found. "
                           f"Available versions: {sorted(pipeline_versions)}")
        resolved_version = pipeline_version
    else:
        # Get latest version (sort by semantic version if possible)
        resolved_version = sorted(pipeline_versions)[-1]
        logger.info(f"Using latest version {resolved_version} for pipeline '{pipeline_name}'")
    
    return pipeline_type, resolved_version


def _format_participant_sessions(
    participants_sessions: List[Tuple[str, str]]
) -> List[Tuple[str, str]]:
    """
    Format participant-session tuples consistently.
    
    Args:
        participants_sessions: List of (participant_id, session_id) tuples.
        
    Returns:
        Sorted list of unique participant-session tuples.
    """
    # Remove duplicates and sort
    unique_pairs = list(set(participants_sessions))
    return sorted(unique_pairs)


def _get_pipeline_status_summary(
    nipoppy_root: str, pipeline_name: str
) -> Dict[str, Dict[str, Any]]:
    """
    Get a summary of pipeline completion status across all versions and steps.
    
    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        pipeline_name: Name of the pipeline.
        
    Returns:
        Dictionary containing status summary per version and step.
    """
    study = _get_study(nipoppy_root)
    status_summary = {}
    
    installed_pipelines = _get_installed_pipelines(nipoppy_root)
    
    for p_type, p_name, p_version in installed_pipelines:
        if p_name == pipeline_name:
            pipeline_config = _get_pipeline_config(nipoppy_root, p_type, p_name, p_version)
            steps = _get_pipeline_steps(nipoppy_root, p_type, p_name, p_version)
            
            status_summary[p_version] = {}
            for step in steps:
                completed_sessions = list(
                    study.processing_status_table.get_completed_participants_sessions(
                        pipeline_name=p_name,
                        pipeline_version=p_version,
                        pipeline_step=step,
                    )
                )
                status_summary[p_version][step] = {
                    "completed_count": len(completed_sessions),
                    "completed_participants": list(set([ps[0] for ps in completed_sessions])),
                    "completed_sessions": list(set([ps[1] for ps in completed_sessions])),
                }
    
    return status_summary


# ============================================================================
# MCP RESOURCES - Context information automatically available to agents
# ============================================================================

@mcp.resource("nipoppy://config")
def get_dataset_config() -> Dict[str, Any]:
    """
    Get global dataset configuration and metadata.
    
    Provides the main configuration file containing dataset metadata, 
    pipeline definitions, and global settings.
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Returns:
        Dictionary containing the dataset configuration.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set.
        FileNotFoundError: If config.json doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    study = _get_study(_current_dataset_root)
    config_path = study.layout.fpath_global_config
    
    config = _read_config_file(config_path)
    
    # Add computed metadata
    config["dataset_root"] = _current_dataset_root
    config["installed_pipelines"] = [
        {"type": p_type, "name": p_name, "version": p_version}
        for p_type, p_name, p_version in _get_installed_pipelines(_current_dataset_root)
    ]
    
    return config


@mcp.resource("nipoppy://manifest") 
def get_dataset_manifest() -> str:
    """
    Get dataset structure manifest (participants/sessions/datatypes).
    
    The manifest is the ground truth file listing all expected participants,
    sessions, and data types in the dataset.
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Returns:
        TSV string containing the manifest data.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set.
        FileNotFoundError: If manifest.tsv doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    study = _get_study(_current_dataset_root)
    manifest_path = study.layout.fpath_manifest
    
    return _read_tsv_file(manifest_path)


@mcp.resource("nipoppy://status/curation")
def get_curation_status() -> str:
    """
    Get data availability at different curation stages.
    
    Shows what data exists at each curation stage: downloaded (pre-reorg),
    organized (post-reorg), and bidsified (BIDS conversion).
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Returns:
        TSV string containing the curation status data.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set.
        FileNotFoundError: If curation_status.tsv doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    study = _get_study(_current_dataset_root)
    curation_status_path = study.layout.fpath_curation_status
    
    return _read_tsv_file(curation_status_path)


@mcp.resource("nipoppy://status/processing") 
def get_processing_status() -> str:
    """
    Get pipeline completion status across participants/sessions.
    
    Shows which processing pipelines have completed successfully for each
    participant and session combination.
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Returns:
        TSV string containing the processing status data.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set.
        FileNotFoundError: If processing_status.tsv doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    study = _get_study(_current_dataset_root)
    processing_status_path = study.layout.fpath_processing_status
    
    return _read_tsv_file(processing_status_path)


@mcp.resource("nipoppy://pipelines/{pipeline_name}/{version}/config")
def get_pipeline_config(pipeline_name: str, version: str) -> Dict[str, Any]:
    """
    Get individual pipeline configuration (steps, containers, parameters).
    
    Provides detailed configuration for a specific pipeline version including
    defined steps, container specifications, and processing parameters.
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Args:
        pipeline_name: Name of the pipeline.
        version: Version of the pipeline.
        
    Returns:
        Dictionary containing the pipeline configuration.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set or pipeline doesn't exist.
        FileNotFoundError: If pipeline config doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    pipeline_type, resolved_version = _validate_pipeline_exists(
        _current_dataset_root, pipeline_name, version
    )
    
    study = _get_study(_current_dataset_root)
    pipeline_config_path = (
        study.layout.get_dpath_pipeline_bundle(pipeline_type, pipeline_name, resolved_version)
        / study.layout.fname_pipeline_config
    )
    
    config = _read_config_file(pipeline_config_path)
    
    # Add computed metadata
    config["pipeline_type"] = pipeline_type
    config["pipeline_name"] = pipeline_name
    config["pipeline_version"] = resolved_version
    config["steps"] = _get_pipeline_steps(_current_dataset_root, pipeline_type, pipeline_name, resolved_version)
    
    return config


@mcp.resource("nipoppy://pipelines/{pipeline_name}/{version}/descriptor") 
def get_pipeline_descriptor(pipeline_name: str, version: str) -> Dict[str, Any]:
    """
    Get Boutiques pipeline descriptor (tool specifications).
    
    Provides the detailed tool specification following the Boutiques format,
    including input/output definitions and command-line interface specifications.
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Args:
        pipeline_name: Name of the pipeline.
        version: Version of the pipeline.
        
    Returns:
        Dictionary containing the pipeline descriptor.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set or pipeline doesn't exist.
        FileNotFoundError: If pipeline descriptor doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    pipeline_type, resolved_version = _validate_pipeline_exists(
        _current_dataset_root, pipeline_name, version
    )
    
    study = _get_study(_current_dataset_root)
    pipeline_descriptor_path = (
        study.layout.get_dpath_pipeline_bundle(pipeline_type, pipeline_name, resolved_version)
        / study.layout.fname_pipeline_json
    )
    
    descriptor = _read_config_file(pipeline_descriptor_path)
    
    # Add computed metadata
    descriptor["pipeline_type"] = pipeline_type
    descriptor["pipeline_name"] = pipeline_name
    descriptor["pipeline_version"] = resolved_version
    
    return descriptor


@mcp.resource("nipoppy://demographics")
def get_demographics() -> str:
    """
    Get de-identified participant demographic information.
    
    Provides basic demographic information for dataset participants.
    This data is typically de-identified and safe for analysis context.
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Returns:
        TSV string containing demographic data.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set.
        FileNotFoundError: If demographics.tsv doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    study = _get_study(_current_dataset_root)
    demographics_path = study.layout.dpath_tabular / "demographics.tsv"
    
    return _read_tsv_file(demographics_path)


@mcp.resource("nipoppy://bids/description")
def get_bids_description() -> Dict[str, Any]:
    """
    Get BIDS dataset description and metadata.
    
    Provides the BIDS-compliant dataset description with metadata about
    the dataset structure and compliance.
    
    Note: Requires NIPOPPY_DATASET_ROOT environment variable to be set.
    
    Returns:
        Dictionary containing the BIDS dataset description.
        
    Raises:
        ValueError: If NIPOPPY_DATASET_ROOT environment variable is not set.
        FileNotFoundError: If dataset_description.json doesn't exist.
    """
    if not _current_dataset_root:
        raise ValueError("NIPOPPY_DATASET_ROOT environment variable must be set to access dataset resources")
    
    study = _get_study(_current_dataset_root)
    bids_description_path = study.layout.dpath_bids / "dataset_description.json"
    
    description = _read_config_file(bids_description_path)
    
    # Add computed metadata
    description["dataset_root"] = _current_dataset_root
    description["bids_dir"] = str(study.layout.dpath_bids)
    
    return description


# ============================================================================
# MCP TOOLS - Refactored and unified functionality
# ============================================================================

@mcp.tool()
def get_dataset_info(
    nipoppy_root: str,
    include_pipeline_details: bool = True,
    include_status_summary: bool = True
) -> Dict[str, Any]:
    """
    Get enhanced dataset overview with configurable detail levels.

    When using a tool, if a pipeline's version is not specified, the latest version
    should be used. If a pipeline's step is not specified, the first step should be used.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        include_pipeline_details: Include detailed pipeline information.
        include_status_summary: Include curation and processing status summaries.

    Returns:
        A dictionary containing comprehensive dataset information:
            - n_participants: Number of participants in the dataset.
            - n_sessions: Number of sessions in the dataset.
            - installed_pipelines: Pipeline information (if include_pipeline_details=True).
            - status_summary: Data availability at various stages (if include_status_summary=True).
            - dataset_root: Path to the dataset.
            - dataset_layout: Key directory paths.
    """
    study = _get_study(nipoppy_root)
    
    # Basic counts from manifest
    df_participants_sessions = pd.DataFrame(
        (list_manifest_participants_sessions(nipoppy_root))
    )
    
    info = {
        "n_participants": len(df_participants_sessions["participant_id"].unique()),
        "n_sessions": len(df_participants_sessions["session_id"].unique()),
        "dataset_root": nipoppy_root,
    }
    
    # Dataset layout information
    info["dataset_layout"] = {
        "bids_dir": str(study.layout.dpath_bids),
        "derivatives_dir": str(study.layout.dpath_derivatives),
        "sourcedata_dir": str(study.layout.dpath_sourcedata),
        "tabular_dir": str(study.layout.dpath_tabular),
    }
    
    # Pipeline details
    if include_pipeline_details:
        installed_pipelines = {}
        for pipeline_info in _get_installed_pipelines(nipoppy_root):
            pipeline_type, pipeline_name, pipeline_version = pipeline_info
            
            try:
                config_path = (
                    study.layout.get_dpath_pipeline_bundle(pipeline_type, pipeline_name, pipeline_version)
                    / study.layout.fname_pipeline_config
                )
                output_path = study.layout.get_dpath_pipeline_output(pipeline_name, pipeline_version)
                
                # Get status summary for this pipeline
                status = _get_pipeline_status_summary(nipoppy_root, pipeline_name)
                
                installed_pipelines[pipeline_info] = {
                    "steps": _get_pipeline_steps(nipoppy_root, *pipeline_info),
                    "config_path": str(config_path),
                    "output_path": str(output_path),
                    "status_summary": status.get(pipeline_version, {}),
                }
            except Exception as e:
                logger.warning(f"Could not get details for pipeline {pipeline_info}: {str(e)}")
                installed_pipelines[pipeline_info] = {
                    "steps": [],
                    "config_path": None,
                    "output_path": None,
                    "status_summary": {},
                }
        
        info["installed_pipelines"] = installed_pipelines
    
    # Status summary
    if include_status_summary:
        info["status_summary"] = {}
        
        try:
            # Curation status
            downloaded = get_pre_reorg_participants_sessions(nipoppy_root)
            organized = get_post_reorg_participants_sessions(nipoppy_root)
            bidsified = get_bids_participants_sessions(nipoppy_root)
            imaging = list_manifest_imaging_participants_sessions(nipoppy_root)
            manifest = list_manifest_participants_sessions(nipoppy_root)
            
            info["status_summary"]["manifest"] = {
                "count": len(manifest),
                "participants": list(set([ps[0] for ps in manifest])),
                "sessions": list(set([ps[1] for ps in manifest])),
            }
            info["status_summary"]["imaging"] = {
                "count": len(imaging),
                "participants": list(set([ps[0] for ps in imaging])),
                "sessions": list(set([ps[1] for ps in imaging])),
            }
            info["status_summary"]["downloaded"] = {
                "count": len(downloaded),
                "participants": list(set([ps[0] for ps in downloaded])),
                "sessions": list(set([ps[1] for ps in downloaded])),
            }
            info["status_summary"]["organized"] = {
                "count": len(organized),
                "participants": list(set([ps[0] for ps in organized])),
                "sessions": list(set([ps[1] for ps in organized])),
            }
            info["status_summary"]["bidsified"] = {
                "count": len(bidsified),
                "participants": list(set([ps[0] for ps in bidsified])),
                "sessions": list(set([ps[1] for ps in bidsified])),
            }
            
        except Exception as e:
            logger.warning(f"Could not generate status summary: {str(e)}")
            info["status_summary"] = {"error": str(e)}
    
    return info


@mcp.tool()
def get_participants_sessions(
    nipoppy_root: str,
    data_stage: str = "all",  # all, imaging, downloaded, organized, bidsified, processed
    pipeline_name: Optional[str] = None,
    pipeline_version: Optional[str] = None,  
    pipeline_step: Optional[str] = None
) -> List[Tuple[str, str]]:
    """
    Unified participant/session query with filtering by data stage.

    This is the primary tool for querying participants and sessions in the dataset.
    It replaces multiple specialized tools with a unified interface.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        data_stage: Data stage to filter by. Options:
            - "all": All participants/sessions from manifest
            - "imaging": Only participants/sessions with imaging data
            - "downloaded": Pre-reorg (downloaded) data
            - "organized": Post-reorg (organized) data  
            - "bidsified": BIDS-converted data
            - "processed": Processed data (requires pipeline parameters)
        pipeline_name: Name of the pipeline (required for "processed" stage).
        pipeline_version: Version of the pipeline (optional, uses latest if not specified).
        pipeline_step: Step of the pipeline (optional, uses first if not specified).

    Returns:
        A list of tuples containing participant IDs and session IDs.

    Raises:
        ValueError: If data_stage is invalid or pipeline parameters are insufficient.
    """
    if data_stage not in VALID_DATA_STAGES:
        raise ValueError(f"Invalid data_stage '{data_stage}'. Valid options: {VALID_DATA_STAGES}")
    
    participants_sessions = []
    
    if data_stage == "all":
        participants_sessions = list_manifest_participants_sessions(nipoppy_root)
    elif data_stage == "imaging":
        participants_sessions = list_manifest_imaging_participants_sessions(nipoppy_root)
    elif data_stage == "downloaded":
        participants_sessions = get_pre_reorg_participants_sessions(nipoppy_root)
    elif data_stage == "organized":
        participants_sessions = get_post_reorg_participants_sessions(nipoppy_root)
    elif data_stage == "bidsified":
        participants_sessions = get_bids_participants_sessions(nipoppy_root)
    elif data_stage == "processed":
        if not pipeline_name:
            raise ValueError("pipeline_name is required for 'processed' data stage")
        
        # Auto-resolve pipeline version if not specified
        pipeline_type, resolved_version = _validate_pipeline_exists(
            nipoppy_root, pipeline_name, pipeline_version
        )
        
        # Auto-resolve pipeline step if not specified
        if not pipeline_step:
            pipeline_step = _get_pipeline_steps(
                nipoppy_root, pipeline_type, pipeline_name, resolved_version
            )[0]
            logger.info(f"Using first pipeline step '{pipeline_step}' for pipeline '{pipeline_name}'")
        
        participants_sessions = list_processed_participants_sessions(
            nipoppy_root, pipeline_name, resolved_version, pipeline_step
        )
    
    # Format and return
    return _format_participant_sessions(participants_sessions)


# ============================================================================
# LEGACY TOOLS - Deprecated but maintained for backward compatibility
# ============================================================================

@mcp.tool()
def list_manifest_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
    """
    [DEPRECATED] Get participants and sessions from the manifest.

    DEPRECATED: Use get_participants_sessions(data_stage="all") instead.
    This tool is maintained for backward compatibility but will be removed in a future version.

    Note: This function uses the full manifest. To filter for imaging data only, use
    `list_manifest_imaging_participants_sessions`.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    import warnings
    warnings.warn(
        "list_manifest_participants_sessions is deprecated. Use get_participants_sessions(data_stage='all') instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    study = _get_study(nipoppy_root)
    return list(study.manifest.get_participants_sessions())


@mcp.tool()
def list_manifest_imaging_participants_sessions(
    nipoppy_root: str,
) -> list[tuple[str, str]]:
    """
    [DEPRECATED] Get participants and sessions with imaging data from the manifest.

    DEPRECATED: Use get_participants_sessions(data_stage="imaging") instead.
    This tool is maintained for backward compatibility but will be removed in a future version.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    import warnings
    warnings.warn(
        "list_manifest_imaging_participants_sessions is deprecated. Use get_participants_sessions(data_stage='imaging') instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    study = _get_study(nipoppy_root)
    return list(study.manifest.get_imaging_subset().get_participants_sessions())


@mcp.tool()
def get_pre_reorg_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
    """
    [DEPRECATED] Get participants and sessions with source imaging data at the pre-reorg curation stage.

    DEPRECATED: Use get_participants_sessions(data_stage="downloaded") instead.
    This tool is maintained for backward compatibility but will be removed in a future version.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    import warnings
    warnings.warn(
        "get_pre_reorg_participants_sessions is deprecated. Use get_participants_sessions(data_stage='downloaded') instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    study = _get_study(nipoppy_root)
    return list(study.curation_status_table.get_downloaded_participants_sessions())


@mcp.tool()
def get_post_reorg_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
    """
    [DEPRECATED] Get participants and sessions with source imaging data at the post-reorg curation stage.

    DEPRECATED: Use get_participants_sessions(data_stage="organized") instead.
    This tool is maintained for backward compatibility but will be removed in a future version.
    
    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    import warnings
    warnings.warn(
        "get_post_reorg_participants_sessions is deprecated. Use get_participants_sessions(data_stage='organized') instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    study = _get_study(nipoppy_root)
    return list(study.curation_status_table.get_organized_participants_sessions())


@mcp.tool()
def get_bids_participants_sessions(nipoppy_root: str) -> list[tuple[str, str]]:
    """
    [DEPRECATED] Get participants and sessions with raw BIDS imaging data.

    DEPRECATED: Use get_participants_sessions(data_stage="bidsified") instead.
    This tool is maintained for backward compatibility but will be removed in a future version.
    
    Args:
        nipoppy_root: Path to the Nipoppy dataset root.

    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    import warnings
    warnings.warn(
        "get_bids_participants_sessions is deprecated. Use get_participants_sessions(data_stage='bidsified') instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    study = _get_study(nipoppy_root)
    return list(study.curation_status_table.get_bidsified_participants_sessions())


@mcp.tool()
def list_processed_participants_sessions(
    nipoppy_root: str, pipeline_name: str, pipeline_version: str, pipeline_step: str
) -> list[tuple[str, str]]:
    """
    [DEPRECATED] Get completed participants and sessions for a given processing pipeline.

    DEPRECATED: Use get_participants_sessions(data_stage="processed", pipeline_name=..., ...) instead.
    This tool is maintained for backward compatibility but will be removed in a future version.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        pipeline_name: Name of the pipeline.
        pipeline_version: Version of the pipeline.
        pipeline_step: Step of the pipeline.
    Returns:
        A list of tuples containing participant IDs and session IDs.
    """
    import warnings
    warnings.warn(
        "list_processed_participants_sessions is deprecated. Use get_participants_sessions(data_stage='processed', pipeline_name=..., ...) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
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


@mcp.tool()
def navigate_dataset(
    nipoppy_root: str,
    path_type: str,  # pipeline_output, config, directory, etc.
    target: Optional[str] = None,
    pipeline_name: Optional[str] = None,
    pipeline_version: Optional[str] = None
) -> Union[Dict[str, Any], str]:
    """
    File path and configuration access with smart path resolution.

    Provides navigation to various dataset directories and files, with smart
    resolution of pipeline paths and automatic version handling.

    Args:
        nipoppy_root: Path to the Nipoppy dataset root.
        path_type: Type of path to navigate to. Options:
            - "dataset_root": Root directory of the dataset
            - "config": Global configuration directory
            - "directory": Specific dataset directory (requires target)
            - "pipeline_output": Pipeline output directory
            - "pipeline_work": Pipeline work directory for specific participant
            - "pipeline_idp": Pipeline IDP directory
            - "bids_db": PyBIDS database directory
        target: Target directory name (required for "directory" path_type).
        pipeline_name: Name of the pipeline (required for pipeline path types).
        pipeline_version: Version of the pipeline (optional, uses latest if not specified).

    Returns:
        Either a dictionary (for complex structures) or string (for simple paths).

    Raises:
        ValueError: If path_type is invalid or required parameters are missing.
    """
    if path_type not in VALID_PATH_TYPES:
        raise ValueError(f"Invalid path_type '{path_type}'. Valid options: {VALID_PATH_TYPES}")
    
    study = _get_study(nipoppy_root)
    layout = study.layout
    
    # Simple directory paths
    if path_type == "dataset_root":
        return {"path": nipoppy_root, "type": "directory"}
    
    if path_type == "config":
        config_dir = layout.dpath_config
        return {"path": str(config_dir), "type": "directory", "contents": {
            "global_config": str(layout.fpath_global_config),
            "manifest": str(layout.fpath_manifest),
            "tabular_data": str(layout.dpath_tabular),
        }}
    
    if path_type == "directory":
        if not target:
            raise ValueError("target is required for 'directory' path_type")
        
        dir_map = {
            "bids": layout.dpath_bids,
            "derivatives": layout.dpath_derivatives,
            "sourcedata": layout.dpath_sourcedata,
            "tabular": layout.dpath_tabular,
            "scratch": layout.dpath_scratch,
            "tmp": layout.dpath_tmp,
            "logs": layout.dpath_logs,
        }
        
        if target not in dir_map:
            raise ValueError(f"Invalid target directory '{target}'. Valid options: {list(dir_map.keys())}")
        
        return {"path": str(dir_map[target]), "type": "directory"}
    
    # Pipeline-related paths
    if path_type in ["pipeline_output", "pipeline_work", "pipeline_idp", "bids_db"]:
        if not pipeline_name:
            raise ValueError(f"pipeline_name is required for '{path_type}' path_type")
        
        # Auto-resolve pipeline version if not specified
        pipeline_type, resolved_version = _validate_pipeline_exists(
            nipoppy_root, pipeline_name, pipeline_version
        )
        
        if path_type == "pipeline_output":
            output_path = layout.get_dpath_pipeline_output(pipeline_name, resolved_version)
            return {"path": str(output_path), "type": "directory", "pipeline_info": {
                "name": pipeline_name,
                "version": resolved_version,
                "type": pipeline_type,
            }}
        
        elif path_type == "pipeline_work":
            if not target:
                raise ValueError("target (participant_id) is required for 'pipeline_work' path_type")
            work_path = layout.get_dpath_pipeline_work(
                pipeline_name, resolved_version, target, "01"
            )
            return {"path": str(work_path), "type": "directory", "pipeline_info": {
                "name": pipeline_name,
                "version": resolved_version,
                "type": pipeline_type,
                "participant_id": target,
            }}
        
        elif path_type == "pipeline_idp":
            idp_path = layout.get_dpath_pipeline_idp(pipeline_name, resolved_version)
            return {"path": str(idp_path), "type": "directory", "pipeline_info": {
                "name": pipeline_name,
                "version": resolved_version,
                "type": pipeline_type,
            }}
        
        elif path_type == "bids_db":
            if not target:
                raise ValueError("target (participant_id) is required for 'bids_db' path_type")
            bids_db_path = layout.get_dpath_pybids_db(pipeline_name, resolved_version, target, "01")
            return {"path": str(bids_db_path), "type": "directory", "pipeline_info": {
                "name": pipeline_name,
                "version": resolved_version,
                "type": pipeline_type,
                "participant_id": target,
            }}


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
