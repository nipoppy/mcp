#!/usr/bin/env python3
"""
Example script demonstrating the refactored Nipoppy MCP server usage.

This script shows how to use the new tools and resources to explore a Nipoppy dataset.
Set the NIPOPPY_DATASET_ROOT environment variable to point to your dataset.
"""

import os
import sys
from pathlib import Path

def main():
    """Demonstrate MCP server functionality."""
    dataset_root = os.environ.get("NIPOPPY_DATASET_ROOT")
    
    if not dataset_root:
        print("❌ Error: NIPOPPY_DATASET_ROOT environment variable not set.")
        print("Set it to point to your Nipoppy dataset:")
        print("export NIPOPPY_DATASET_ROOT=/path/to/your/nipoppy/dataset")
        return 1
    
    print(f"🔍 Exploring Nipoppy dataset: {dataset_root}")
    print()
    
    try:
        from nipoppy_mcp.server import (
            get_dataset_info,
            get_participants_sessions,
            navigate_dataset
        )
        
        # 1. Get enhanced dataset overview
        print("📊 Dataset Overview:")
        info = get_dataset_info(
            nipoppy_root=dataset_root,
            include_pipeline_details=True,
            include_status_summary=True
        )
        print(f"   Participants: {info['n_participants']}")
        print(f"   Sessions: {info['n_sessions']}")
        print(f"   Dataset root: {info['dataset_root']}")
        print()
        
        # 2. Explore different data stages
        print("👥 Participants by Data Stage:")
        stages = ["all", "imaging", "downloaded", "organized", "bidsified"]
        for stage in stages:
            try:
                participants_sessions = get_participants_sessions(
                    nipoppy_root=dataset_root,
                    data_stage=stage
                )
                unique_participants = len(set([ps[0] for ps in participants_sessions]))
                print(f"   {stage:12}: {unique_participants:3} participants, {len(participants_sessions):3} participant-session pairs")
            except Exception as e:
                print(f"   {stage:12}: Error - {str(e)[:40]}...")
        print()
        
        # 3. Navigate dataset structure
        print("📂 Dataset Navigation:")
        path_types = ["dataset_root", "config", "directory"]
        targets = {"directory": ["bids", "derivatives", "tabular"]}
        
        for path_type in path_types:
            try:
                if path_type == "directory":
                    for target in targets[path_type]:
                        result = navigate_dataset(
                            nipoppy_root=dataset_root,
                            path_type=path_type,
                            target=target
                        )
                        print(f"   {path_type}/{target:12}: {result['path']}")
                else:
                    result = navigate_dataset(
                        nipoppy_root=dataset_root,
                        path_type=path_type
                    )
                    print(f"   {path_type:12}: {result['path']}")
            except Exception as e:
                print(f"   {path_type:12}: Error - {str(e)[:40]}...")
        
        print()
        print("✅ Demo completed successfully!")
        print()
        print("💡 To access this data through MCP clients:")
        print("   1. Set NIPOPPY_DATASET_ROOT environment variable")
        print("   2. Start the MCP server: python -m nipoppy_mcp.server")
        print("   3. Connect your MCP client to access tools and resources")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())