"""
GST Output Audit Tool

Compares generated output CSVs against previous month's actual template CSVs.
Runs 10 automated checks and generates a markdown report for Claude consumption.

Usage:
    1. Copy template files into audit/templates/
    2. Copy output files into audit/output/
    3. python audit/run_audit.py
    4. Read audit/reports/audit_report.md
"""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime

STANDARD_RATES = {0, 5, 12, 18, 28}

# Base names for matching output → template
FILE_BASE_NAMES = [
    "b2b,sez,de",
    "b2cs",
    "cdnr1",
    "hsn(b2b)",
    "hsn(b2c)",
    "docs",
    "eco",
]


# ── File Matching ─────────────────────────────────────────────

def match_files(output_dir, template_dir):
    """
    Match output CSVs to template CSVs by base name.
    Returns list of (output_path, template_path, display_name) tuples.
    Also returns unmatched files from both sides.
    """
    out_files = {f.name: f for f in sorted(output_dir.glob("*.csv"))}
    tpl_files = {f.name: f for f in sorted(template_dir.glob("*.csv"))}

    matched = []
    used_tpl = set()

    for out_name, out_path in out_files.items():
        out_base = out_name.replace(".csv", "")
        best_tpl = None

        # Try exact match first
        if out_name in tpl_files:
            best_tpl = tpl_files[out_name]
        else:
            # Try prefix match (e.g., "b2b,sez,de" matches "b2b,sez,de DEC.csv")
            for tpl_name, tpl_path in tpl_files.items():
                if tpl_name.startswith(out_base):
                    best_tpl = tpl_path
                    break

        if best_tpl:
            matched.append((out_path, best_tpl, out_name))
            used_tpl.add(best_tpl.name)
        else:
            matched.append((out_path, None, out_name))

    # Templates without output match
    unmatched_tpl = [
        tpl_files[name] for name in tpl_files if name not in used_tpl
    ]

    return matched, unmatched_tpl


# ── Check Functions ───────────────────────────────────────────

def check_columns(out_df, tpl_df, name):
    """Check 1: Column header match."""
    out_cols = list(out_df.columns)
    tpl_cols = list(tpl_df.columns)

    # Strip trailing empty columns from template (some have trailing commas)
    tpl_cols = [c for c in tpl_cols if not c.startswith("Unnamed")]

    if out_cols == tpl_cols:
        return {"status": "PASS", "detail": ""}

    missing = [c for c in tpl_cols if c not in out_cols]
    extra = [c for c in out_cols if c not in tpl_cols]
    order_match = set(out_cols) == set(tpl_cols)

    detail = ""
    if missing:
        detail += f"Missing: {missing}. "
    if extra:
        detail += f"Extra: {extra}. "
    if order_match and not missing and not extra:
        detail = "Same columns but different order."

    return {"status": "FAIL", "detail": detail.strip()}


def check_duplicates(df, key_col, name):
    """Check 2: Duplicate invoice/note detection."""
    if key_col not in df.columns:
        return {"status": "SKIP", "detail": f"No '{key_col}' column", "duplicates": []}

    # Include Rate in duplicate key — same invoice/note at different rates is valid (multi-rate)
    dupe_subset = [key_col, "Rate"] if "Rate" in df.columns else [key_col]
    dupes = df[df.duplicated(subset=dupe_subset, keep=False)]
    if len(dupes) == 0:
        return {"status": "PASS", "detail": "No duplicates", "duplicates": []}

    dupe_numbers = sorted(dupes[key_col].unique())
    count = len(dupe_numbers)

    # Analyze each duplicate pair
    dupe_details = []
    for num in dupe_numbers[:20]:  # Cap at 20 for report readability
        rows = df[df[key_col] == num]
        has_name = rows["Receiver Name"].notna() & (rows["Receiver Name"] != "")
        sources = []
        for _, row in rows.iterrows():
            src = "E-Invoice" if (pd.notna(row.get("Receiver Name")) and str(row.get("Receiver Name")).strip()) else "Amazon"
            sources.append(src)
        dupe_details.append({
            "number": num,
            "count": len(rows),
            "sources": sources,
        })

    return {
        "status": "FAIL",
        "detail": f"{count} duplicate {key_col}s found ({len(dupes)} total rows)",
        "duplicates": dupe_details,
        "total_dupe_numbers": count,
        "total_dupe_rows": len(dupes),
    }


def check_pos_format(df, name):
    """Check 3: Place Of Supply format consistency."""
    if "Place Of Supply" not in df.columns:
        return {"status": "SKIP", "detail": "No Place Of Supply column"}

    pos = df["Place Of Supply"].dropna().astype(str)
    if len(pos) == 0:
        return {"status": "SKIP", "detail": "No PoS values"}

    # Detect formats: "XX-Name" vs "XX - Name"
    tight = pos.str.match(r"^\d{2}-\S")  # No space after dash
    spaced = pos.str.match(r"^\d{2}\s+-\s+")  # Space around dash

    tight_count = tight.sum()
    spaced_count = spaced.sum()
    other_count = len(pos) - tight_count - spaced_count

    if spaced_count > 0 and tight_count > 0:
        return {
            "status": "FAIL",
            "detail": f"Mixed formats: {tight_count} tight (XX-Name), {spaced_count} spaced (XX - Name)",
            "tight": int(tight_count),
            "spaced": int(spaced_count),
        }
    elif spaced_count > 0:
        return {
            "status": "WARN",
            "detail": f"All {spaced_count} values use spaced format (XX - Name)",
            "tight": 0,
            "spaced": int(spaced_count),
        }
    else:
        return {"status": "PASS", "detail": f"All {tight_count} values use tight format (XX-Name)"}


def check_rates(df, name):
    """Check 4: Rate integrity."""
    if "Rate" not in df.columns:
        return {"status": "SKIP", "detail": "No Rate column"}

    rates = pd.to_numeric(df["Rate"], errors="coerce").dropna()
    if len(rates) == 0:
        return {"status": "SKIP", "detail": "No rate values"}

    # Check for decimals (fractional values < 1 that look like 0.05, 0.18)
    decimal_rates = rates[(rates > 0) & (rates < 1)]
    if len(decimal_rates) > 0:
        bad = sorted(decimal_rates.unique())
        return {
            "status": "FAIL",
            "detail": f"Decimal rates found: {bad[:10]}",
            "decimal_count": len(decimal_rates),
        }

    # Check for non-integer
    non_int = rates[rates != rates.astype(int)]
    if len(non_int) > 0:
        bad = sorted(non_int.unique())
        return {
            "status": "FAIL",
            "detail": f"Non-integer rates: {bad[:10]}",
        }

    # Check for non-standard
    int_rates = set(int(r) for r in rates.astype(int).unique())
    non_standard = int_rates - STANDARD_RATES
    if non_standard:
        return {
            "status": "WARN",
            "detail": f"Non-standard rates: {sorted(non_standard)}",
        }

    return {"status": "PASS", "detail": f"All {len(rates)} rates are standard integers: {sorted(int_rates)}"}


def check_precision(df, name):
    """Check 5: Floating point precision."""
    numeric_cols = df.select_dtypes(include=["float64", "float32"]).columns
    bad_values = []

    for col in numeric_cols:
        vals = df[col].dropna()
        for val in vals:
            # Check if value has more than 2 meaningful decimal places
            rounded = round(val, 2)
            if abs(val - rounded) > 1e-9:
                bad_values.append({"column": col, "value": val, "should_be": rounded})

    if not bad_values:
        return {"status": "PASS", "detail": f"All values in {len(numeric_cols)} numeric columns are clean"}

    # Group by column
    by_col = {}
    for bv in bad_values:
        col = bv["column"]
        if col not in by_col:
            by_col[col] = []
        by_col[col].append(bv)

    detail_parts = []
    for col, items in by_col.items():
        sample = items[0]
        detail_parts.append(f"{col}: {len(items)} values (e.g., {sample['value']} → {sample['should_be']})")

    return {
        "status": "FAIL",
        "detail": f"{len(bad_values)} values need rounding: " + "; ".join(detail_parts),
        "bad_count": len(bad_values),
        "by_column": {col: len(items) for col, items in by_col.items()},
        "samples": bad_values[:10],
    }


def compare_row_counts(out_df, tpl_df, name):
    """Check 6: Row count comparison."""
    out_rows = len(out_df)
    tpl_rows = len(tpl_df)
    diff = out_rows - tpl_rows

    return {
        "status": "INFO",
        "detail": f"Output: {out_rows}, Template: {tpl_rows}, Diff: {diff:+d}",
        "output_rows": out_rows,
        "template_rows": tpl_rows,
        "diff": diff,
    }


def compare_totals(out_df, tpl_df, name):
    """Check 7: Taxable value totals comparison."""
    # Find the right value column
    for col in ["Taxable Value", "Net value of supplies"]:
        if col in out_df.columns and col in tpl_df.columns:
            out_total = pd.to_numeric(out_df[col], errors="coerce").sum()
            tpl_total = pd.to_numeric(tpl_df[col], errors="coerce").sum()
            diff = out_total - tpl_total
            pct = (diff / tpl_total * 100) if tpl_total != 0 else 0

            return {
                "status": "INFO",
                "detail": f"Output: {out_total:,.2f}, Template: {tpl_total:,.2f}, Diff: {diff:+,.2f} ({pct:+.1f}%)",
                "output_total": round(out_total, 2),
                "template_total": round(tpl_total, 2),
                "diff": round(diff, 2),
                "pct_change": round(pct, 1),
                "column": col,
            }

    return {"status": "SKIP", "detail": "No taxable value column found"}


def check_uqc(out_df, tpl_df, name):
    """Check 8: UQC format check (hsn files only)."""
    if "UQC" not in out_df.columns:
        return {"status": "SKIP", "detail": "No UQC column"}

    out_uqc = set(out_df["UQC"].dropna().unique())
    tpl_uqc = set(tpl_df["UQC"].dropna().unique()) if "UQC" in tpl_df.columns else set()

    # Detect short vs long format
    out_has_long = any("-" in str(u) for u in out_uqc)
    tpl_has_long = any("-" in str(u) for u in tpl_uqc)

    if out_has_long == tpl_has_long:
        return {
            "status": "PASS",
            "detail": f"Both use {'long' if out_has_long else 'short'} format. Output: {sorted(out_uqc)}, Template: {sorted(tpl_uqc)}",
        }

    return {
        "status": "WARN",
        "detail": f"Format mismatch — Output: {sorted(out_uqc)} ({'long' if out_has_long else 'short'}), Template: {sorted(tpl_uqc)} ({'long' if tpl_has_long else 'short'})",
        "output_uqc": sorted(str(u) for u in out_uqc),
        "template_uqc": sorted(str(u) for u in tpl_uqc),
    }


def check_completeness(out_df, tpl_df, name):
    """Check 9: Data completeness (docs + eco)."""
    if "docs" in name:
        # Extract series prefixes (alphabetic prefix before digits)
        def get_prefix(val):
            val = str(val).strip()
            m = re.match(r'^([A-Za-z\-]+)', val)
            return m.group(1) if m else val

        tpl_prefixes = []
        if "Sr. No. From" in tpl_df.columns:
            tpl_prefixes = sorted(set(get_prefix(v) for v in tpl_df["Sr. No. From"].dropna()))
        out_prefixes = []
        if "Sr. No. From" in out_df.columns:
            out_prefixes = sorted(set(get_prefix(v) for v in out_df["Sr. No. From"].dropna()))

        missing = [p for p in tpl_prefixes if p not in out_prefixes]

        if not missing:
            return {"status": "PASS", "detail": f"All {len(tpl_prefixes)} invoice series present: {out_prefixes}"}

        return {
            "status": "WARN",
            "detail": f"Output has {len(out_prefixes)} series ({out_prefixes}), template has {len(tpl_prefixes)} ({tpl_prefixes}). Missing series: {missing}",
            "output_series": out_prefixes,
            "template_series": tpl_prefixes,
            "missing": missing,
        }

    elif "eco" in name:
        gstin_col = "GSTIN of E-Commerce Operator"
        if gstin_col not in out_df.columns or gstin_col not in tpl_df.columns:
            return {"status": "SKIP", "detail": "No GSTIN column"}

        out_ops = set(out_df[gstin_col].dropna().unique())
        tpl_ops = set(tpl_df[gstin_col].dropna().unique())
        missing = tpl_ops - out_ops

        if not missing:
            return {"status": "PASS", "detail": f"All {len(tpl_ops)} operators present"}

        return {
            "status": "WARN",
            "detail": f"Output has {len(out_ops)} operators, template has {len(tpl_ops)}. Missing: {sorted(missing)}",
            "output_operators": sorted(out_ops),
            "template_operators": sorted(tpl_ops),
            "missing": sorted(missing),
        }

    return {"status": "SKIP", "detail": "Not docs or eco"}


def compare_values(out_df, tpl_df, key_col, name):
    """Check 10: Value-level comparison for matched invoices/notes."""
    if key_col not in out_df.columns or key_col not in tpl_df.columns:
        return {"status": "SKIP", "detail": f"No '{key_col}' column"}

    out_keys = set(out_df[key_col].dropna().astype(str))
    tpl_keys = set(tpl_df[key_col].dropna().astype(str))

    matched_keys = out_keys & tpl_keys
    only_output = out_keys - tpl_keys
    only_template = tpl_keys - out_keys

    # Compare values for matched keys
    value_col = "Taxable Value"
    mismatches = []

    if value_col in out_df.columns and value_col in tpl_df.columns:
        for key in sorted(matched_keys)[:100]:  # Cap at 100
            out_rows = out_df[out_df[key_col].astype(str) == key]
            tpl_rows = tpl_df[tpl_df[key_col].astype(str) == key]

            out_val = pd.to_numeric(out_rows[value_col], errors="coerce").sum()
            tpl_val = pd.to_numeric(tpl_rows[value_col], errors="coerce").sum()

            if abs(out_val - tpl_val) > 1.0:
                mismatches.append({
                    "key": key,
                    "output_value": round(out_val, 2),
                    "template_value": round(tpl_val, 2),
                    "diff": round(out_val - tpl_val, 2),
                })

    status = "FAIL" if mismatches else "PASS"
    detail = (
        f"Matched: {len(matched_keys)}, Only in output: {len(only_output)}, "
        f"Only in template: {len(only_template)}, Value mismatches: {len(mismatches)}"
    )

    return {
        "status": status,
        "detail": detail,
        "matched": len(matched_keys),
        "only_output": len(only_output),
        "only_template": len(only_template),
        "mismatches": mismatches[:20],
        "only_output_samples": sorted(only_output)[:10],
        "only_template_samples": sorted(only_template)[:10],
    }


# ── Report Generation ─────────────────────────────────────────

def generate_report(all_results, file_results, output_dir, template_dir, report_path,
                    unmatched_tpl):
    """Generate audit_report.md."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("# GST Output Audit Report")
    lines.append(f"Generated: {now}")
    lines.append(f"Output folder: `{output_dir}`")
    lines.append(f"Template folder: `{template_dir}`")
    lines.append("")

    # ── Quick Summary ──
    lines.append("## Quick Summary")
    lines.append("")
    lines.append("| # | Check | Status | Key Finding |")
    lines.append("|---|-------|--------|-------------|")

    check_names = [
        "Column Headers", "Duplicate Invoices", "Place Of Supply Format",
        "Rate Integrity", "Floating Point Precision", "Row Counts",
        "Taxable Value Totals", "UQC Format", "Data Completeness",
        "Value Comparison"
    ]

    for i, (check_name, results) in enumerate(zip(check_names, all_results), 1):
        # Aggregate status across files
        statuses = [r["status"] for r in results if r["status"] != "SKIP"]
        if not statuses:
            agg_status = "SKIP"
        elif any(s == "FAIL" for s in statuses):
            agg_status = "FAIL"
        elif any(s == "WARN" for s in statuses):
            agg_status = "WARN"
        else:
            agg_status = "PASS"

        # Key finding from first non-skip result
        key_finding = ""
        for r in results:
            if r["status"] != "SKIP" and r.get("detail"):
                key_finding = r["detail"][:80]
                break

        lines.append(f"| {i} | {check_name} | **{agg_status}** | {key_finding} |")

    lines.append("")

    # ── Files Analyzed ──
    lines.append("## Files Analyzed")
    lines.append("")
    lines.append("| File | Output Rows | Template Rows | Diff |")
    lines.append("|------|-------------|---------------|------|")

    for name, fr in file_results.items():
        out_rows = fr.get("output_rows", "—")
        tpl_rows = fr.get("template_rows", "—")
        diff = fr.get("diff", "—")
        if isinstance(diff, int):
            diff = f"{diff:+d}"
        lines.append(f"| {name} | {out_rows} | {tpl_rows} | {diff} |")

    if unmatched_tpl:
        lines.append("")
        lines.append("**Templates without output match:**")
        for f in unmatched_tpl:
            lines.append(f"- `{f.name}`")

    lines.append("")

    # ── Detailed Findings ──
    lines.append("## Detailed Findings")
    lines.append("")

    for i, (check_name, results) in enumerate(zip(check_names, all_results), 1):
        lines.append(f"### {i}. {check_name}")
        lines.append("")

        for r in results:
            fname = r.get("file", "")
            status = r["status"]
            detail = r.get("detail", "")

            if status == "SKIP":
                continue

            lines.append(f"**{fname}**: {status} — {detail}")

            # Extra details for duplicates
            if "duplicates" in r and r["duplicates"]:
                lines.append("")
                lines.append(f"| {r.get('key_col', 'Number')} | Copies | Sources |")
                lines.append("|--------|--------|---------|")
                for d in r["duplicates"][:15]:
                    sources = ", ".join(d["sources"])
                    lines.append(f"| {d['number']} | {d['count']} | {sources} |")
                if r.get("total_dupe_numbers", 0) > 15:
                    lines.append(f"| ... | ... | ({r['total_dupe_numbers']} total) |")

            # Extra details for value comparison
            if "mismatches" in r and r["mismatches"]:
                lines.append("")
                lines.append("**Value mismatches (>1.0 tolerance):**")
                lines.append(f"| {r.get('key_col', 'Key')} | Output | Template | Diff |")
                lines.append("|--------|--------|----------|------|")
                for m in r["mismatches"][:10]:
                    lines.append(f"| {m['key']} | {m['output_value']:,.2f} | {m['template_value']:,.2f} | {m['diff']:+,.2f} |")

            if "only_output_samples" in r and r["only_output_samples"]:
                lines.append("")
                lines.append(f"**Only in output ({r['only_output']} total):** {', '.join(r['only_output_samples'][:5])}...")

            if "only_template_samples" in r and r["only_template_samples"]:
                lines.append(f"**Only in template ({r['only_template']} total):** {', '.join(r['only_template_samples'][:5])}...")

            # Precision samples
            if "samples" in r and r.get("bad_count"):
                lines.append("")
                lines.append("**Samples:**")
                for s in r["samples"][:5]:
                    lines.append(f"- `{s['column']}`: `{s['value']}` → should be `{s['should_be']}`")

            # Completeness details
            if "missing" in r and r["missing"]:
                lines.append("")
                lines.append("**Missing from output:**")
                for m in r["missing"]:
                    lines.append(f"- `{m}`")

            lines.append("")

        lines.append("")

    # ── Recommended Fixes ──
    lines.append("## Recommended Fixes")
    lines.append("")
    lines.append("*Auto-generated from findings. Feed this section to Claude to implement changes.*")
    lines.append("")

    fixes = _generate_fixes(all_results, check_names)
    for fix in fixes:
        lines.append(f"- **{fix['severity']}**: {fix['description']}")

    if not fixes:
        lines.append("- No fixes needed — all checks passed!")

    lines.append("")

    # ── Raw Data Samples ──
    lines.append("## Raw Data Samples")
    lines.append("")
    lines.append("*First 3 rows of each output file for context.*")
    lines.append("")

    for name, fr in file_results.items():
        if fr.get("out_df") is not None:
            lines.append(f"### {name}")
            lines.append("```")
            lines.append(fr["out_df"].head(3).to_string(index=False))
            lines.append("```")
            lines.append("")

    # Write report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _generate_fixes(all_results, check_names):
    """Auto-generate fix recommendations from results."""
    fixes = []

    # Check 2: Duplicates
    for r in all_results[1]:
        if r["status"] == "FAIL" and r.get("total_dupe_numbers", 0) > 0:
            fname = r.get("file", "")
            key = r.get("key_col", "Invoice Number")
            count = r["total_dupe_numbers"]
            fixes.append({
                "severity": "CRITICAL",
                "description": (
                    f"Deduplicate `{fname}` by `{key}` — {count} duplicates found. "
                    f"Keep the row WITH Receiver Name (E-Invoice source), drop the row WITHOUT (Amazon source). "
                    f"Fix in the generator that concatenates Amazon + E-Invoice data."
                ),
            })

    # Check 3: PoS format
    for r in all_results[2]:
        if r["status"] == "FAIL":
            fname = r.get("file", "")
            fixes.append({
                "severity": "CRITICAL",
                "description": (
                    f"Normalize Place Of Supply in `{fname}` — mixed formats detected. "
                    f"Apply regex: strip spaces around dash → `XX-State Name`. "
                    f"E-Invoice uses `XX - Name` (spaced), Amazon uses `XX-Name` (tight). "
                    f"Normalize after combining sources, before writing CSV."
                ),
            })

    # Check 4: Rates
    for r in all_results[3]:
        if r["status"] == "FAIL":
            fname = r.get("file", "")
            fixes.append({
                "severity": "CRITICAL",
                "description": (
                    f"Fix rates in `{fname}` — {r['detail']}. "
                    f"All rates must be integers (5, 12, 18, 28). "
                    f"Apply rate normalization: multiply by 100 if <1, then cast to int."
                ),
            })

    # Check 5: Precision
    for r in all_results[4]:
        if r["status"] == "FAIL":
            fname = r.get("file", "")
            count = r.get("bad_count", 0)
            fixes.append({
                "severity": "MEDIUM",
                "description": (
                    f"Round numeric columns in `{fname}` — {count} values have floating point artifacts. "
                    f"Apply `.round(2)` to all numeric columns after HSN subtraction/aggregation."
                ),
            })

    # Check 8: UQC
    for r in all_results[7]:
        if r["status"] == "WARN":
            fname = r.get("file", "")
            fixes.append({
                "severity": "MINOR",
                "description": (
                    f"UQC format mismatch in `{fname}` — output uses short codes, template uses long codes. "
                    f"Add UQC mapping: PCS→PCS-PIECE, OTH→OTH-OTHERS, UNT→UNT-UNITS, etc."
                ),
            })

    # Check 9: Completeness
    for r in all_results[8]:
        if r["status"] == "WARN" and r.get("missing"):
            fname = r.get("file", "")
            missing = r["missing"]
            fixes.append({
                "severity": "LOW",
                "description": (
                    f"Incomplete data in `{fname}` — missing entries: {missing[:3]}. "
                    f"For docs: derive invoice series from B2B/CDNR data (min/max number, count per prefix). "
                    f"For eco: need Amazon/Meesho TCS reports as additional input files."
                ),
            })

    # Sort by severity
    severity_order = {"CRITICAL": 0, "MEDIUM": 1, "LOW": 2, "MINOR": 3}
    fixes.sort(key=lambda f: severity_order.get(f["severity"], 9))

    return fixes


# ── Main Orchestrator ─────────────────────────────────────────

def main():
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    template_dir = script_dir / "templates"
    report_path = script_dir / "reports" / "audit_report.md"

    print("=" * 60)
    print("GST OUTPUT AUDIT")
    print("=" * 60)

    # Validate folders
    if not output_dir.exists() or not any(output_dir.glob("*.csv")):
        print(f"\n  ERROR: No CSV files in {output_dir}")
        print("  Copy output files into audit/output/ first.")
        return

    if not template_dir.exists() or not any(template_dir.glob("*.csv")):
        print(f"\n  ERROR: No CSV files in {template_dir}")
        print("  Copy template files into audit/templates/ first.")
        return

    # Match files
    matched, unmatched_tpl = match_files(output_dir, template_dir)
    print(f"\n  Matched: {sum(1 for _, t, _ in matched if t)} file pairs")
    print(f"  Output only: {sum(1 for _, t, _ in matched if t is None)}")
    print(f"  Template only: {len(unmatched_tpl)}")

    # Run checks
    all_results = [[] for _ in range(10)]  # 10 check slots
    file_results = {}

    for out_path, tpl_path, name in matched:
        out_df = pd.read_csv(out_path)
        tpl_df = pd.read_csv(tpl_path) if tpl_path else None

        file_results[name] = {
            "output_rows": len(out_df),
            "template_rows": len(tpl_df) if tpl_df is not None else None,
            "diff": len(out_df) - len(tpl_df) if tpl_df is not None else None,
            "out_df": out_df,
        }

        if tpl_df is None:
            print(f"\n  [{name}] No template match — skipping comparison checks")
            continue

        print(f"\n  [{name}] Running checks...")

        # Check 1: Columns
        r = check_columns(out_df, tpl_df, name)
        r["file"] = name
        all_results[0].append(r)
        print(f"    [1] Columns: {r['status']}")

        # Check 2: Duplicates
        if "b2b" in name and "hsn" not in name:
            r = check_duplicates(out_df, "Invoice Number", name)
            r["file"] = name
            r["key_col"] = "Invoice Number"
            all_results[1].append(r)
            print(f"    [2] Duplicates: {r['status']} — {r['detail']}")
        elif "cdnr" in name:
            r = check_duplicates(out_df, "Note Number", name)
            r["file"] = name
            r["key_col"] = "Note Number"
            all_results[1].append(r)
            print(f"    [2] Duplicates: {r['status']} — {r['detail']}")

        # Check 3: PoS format
        r = check_pos_format(out_df, name)
        r["file"] = name
        all_results[2].append(r)
        if r["status"] != "SKIP":
            print(f"    [3] PoS format: {r['status']}")

        # Check 4: Rates
        r = check_rates(out_df, name)
        r["file"] = name
        all_results[3].append(r)
        if r["status"] != "SKIP":
            print(f"    [4] Rates: {r['status']}")

        # Check 5: Precision
        r = check_precision(out_df, name)
        r["file"] = name
        all_results[4].append(r)
        if r["status"] != "SKIP":
            print(f"    [5] Precision: {r['status']}")

        # Check 6: Row counts
        r = compare_row_counts(out_df, tpl_df, name)
        r["file"] = name
        all_results[5].append(r)
        print(f"    [6] Rows: {r['detail']}")

        # Check 7: Totals
        r = compare_totals(out_df, tpl_df, name)
        r["file"] = name
        all_results[6].append(r)
        if r["status"] != "SKIP":
            print(f"    [7] Totals: {r['detail']}")

        # Check 8: UQC
        if "hsn" in name:
            r = check_uqc(out_df, tpl_df, name)
            r["file"] = name
            all_results[7].append(r)
            print(f"    [8] UQC: {r['status']}")

        # Check 9: Completeness
        if "docs" in name or "eco" in name:
            r = check_completeness(out_df, tpl_df, name)
            r["file"] = name
            all_results[8].append(r)
            print(f"    [9] Completeness: {r['status']}")

        # Check 10: Value comparison
        if "b2b" in name and "hsn" not in name:
            r = compare_values(out_df, tpl_df, "Invoice Number", name)
            r["file"] = name
            r["key_col"] = "Invoice Number"
            all_results[9].append(r)
            print(f"    [10] Values: {r['status']} — {r['detail']}")
        elif "cdnr" in name:
            r = compare_values(out_df, tpl_df, "Note Number", name)
            r["file"] = name
            r["key_col"] = "Note Number"
            all_results[9].append(r)
            print(f"    [10] Values: {r['status']} — {r['detail']}")

    # Generate report
    print(f"\n  Generating report...")
    generate_report(all_results, file_results, output_dir, template_dir,
                    report_path, unmatched_tpl)
    print(f"  Report: {report_path}")

    # Print summary
    total_fail = sum(
        1 for checks in all_results for r in checks if r["status"] == "FAIL"
    )
    total_warn = sum(
        1 for checks in all_results for r in checks if r["status"] == "WARN"
    )
    total_pass = sum(
        1 for checks in all_results for r in checks if r["status"] == "PASS"
    )

    print(f"\n  --- Summary: {total_pass} PASS, {total_fail} FAIL, {total_warn} WARN ---")
    print("=" * 60)


if __name__ == "__main__":
    main()
