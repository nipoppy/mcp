#!/usr/bin/env python
"""
Example script demonstrating how to use the Nipoppy MCP Server tools directly.

This shows what an MCP client (like Claude Desktop) would do when calling these tools.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from nipoppy_mcp.server import (
    get_dataset_info,
    get_manifest,
    list_pipelines,
    get_pipeline_config,
    list_subjects,
    get_directory_structure,
    list_files_in_directory,
    read_file
)


def print_separator():
    print("\n" + "=" * 80 + "\n")


def main():
    # Set the dataset path to the example dataset
    dataset_path = str(Path(__file__).parent / "nipoppy_dataset")
    
    print("Nipoppy MCP Server - Example Usage")
    print(f"Dataset: {dataset_path}")
    print_separator()
    
    # 1. Get dataset info
    print("1. Getting dataset information...")
    result = get_dataset_info(dataset_path)
    print(f"Dataset Name: {result['config']['DATASET_NAME']}")
    print(f"Description: {result['config']['DATASET_DESCRIPTION']}")
    print(f"Version: {result['config']['VERSION']}")
    print_separator()
    
    # 2. Get manifest
    print("2. Getting manifest...")
    result = get_manifest(dataset_path)
    print(f"Manifest found at: {result['manifest_path']}")
    print(f"Total lines: {result['total_lines']}")
    print("\nFirst few lines:")
    print(result['content'][:200] + "...")
    print_separator()
    
    # 3. List pipelines
    print("3. Listing pipelines...")
    result = list_pipelines(dataset_path)
    print(f"Found {result['count']} pipeline(s):")
    for pipeline in result['pipelines']:
        print(f"  - {pipeline['name']}")
        print(f"    Config files: {', '.join(pipeline['config_files'])}")
    print_separator()
    
    # 4. Get pipeline config
    print("4. Getting fmriprep configuration...")
    result = get_pipeline_config("fmriprep-20.2.7", "config.json", dataset_path)
    if 'config' in result:
        print(f"Pipeline: {result['config']['pipeline']}")
        print(f"Version: {result['config']['version']}")
        print(f"Container: {result['config']['container']}")
    print_separator()
    
    # 5. List subjects
    print("5. Listing subjects in BIDS directory...")
    result = list_subjects(dataset_path, "bids")
    print(f"Found {result['count']} subject(s):")
    for subject in result['subjects']:
        sessions = f" with sessions: {', '.join(subject['sessions'])}" if subject['sessions'] else ""
        print(f"  - {subject['subject_id']}{sessions}")
    print_separator()
    
    # 6. Get directory structure
    print("6. Getting directory structure...")
    result = get_directory_structure(dataset_path, max_depth=2)
    print(f"Dataset root: {result['dataset_root']}")
    print(f"Structure (max depth {result['max_depth']}):")
    print(f"  - {result['structure']['name']} ({result['structure']['count']} items)")
    print_separator()
    
    # 7. List files in a directory
    print("7. Listing files in pipelines directory...")
    result = list_files_in_directory(dataset_path, "pipelines")
    print(f"Found {result['count']} item(s):")
    for item in result['items']:
        print(f"  - {item['name']} ({item['type']})")
    print_separator()
    
    # 8. Read a file
    print("8. Reading global_config.json...")
    result = read_file("global_config.json", dataset_path)
    if 'content' in result:
        print(f"File type: {result['type']}")
        print(f"Dataset name: {result['content']['DATASET_NAME']}")
    print_separator()
    
    print("All examples completed successfully!")


if __name__ == "__main__":
    main()
