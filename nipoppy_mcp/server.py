"""
Nipoppy MCP Server

This server exposes Nipoppy dataset information through the Model Context Protocol.
It provides tools to query dataset configuration, manifests, pipelines, and structure.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Nipoppy Dataset Server")


def _get_dataset_root() -> Path:
    """Get the dataset root from environment variable or current directory."""
    dataset_path = os.getenv("NIPOPPY_DATASET_ROOT", os.getcwd())
    return Path(dataset_path)


def _read_json_file(file_path: Path) -> Dict[str, Any]:
    """Read and parse a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")


def _read_text_file(file_path: Path) -> str:
    """Read a text file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")


def _validate_path_within_root(root: Path, target: Path) -> bool:
    """Validate that target path is within root directory (prevent directory traversal)."""
    try:
        resolved_root = root.resolve()
        resolved_target = target.resolve()
        return resolved_target.is_relative_to(resolved_root)
    except (ValueError, OSError):
        return False


@mcp.tool()
def get_dataset_info(dataset_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Get dataset information from the global_config.json file.
    
    Args:
        dataset_root: Optional path to the Nipoppy dataset root directory.
                     If not provided, uses NIPOPPY_DATASET_ROOT env var or current directory.
    
    Returns:
        Dictionary containing the global configuration including dataset name,
        description, paths, and processing settings.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    config_path = root / "global_config.json"
    
    if not config_path.exists():
        return {
            "error": f"global_config.json not found at {config_path}",
            "dataset_root": str(root)
        }
    
    try:
        config = _read_json_file(config_path)
        return {
            "dataset_root": str(root),
            "config": config
        }
    except (ValueError, IOError, OSError) as e:
        return {
            "error": f"Failed to read configuration: {e}",
            "config_path": str(config_path)
        }


@mcp.tool()
def get_manifest(dataset_root: Optional[str] = None, max_rows: int = 100) -> Dict[str, Any]:
    """
    Get the dataset manifest (manifest.csv or manifest.tsv).
    
    Args:
        dataset_root: Optional path to the Nipoppy dataset root directory.
        max_rows: Maximum number of rows to return (default: 100).
    
    Returns:
        Dictionary with manifest content and metadata.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    
    # Try both .csv and .tsv extensions
    manifest_path = None
    for ext in ['.csv', '.tsv']:
        path = root / f"manifest{ext}"
        if path.exists():
            manifest_path = path
            break
    
    if not manifest_path:
        return {
            "error": "manifest.csv or manifest.tsv not found",
            "dataset_root": str(root)
        }
    
    try:
        content = _read_text_file(manifest_path)
        lines = content.split('\n')
        
        # Limit rows if needed
        if len(lines) > max_rows + 1:  # +1 for header
            lines = lines[:max_rows + 1]
            truncated = True
        else:
            truncated = False
        
        return {
            "dataset_root": str(root),
            "manifest_path": str(manifest_path),
            "content": '\n'.join(lines),
            "total_lines": len(content.split('\n')),
            "returned_lines": len(lines),
            "truncated": truncated
        }
    except (IOError, OSError) as e:
        return {
            "error": f"Failed to read manifest: {e}",
            "manifest_path": str(manifest_path)
        }


@mcp.tool()
def list_pipelines(dataset_root: Optional[str] = None) -> Dict[str, Any]:
    """
    List all available processing pipelines in the dataset.
    
    Args:
        dataset_root: Optional path to the Nipoppy dataset root directory.
    
    Returns:
        Dictionary with list of pipeline directories and their contents.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    pipelines_dir = root / "pipelines"
    
    if not pipelines_dir.exists():
        return {
            "error": "pipelines directory not found",
            "dataset_root": str(root)
        }
    
    pipelines = []
    try:
        for item in pipelines_dir.iterdir():
            if item.is_dir():
                # List config files in each pipeline directory
                try:
                    config_files = [f.name for f in item.iterdir() if f.is_file()]
                except (PermissionError, OSError):
                    config_files = ["<permission denied>"]
                
                pipelines.append({
                    "name": item.name,
                    "path": str(item),
                    "config_files": config_files
                })
    except (PermissionError, OSError) as e:
        return {
            "error": f"Failed to list pipelines: {e}",
            "pipelines_directory": str(pipelines_dir)
        }
    
    return {
        "dataset_root": str(root),
        "pipelines_directory": str(pipelines_dir),
        "pipelines": pipelines,
        "count": len(pipelines)
    }


@mcp.tool()
def get_pipeline_config(pipeline_name: str, config_file: str, 
                       dataset_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Get configuration for a specific pipeline.
    
    Args:
        pipeline_name: Name of the pipeline directory (e.g., 'fmriprep-20.2.7').
        config_file: Name of the configuration file to read.
        dataset_root: Optional path to the Nipoppy dataset root directory.
    
    Returns:
        Dictionary with the pipeline configuration content.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    config_path = root / "pipelines" / pipeline_name / config_file
    
    if not config_path.exists():
        return {
            "error": f"Configuration file not found: {config_path}",
            "dataset_root": str(root)
        }
    
    # Try to parse as JSON if it's a .json file
    if config_path.suffix == '.json':
        try:
            config = _read_json_file(config_path)
            return {
                "dataset_root": str(root),
                "pipeline_name": pipeline_name,
                "config_file": config_file,
                "config_path": str(config_path),
                "config": config
            }
        except (json.JSONDecodeError, IOError, OSError) as e:
            return {
                "error": f"Failed to parse JSON: {e}",
                "config_path": str(config_path)
            }
    else:
        # Return as text for non-JSON files
        try:
            content = _read_text_file(config_path)
            return {
                "dataset_root": str(root),
                "pipeline_name": pipeline_name,
                "config_file": config_file,
                "config_path": str(config_path),
                "content": content
            }
        except (IOError, OSError) as e:
            return {
                "error": f"Failed to read file: {e}",
                "config_path": str(config_path)
            }


@mcp.tool()
def list_subjects(dataset_root: Optional[str] = None, 
                 directory: str = "bids") -> Dict[str, Any]:
    """
    List subjects in the dataset from BIDS or derivatives directory.
    
    Args:
        dataset_root: Optional path to the Nipoppy dataset root directory.
        directory: Directory to list subjects from ('bids' or 'derivatives').
    
    Returns:
        Dictionary with list of subject IDs found.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    target_dir = root / directory
    
    if not target_dir.exists():
        return {
            "error": f"Directory not found: {target_dir}",
            "dataset_root": str(root)
        }
    
    # Look for subject directories (starting with 'sub-')
    subjects = []
    try:
        for item in target_dir.iterdir():
            if item.is_dir() and item.name.startswith('sub-'):
                # Get sessions if they exist
                sessions = []
                try:
                    for session in item.iterdir():
                        if session.is_dir() and session.name.startswith('ses-'):
                            sessions.append(session.name)
                except (PermissionError, OSError):
                    sessions = []
                
                subjects.append({
                    "subject_id": item.name,
                    "sessions": sessions if sessions else None
                })
    except (PermissionError, OSError) as e:
        return {
            "error": f"Failed to list subjects: {e}",
            "directory": str(target_dir)
        }
    
    return {
        "dataset_root": str(root),
        "directory": directory,
        "subjects": subjects,
        "count": len(subjects)
    }


@mcp.tool()
def get_directory_structure(dataset_root: Optional[str] = None, 
                           max_depth: int = 2) -> Dict[str, Any]:
    """
    Get the directory structure of the Nipoppy dataset.
    
    Args:
        dataset_root: Optional path to the Nipoppy dataset root directory.
        max_depth: Maximum depth to traverse (default: 2).
    
    Returns:
        Dictionary with the directory tree structure.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    
    if not root.exists():
        return {
            "error": f"Dataset root not found: {root}",
            "dataset_root": str(root)
        }
    
    def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
        """Recursively build directory tree."""
        if current_depth >= max_depth:
            return {"truncated": True}
        
        tree = {
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
        }
        
        if path.is_dir():
            children = []
            try:
                for item in sorted(path.iterdir()):
                    # Skip hidden files and common large directories
                    if item.name.startswith('.'):
                        continue
                    if item.name in ['__pycache__', 'node_modules', '.git']:
                        continue
                    
                    child = build_tree(item, current_depth + 1)
                    children.append(child)
                
                tree["children"] = children
                tree["count"] = len(children)
            except PermissionError:
                tree["error"] = "Permission denied"
        
        return tree
    
    structure = build_tree(root, 0)
    
    return {
        "dataset_root": str(root),
        "max_depth": max_depth,
        "structure": structure
    }


@mcp.tool()
def list_files_in_directory(dataset_root: Optional[str] = None,
                            subdirectory: str = "") -> Dict[str, Any]:
    """
    List files in a specific directory within the dataset.
    
    Args:
        dataset_root: Optional path to the Nipoppy dataset root directory.
        subdirectory: Subdirectory path relative to dataset root (e.g., 'pipelines/fmriprep-20.2.7').
    
    Returns:
        Dictionary with list of files and directories.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    target_dir = root / subdirectory if subdirectory else root
    
    # Validate path to prevent directory traversal
    if not _validate_path_within_root(root, target_dir):
        return {
            "error": "Invalid path: directory traversal not allowed",
            "dataset_root": str(root),
            "subdirectory": subdirectory
        }
    
    if not target_dir.exists():
        return {
            "error": f"Directory not found: {target_dir}",
            "dataset_root": str(root),
            "subdirectory": subdirectory
        }
    
    items = []
    try:
        for item in target_dir.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item.relative_to(root))
            })
    except (PermissionError, OSError) as e:
        return {
            "error": f"Failed to list directory: {e}",
            "directory": str(target_dir)
        }
    
    return {
        "dataset_root": str(root),
        "directory": str(target_dir),
        "subdirectory": subdirectory,
        "items": sorted(items, key=lambda x: (x["type"], x["name"])),
        "count": len(items)
    }


@mcp.tool()
def read_file(file_path: str, dataset_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Read any file within the dataset.
    
    Args:
        file_path: Path to file relative to dataset root (e.g., 'global_config.json').
        dataset_root: Optional path to the Nipoppy dataset root directory.
    
    Returns:
        Dictionary with file content.
    """
    root = Path(dataset_root) if dataset_root else _get_dataset_root()
    full_path = root / file_path
    
    # Validate path to prevent directory traversal
    if not _validate_path_within_root(root, full_path):
        return {
            "error": "Invalid path: directory traversal not allowed",
            "dataset_root": str(root),
            "file_path": file_path
        }
    
    if not full_path.exists():
        return {
            "error": f"File not found: {full_path}",
            "dataset_root": str(root),
            "file_path": file_path
        }
    
    if not full_path.is_file():
        return {
            "error": f"Path is not a file: {full_path}",
            "dataset_root": str(root),
            "file_path": file_path
        }
    
    # Try to parse as JSON if it's a .json file
    if full_path.suffix == '.json':
        try:
            content = _read_json_file(full_path)
            return {
                "dataset_root": str(root),
                "file_path": file_path,
                "full_path": str(full_path),
                "type": "json",
                "content": content
            }
        except (json.JSONDecodeError, IOError, OSError) as e:
            return {
                "error": f"Failed to parse JSON: {e}",
                "full_path": str(full_path)
            }
    else:
        # Return as text for non-JSON files
        try:
            content = _read_text_file(full_path)
            return {
                "dataset_root": str(root),
                "file_path": file_path,
                "full_path": str(full_path),
                "type": "text",
                "content": content
            }
        except (IOError, OSError, UnicodeDecodeError) as e:
            return {
                "error": f"Failed to read file: {e}",
                "full_path": str(full_path)
            }


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
