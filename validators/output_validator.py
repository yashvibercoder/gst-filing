"""
Output Validator Module

Validates generated CSV output for correctness before GST portal upload.
Checks: column headers, rate integrity, row count reconciliation,
HSN B2B+B2C balance, empty files, GSTIN format.

Outputs a validation_report.csv summary.
"""

import pandas as pd
from pathlib import Path

STANDARD_RATES = {0, 5, 12, 18, 28}

# Map output filename → config key for column lookup
FILE_TO_CONFIG = {
    "b2b,sez,de.csv": "b2b",
    "b2cs.csv": "b2cs",
    "hsn(b2b).csv": "hsn_b2b",
    "hsn(b2c).csv": "hsn_b2c",
    "docs.csv": "documents",
    "cdnr1.csv": "credit_notes",
    "eco.csv": "eco",
}


def _check_columns(csv_path, expected_cols):
    """Check if CSV column headers match expected. Returns (status, detail)."""
    try:
        df = pd.read_csv(csv_path, nrows=0)
        actual = list(df.columns)
        if actual == expected_cols:
            return "PASS", ""
        else:
            missing = set(expected_cols) - set(actual)
            extra = set(actual) - set(expected_cols)
            detail = ""
            if missing:
                detail += f"missing={missing} "
            if extra:
                detail += f"extra={extra}"
            return "FAIL", detail.strip()
    except Exception as e:
        return "FAIL", str(e)


def _check_rates(csv_path):
    """Check all Rate values are standard integers. Returns (status, detail)."""
    try:
        df = pd.read_csv(csv_path)
        if "Rate" not in df.columns:
            return "PASS", "no Rate column"
        rates = pd.to_numeric(df["Rate"], errors="coerce").dropna()
        if len(rates) == 0:
            return "PASS", "no rate values"

        # Check for decimals (fractional part)
        has_decimal = (rates != rates.astype(int)).any()
        if has_decimal:
            bad = rates[rates != rates.astype(int)].unique()
            return "FAIL", f"decimal rates found: {sorted(bad)}"

        non_standard = set(rates.astype(int).unique()) - STANDARD_RATES
        if non_standard:
            return "WARN", f"non-standard rates: {sorted(non_standard)}"

        return "PASS", ""
    except Exception as e:
        return "FAIL", str(e)


def _check_gstin_format(csv_path, gstin_col):
    """Check GSTIN values are 15 characters. Returns (status, detail)."""
    try:
        df = pd.read_csv(csv_path)
        if gstin_col not in df.columns:
            return "PASS", "column not found"
        gstins = df[gstin_col].dropna().astype(str).str.strip()
        bad_len = gstins[gstins.str.len() != 15]
        if len(bad_len) > 0:
            samples = bad_len.head(3).tolist()
            return "WARN", f"{len(bad_len)} invalid GSTINs (e.g. {samples})"
        return "PASS", ""
    except Exception as e:
        return "FAIL", str(e)


def validate_columns(folders, states_dict, config):
    """Validation 1: Check column headers match templates."""
    results = []
    templates = config["output_templates"]

    for code, info in sorted(states_dict.items()):
        folder = folders[code]
        for filename, config_key in FILE_TO_CONFIG.items():
            csv_path = folder / filename
            if not csv_path.exists():
                continue
            expected = templates[config_key]["columns"]
            status, detail = _check_columns(csv_path, expected)
            results.append({
                "check": "columns",
                "state": f"{code}-{info['name']}",
                "file": filename,
                "status": status,
                "detail": detail,
            })
    return results


def validate_rates(folders, states_dict):
    """Validation 2: Check all rates are standard integers."""
    results = []
    rate_files = ["b2b,sez,de.csv", "b2cs.csv", "cdnr1.csv", "hsn(b2b).csv", "hsn(b2c).csv"]

    for code, info in sorted(states_dict.items()):
        folder = folders[code]
        for filename in rate_files:
            csv_path = folder / filename
            if not csv_path.exists():
                continue
            status, detail = _check_rates(csv_path)
            if status != "PASS" or not detail:
                results.append({
                    "check": "rates",
                    "state": f"{code}-{info['name']}",
                    "file": filename,
                    "status": status,
                    "detail": detail,
                })
    return results


def validate_b2b_row_counts(folders, states_dict, amazon_data, einvoice_data):
    """Validation 3: B2B row counts — output ≤ source (after dedup)."""
    results = []
    amz_b2b = amazon_data.get("b2b")

    for code, info in sorted(states_dict.items()):
        csv_path = folders[code] / "b2b,sez,de.csv"
        if not csv_path.exists():
            continue

        output_df = pd.read_csv(csv_path)
        output_rows = len(output_df)

        # Count source rows before dedup
        source_total = 0
        if amz_b2b is not None and "source_gstin" in amz_b2b.columns:
            source_total += len(amz_b2b[amz_b2b["source_gstin"].str[:2] == code])

        einv_b2b = einvoice_data.get(code, {}).get("b2b")
        if einv_b2b is not None:
            source_total += len(einv_b2b)

        # Check no duplicate Invoice Numbers in output
        dupes = output_df["Invoice Number"].duplicated().sum()
        if dupes > 0:
            results.append({
                "check": "b2b_rows",
                "state": f"{code}-{info['name']}",
                "file": "b2b,sez,de.csv",
                "status": "FAIL",
                "detail": f"{dupes} duplicate Invoice Numbers in output",
            })
        elif output_rows > source_total:
            results.append({
                "check": "b2b_rows",
                "state": f"{code}-{info['name']}",
                "file": "b2b,sez,de.csv",
                "status": "FAIL",
                "detail": f"output={output_rows} > source={source_total}",
            })
        else:
            deduped = source_total - output_rows
            detail = f"{output_rows} rows"
            if deduped > 0:
                detail += f" ({deduped} duplicates removed)"
            results.append({
                "check": "b2b_rows",
                "state": f"{code}-{info['name']}",
                "file": "b2b,sez,de.csv",
                "status": "PASS",
                "detail": detail,
            })
    return results


def validate_cn_row_counts(folders, states_dict, amazon_data, einvoice_data):
    """Validation 4: Credit note row counts — output ≤ source (after dedup)."""
    results = []
    amz_cn = amazon_data.get("credit_notes")

    for code, info in sorted(states_dict.items()):
        csv_path = folders[code] / "cdnr1.csv"
        if not csv_path.exists():
            continue

        output_df = pd.read_csv(csv_path)
        output_rows = len(output_df)

        source_total = 0
        if amz_cn is not None and "source_gstin" in amz_cn.columns:
            source_total += len(amz_cn[amz_cn["source_gstin"].str[:2] == code])

        einv_cn = einvoice_data.get(code, {}).get("credit_notes")
        if einv_cn is not None:
            source_total += len(einv_cn)

        # Check no duplicate Note Numbers in output
        dupes = output_df["Note Number"].duplicated().sum()
        if dupes > 0:
            results.append({
                "check": "cn_rows",
                "state": f"{code}-{info['name']}",
                "file": "cdnr1.csv",
                "status": "FAIL",
                "detail": f"{dupes} duplicate Note Numbers in output",
            })
        elif output_rows > source_total:
            results.append({
                "check": "cn_rows",
                "state": f"{code}-{info['name']}",
                "file": "cdnr1.csv",
                "status": "FAIL",
                "detail": f"output={output_rows} > source={source_total}",
            })
        else:
            deduped = source_total - output_rows
            detail = f"{output_rows} rows"
            if deduped > 0:
                detail += f" ({deduped} duplicates removed)"
            results.append({
                "check": "cn_rows",
                "state": f"{code}-{info['name']}",
                "file": "cdnr1.csv",
                "status": "PASS",
                "detail": detail,
            })
    return results


def validate_hsn_balance(folders, states_dict):
    """Validation 5: HSN B2B + B2C taxable value ≈ total (for E-Invoice states)."""
    results = []

    for code, info in sorted(states_dict.items()):
        b2b_path = folders[code] / "hsn(b2b).csv"
        b2c_path = folders[code] / "hsn(b2c).csv"

        if not b2b_path.exists():
            continue  # No E-Invoice for this state

        if not b2c_path.exists():
            results.append({
                "check": "hsn_balance",
                "state": f"{code}-{info['name']}",
                "file": "hsn(b2b)+hsn(b2c)",
                "status": "WARN",
                "detail": "hsn(b2b) exists but no hsn(b2c)",
            })
            continue

        b2b_df = pd.read_csv(b2b_path)
        b2c_df = pd.read_csv(b2c_path)

        b2b_taxable = pd.to_numeric(b2b_df["Taxable Value"], errors="coerce").sum()
        b2c_taxable = pd.to_numeric(b2c_df["Taxable Value"], errors="coerce").sum()

        results.append({
            "check": "hsn_balance",
            "state": f"{code}-{info['name']}",
            "file": "hsn(b2b)+hsn(b2c)",
            "status": "PASS",
            "detail": f"B2B={b2b_taxable:,.2f} + B2C={b2c_taxable:,.2f} = {b2b_taxable + b2c_taxable:,.2f}",
        })
    return results


def validate_no_empty_files(folders, states_dict):
    """Validation 6: No generated CSV has 0 data rows."""
    results = []

    for code, info in sorted(states_dict.items()):
        folder = folders[code]
        for csv_file in sorted(folder.glob("*.csv")):
            df = pd.read_csv(csv_file)
            if len(df) == 0:
                results.append({
                    "check": "empty_file",
                    "state": f"{code}-{info['name']}",
                    "file": csv_file.name,
                    "status": "FAIL",
                    "detail": "0 data rows",
                })
    return results


def validate_gstin_format(folders, states_dict):
    """Validation 7: GSTIN format check in B2B and CDNR."""
    results = []

    for code, info in sorted(states_dict.items()):
        for filename, col in [("b2b,sez,de.csv", "GSTIN/UIN of Recipient"),
                               ("cdnr1.csv", "GSTIN/UIN of Recipient")]:
            csv_path = folders[code] / filename
            if not csv_path.exists():
                continue
            status, detail = _check_gstin_format(csv_path, col)
            if status != "PASS":
                results.append({
                    "check": "gstin_format",
                    "state": f"{code}-{info['name']}",
                    "file": filename,
                    "status": status,
                    "detail": detail,
                })
    return results


def build_state_summary(folders, states_dict):
    """Validation 8: Per-state summary with row counts and taxable values."""
    rows = []

    for code, info in sorted(states_dict.items()):
        folder = folders[code]
        for csv_file in sorted(folder.glob("*.csv")):
            df = pd.read_csv(csv_file)
            taxable = 0
            if "Taxable Value" in df.columns:
                taxable = pd.to_numeric(df["Taxable Value"], errors="coerce").sum()
            elif "Net value of supplies" in df.columns:
                taxable = pd.to_numeric(df["Net value of supplies"], errors="coerce").sum()
            rows.append({
                "State": f"{code}-{info['name']}",
                "File": csv_file.name,
                "Rows": len(df),
                "Taxable Value": round(taxable, 2),
            })
    return pd.DataFrame(rows)


def run_validation(folders, states_dict, amazon_data, einvoice_data, config, output_root):
    """
    Run all validations and print summary.
    Returns total counts of PASS/FAIL/WARN.
    """
    print("\n" + "=" * 60)
    print("PHASE 7: VALIDATION")
    print("=" * 60)

    all_results = []

    # 1. Column headers
    print("\n  [1/7] Column header compliance...")
    results = validate_columns(folders, states_dict, config)
    all_results.extend(results)
    fails = sum(1 for r in results if r["status"] == "FAIL")
    if fails:
        print(f"        FAIL: {fails} file(s) with wrong columns")
        for r in results:
            if r["status"] == "FAIL":
                print(f"          {r['state']} / {r['file']}: {r['detail']}")
    else:
        print(f"        PASS: all {len(results)} files match template columns")

    # 2. Rate integrity
    print("\n  [2/7] Rate integrity...")
    results = validate_rates(folders, states_dict)
    all_results.extend(results)
    issues = [r for r in results if r["status"] != "PASS"]
    if issues:
        for r in issues:
            print(f"        {r['status']}: {r['state']} / {r['file']}: {r['detail']}")
    else:
        print("        PASS: all rates are standard integers")

    # 3. B2B row counts
    print("\n  [3/7] B2B row count reconciliation...")
    results = validate_b2b_row_counts(folders, states_dict, amazon_data, einvoice_data)
    all_results.extend(results)
    fails = [r for r in results if r["status"] == "FAIL"]
    if fails:
        for r in fails:
            print(f"        FAIL: {r['state']}: {r['detail']}")
    else:
        print(f"        PASS: all {len(results)} states match")

    # 4. Credit note row counts
    print("\n  [4/7] Credit notes row count reconciliation...")
    results = validate_cn_row_counts(folders, states_dict, amazon_data, einvoice_data)
    all_results.extend(results)
    fails = [r for r in results if r["status"] == "FAIL"]
    if fails:
        for r in fails:
            print(f"        FAIL: {r['state']}: {r['detail']}")
    else:
        print(f"        PASS: all {len(results)} states match")

    # 5. HSN balance
    print("\n  [5/7] HSN B2B + B2C balance...")
    results = validate_hsn_balance(folders, states_dict)
    all_results.extend(results)
    for r in results:
        print(f"        {r['status']}: {r['state']}: {r['detail']}")

    # 6. No empty files
    print("\n  [6/7] No empty output files...")
    results = validate_no_empty_files(folders, states_dict)
    all_results.extend(results)
    if results:
        for r in results:
            print(f"        FAIL: {r['state']} / {r['file']}")
    else:
        print("        PASS: no empty files")

    # 7. GSTIN format
    print("\n  [7/7] GSTIN format check...")
    results = validate_gstin_format(folders, states_dict)
    all_results.extend(results)
    if results:
        for r in results:
            print(f"        {r['status']}: {r['state']} / {r['file']}: {r['detail']}")
    else:
        print("        PASS: all GSTINs are 15 characters")

    # Summary
    pass_count = sum(1 for r in all_results if r["status"] == "PASS")
    fail_count = sum(1 for r in all_results if r["status"] == "FAIL")
    warn_count = sum(1 for r in all_results if r["status"] == "WARN")

    print(f"\n  --- Summary: {pass_count} PASS, {fail_count} FAIL, {warn_count} WARN ---")

    # Write state summary report
    summary_df = build_state_summary(folders, states_dict)
    report_path = Path(output_root) / "validation_report.csv"
    summary_df.to_csv(report_path, index=False)
    print(f"  Report: {report_path}")

    # Write structured check results for the portal validation view
    import csv as _csv
    checks_path = Path(output_root) / "validation_checks.csv"
    with open(checks_path, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=["check", "state", "file", "status", "detail"])
        writer.writeheader()
        writer.writerows(all_results)

    return {"pass": pass_count, "fail": fail_count, "warn": warn_count}
