"""
GST Automation - Main Orchestrator

Coordinates all phases of GST return generation:
  Phase 1: File Discovery      - Auto-detect input files
  Phase 2: Data Loading        - Read Flipkart, Amazon, Meesho, E-Invoice
  Phase 3: Data Normalization  - Clean HSN codes, normalize rates, normalize states
  Phase 4: State Detection     - Find states with transaction data
  Phase 5: Output Structure    - Create per-state output folders
  Phase 6: Template Generation - Generate 7 CSV templates per state
  Phase 7: Validation         - Cross-check totals, format compliance

Usage: python main.py
"""

from pathlib import Path

from utils.file_discovery import load_config, discover_files, print_discovery_report
from readers.flipkart_reader import FlipkartReader
from readers.amazon_reader import AmazonReader
from readers.meesho_reader import MeeshoReader
from readers.einvoice_reader import EInvoiceReader
from processors.hsn_cleaner import clean_hsn_codes, fill_empty_hsn, generate_empty_hsn_report
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


def main():
    project_root = Path(__file__).parent
    output_root = project_root / "output"

    # ── Phase 1: File Discovery ──────────────────────────────────
    config = load_config(project_root)
    discovered = discover_files(config, project_root)
    print_discovery_report(discovered)

    # ── Phase 2: Data Loading ────────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 2: DATA LOADING")
    print("=" * 60)

    # Flipkart
    flipkart_data = {}
    if discovered.get("flipkart"):
        print("\n  Reading Flipkart...")
        reader = FlipkartReader(discovered["flipkart"], config)
        flipkart_data = reader.read_all()
    else:
        print("\n  No Flipkart files found — skipping")

    # Amazon
    amazon_data = {}
    if discovered.get("amazon"):
        print("\n  Reading Amazon...")
        reader = AmazonReader(discovered["amazon"], config)
        amazon_data = reader.read_all()
    else:
        print("\n  No Amazon files found — skipping")

    # Meesho
    meesho_data = {}
    if discovered.get("meesho"):
        print("\n  Reading Meesho...")
        reader = MeeshoReader(discovered["meesho"], config)
        meesho_data = reader.read_all()
    else:
        print("\n  No Meesho files found — skipping")

    # E-Invoice
    einvoice_data = {}
    if discovered.get("einvoice"):
        print("\n  Reading E-Invoice...")
        reader = EInvoiceReader(discovered["einvoice"], config)
        einvoice_data = reader.read_all()
    else:
        print("\n  No E-Invoice files found — skipping")

    # ── Phase 3: Data Normalization ──────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 3: DATA NORMALIZATION")
    print("=" * 60)

    rate_hsn_map = config.get("empty_hsn_fill_map")

    # Normalize Amazon HSN
    amazon_hsn = amazon_data.get("hsn")
    if amazon_hsn is not None and len(amazon_hsn) > 0:
        print("\n  Cleaning Amazon HSN...")
        amazon_hsn = clean_hsn_codes(amazon_hsn, "HSN")
        amazon_hsn = normalize_rate(amazon_hsn, "Rate")
        generate_empty_hsn_report(
            amazon_hsn, "HSN", "Taxable Value", "Rate",
            output_root / "empty_hsn_report.csv", rate_hsn_map
        )
        amazon_hsn = fill_empty_hsn(amazon_hsn, "HSN", "Taxable Value", "Rate", rate_hsn_map)
        amazon_data["hsn"] = amazon_hsn

    # Normalize Flipkart HSN
    flipkart_hsn = flipkart_data.get("hsn")
    if flipkart_hsn is not None and len(flipkart_hsn) > 0:
        print("\n  Cleaning Flipkart HSN...")
        flipkart_hsn = clean_hsn_codes(flipkart_hsn, "HSN Number")
        flipkart_data["hsn"] = flipkart_hsn

    # Normalize Meesho states
    meesho_raw = meesho_data.get("raw")
    if meesho_raw is not None and len(meesho_raw) > 0:
        print("\n  Normalizing Meesho states...")
        meesho_cols = config["meesho_columns"]
        meesho_raw = normalize_meesho_states(meesho_raw, meesho_cols["state"])
        meesho_data["raw"] = meesho_raw

    # ── Phase 4: State Detection ─────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 4: STATE DETECTION")
    print("=" * 60)

    states_dict = detect_seller_states(
        flipkart_data, amazon_data, meesho_data,
        discovered.get("amazon", []),
        discovered.get("einvoice", [])
    )

    print(f"\n  Found {len(states_dict)} seller states:")
    for code, info in sorted(states_dict.items()):
        platforms = ", ".join(info["platforms"])
        print(f"    {code}-{info['name']}: {platforms}")

    # ── Phase 5: Output Structure ────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 5: OUTPUT STRUCTURE")
    print("=" * 60)

    folders = create_state_folders(states_dict, output_root)
    print(f"\n  Created {len(folders)} state folders in {output_root}")

    # ── Phase 6: Template Generation ─────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 6: TEMPLATE GENERATION")
    print("=" * 60)

    # 1. HSN B2B + B2C
    print("\n  --- HSN Templates ---")
    generate_hsn_files(
        einvoice_data,
        amazon_data.get("hsn"),
        flipkart_data.get("hsn"),
        meesho_data.get("raw"),
        states_dict, folders, config
    )

    # 2. B2B (Amazon + E-Invoice)
    print("\n  --- B2B Templates ---")
    b2b_by_state = generate_b2b_files(amazon_data, einvoice_data, states_dict, folders)

    # 3. B2CS (Flipkart + Amazon + Meesho)
    print("\n  --- B2CS Templates ---")
    generate_b2cs_files(
        flipkart_data, amazon_data, meesho_data,
        states_dict, folders, config
    )

    # 4. Credit Notes (Amazon + E-Invoice)
    print("\n  --- Credit Notes Templates ---")
    generate_creditnotes_files(amazon_data, einvoice_data, states_dict, folders)

    # 5. Documents (Flipkart + B2B invoice series)
    print("\n  --- Documents Templates ---")
    generate_documents_files(flipkart_data, b2b_by_state, states_dict, folders)

    # 6. ECO (Flipkart only)
    print("\n  --- ECO Templates ---")
    generate_eco_files(flipkart_data, states_dict, folders)

    # ── Phase 7: Validation ─────────────────────────────────────
    counts = run_validation(
        folders, states_dict, amazon_data, einvoice_data, config, output_root
    )

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"\n  Output: {output_root}")
    print(f"  States: {len(states_dict)}")
    print(f"  Templates: hsn(b2b), hsn(b2c), b2b, b2cs, cdnr1, docs, eco")
    if counts["fail"] > 0:
        print(f"  Validation: {counts['fail']} FAIL(s) — review above")
    else:
        print(f"  Validation: ALL PASS")
    print()


if __name__ == "__main__":
    main()
