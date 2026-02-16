"""
Processing bridge — imports and runs System A pipeline from the portal.
"""

import sys
from pathlib import Path

from ..config import settings


def run_pipeline() -> dict:
    """
    Run the GST pipeline using System A modules.
    Returns dict with output_dir, states_count, files_count, validation summary.
    """
    project_root = settings.project_root

    # Add project root to sys.path so we can import System A modules
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    # Import System A modules
    from utils.file_discovery import load_config, discover_files
    from readers.flipkart_reader import FlipkartReader
    from readers.amazon_reader import AmazonReader
    from readers.meesho_reader import MeeshoReader
    from readers.einvoice_reader import EInvoiceReader
    from processors.hsn_cleaner import clean_hsn_codes, fill_empty_hsn
    from processors.rate_normalizer import normalize_rate
    from processors.state_detector import (
        normalize_meesho_states, detect_seller_states, create_state_folders
    )
    from generators.hsn_generator import generate_hsn_files
    from generators.gstr_b2b_gen import generate_b2b_files
    from generators.gstr_b2cs_gen import generate_b2cs_files
    from generators.creditnotes_gen import generate_creditnotes_files
    from generators.documents_gen import generate_documents_files
    from generators.eco_gen import generate_eco_files
    from validators.output_validator import run_validation

    output_root = project_root / "output"

    # Phase 1: File Discovery
    config = load_config(project_root)
    discovered = discover_files(config, project_root)

    # Phase 2: Data Loading
    flipkart_data = {}
    if discovered.get("flipkart"):
        reader = FlipkartReader(discovered["flipkart"], config)
        flipkart_data = reader.read_all()

    amazon_data = {}
    if discovered.get("amazon"):
        reader = AmazonReader(discovered["amazon"], config)
        amazon_data = reader.read_all()

    meesho_data = {}
    if discovered.get("meesho"):
        reader = MeeshoReader(discovered["meesho"], config)
        meesho_data = reader.read_all()

    einvoice_data = {}
    if discovered.get("einvoice"):
        reader = EInvoiceReader(discovered["einvoice"], config)
        einvoice_data = reader.read_all()

    # Phase 3: Data Normalization
    rate_hsn_map = config.get("empty_hsn_fill_map")

    amazon_hsn = amazon_data.get("hsn")
    if amazon_hsn is not None and len(amazon_hsn) > 0:
        amazon_hsn = clean_hsn_codes(amazon_hsn, "HSN")
        amazon_hsn = normalize_rate(amazon_hsn, "Rate")
        amazon_hsn = fill_empty_hsn(amazon_hsn, "HSN", "Taxable Value", "Rate", rate_hsn_map)
        amazon_data["hsn"] = amazon_hsn

    flipkart_hsn = flipkart_data.get("hsn")
    if flipkart_hsn is not None and len(flipkart_hsn) > 0:
        flipkart_hsn = clean_hsn_codes(flipkart_hsn, "HSN Number")
        flipkart_data["hsn"] = flipkart_hsn

    meesho_raw = meesho_data.get("raw")
    if meesho_raw is not None and len(meesho_raw) > 0:
        meesho_cols = config["meesho_columns"]
        meesho_raw = normalize_meesho_states(meesho_raw, meesho_cols["state"])
        meesho_data["raw"] = meesho_raw

    # Phase 4: State Detection
    states_dict = detect_seller_states(
        flipkart_data, amazon_data, meesho_data,
        discovered.get("amazon", []),
        discovered.get("einvoice", [])
    )

    # Phase 5: Output Structure
    folders = create_state_folders(states_dict, output_root)

    # Phase 6: Template Generation
    generate_hsn_files(
        einvoice_data, amazon_data.get("hsn"), flipkart_data.get("hsn"),
        meesho_data.get("raw"), states_dict, folders, config
    )
    b2b_by_state = generate_b2b_files(amazon_data, einvoice_data, states_dict, folders)
    generate_b2cs_files(flipkart_data, amazon_data, meesho_data, states_dict, folders, config)
    generate_creditnotes_files(amazon_data, einvoice_data, states_dict, folders)
    generate_documents_files(flipkart_data, b2b_by_state, states_dict, folders)
    generate_eco_files(flipkart_data, states_dict, folders)

    # Phase 7: Validation
    counts = run_validation(folders, states_dict, amazon_data, einvoice_data, config, output_root)

    # Count total output files
    total_files = sum(
        len(list(folder.glob("*.csv")))
        for folder in folders.values()
    )

    return {
        "output_dir": output_root,
        "states_count": len(states_dict),
        "files_count": total_files,
        "validation": counts,
    }
