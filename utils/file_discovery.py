"""
File Discovery Module
Auto-discovers input files using glob patterns from config.json.

Scans the input folder and matches files to platforms:
  - Flipkart: *Flipkart*
  - Amazon:   *A3SZBDZ05A1P39*
  - Meesho:   *Meesho*
  - E-Invoice: *EInvoice* or *E-Invoice*

No hardcoded file lists needed - new files are auto-detected.
"""

import json
from pathlib import Path


def load_config(project_root=None):
    """Load config.json from project root."""
    if project_root is None:
        project_root = Path(__file__).parent.parent
    config_path = Path(project_root) / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)


def discover_files(config=None, project_root=None):
    """
    Scan the input folder and match files to platforms using glob patterns.

    Returns dict like:
        {
            "flipkart": [Path("Input files/Flipkart_raw_gst_report_2.xlsx")],
            "amazon": [Path("Input files/GSTR1-...xlsx"), ...],
            "meesho": [Path("Input files/Meesho_gst_report.xlsx")],
            "einvoice": [],
            "offline_b2b": []
        }
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent
    project_root = Path(project_root)

    if config is None:
        config = load_config(project_root)

    input_folder = project_root / config["paths"]["input_folder"]

    if not input_folder.exists():
        print(f"  ERROR: Input folder not found: {input_folder}")
        return {}

    discovered = {}
    for platform, pattern in config["file_patterns"].items():
        matches = sorted(
            f for f in input_folder.glob(pattern)
            if not f.name.startswith("~$")
        )
        discovered[platform] = matches

    return discovered


def print_discovery_report(discovered):
    """Print a summary of discovered files."""
    print("=" * 60)
    print("PHASE 1: FILE DISCOVERY")
    print("=" * 60)

    total = 0
    for platform, files in discovered.items():
        count = len(files)
        total += count
        status = "OK" if count > 0 else "NONE"
        print(f"\n  [{status}] {platform.upper()}: {count} file(s)")
        for f in files:
            print(f"       - {f.name}")

    print(f"\n  TOTAL: {total} input file(s) discovered")
    print("=" * 60)
    return total


if __name__ == "__main__":
    config = load_config()
    discovered = discover_files(config)
    print_discovery_report(discovered)
