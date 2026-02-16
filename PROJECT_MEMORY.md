# GST Automation Project - Complete Reference

## Project Overview
- **Purpose**: GST return automation for multi-state Indian business (14 states)
- **Flow**: Reads data from Flipkart, Amazon, Meesho, E-Invoice Excel files → Generates 7 CSV templates per state for GST portal filing
- **Architecture**: `readers/ → processors/ → generators/` → `output/{state_code}-{State Name}/`
- **Entry point**: `python main.py`
- **Environment**: Python 3.14.3, pandas 3.0.0, openpyxl 3.1.5 (venv/)

---

## Directory Structure
```
GST Project/
├── main.py                      # Full pipeline orchestrator (Phases 1-7)
├── config.json                  # All configuration (file patterns, sheet names, columns)
├── requirements.txt
├── readers/
│   ├── base_reader.py           # Abstract base class (file_paths, config)
│   ├── flipkart_reader.py       # 1 file, 5 sheets (b2c_intra, b2c_inter, hsn, documents, eco)
│   ├── amazon_reader.py         # 14 files, 6 sheets each (b2b, b2c_small, b2c_large, hsn, credit_notes)
│   ├── meesho_reader.py         # 1 file, sheet "80307" (raw transactions)
│   └── einvoice_reader.py       # Dynamic multi-file, keyed by state code
├── processors/
│   ├── hsn_cleaner.py           # Clean HSN codes, fill empty, generate report
│   ├── rate_normalizer.py       # Convert decimal rates (0.05→5, 0.18→18)
│   └── state_detector.py        # Detect 14 states, create folders, GSTIN filtering
├── generators/
│   ├── hsn_generator.py         # hsn(b2b).csv + hsn(b2c).csv per state
│   ├── gstr_b2b_gen.py          # b2b,sez,de.csv per state (with dedup + PoS normalization)
│   ├── gstr_b2cs_gen.py         # b2cs.csv per state
│   ├── creditnotes_gen.py       # cdnr1.csv per state (with dedup + PoS normalization)
│   ├── documents_gen.py         # docs.csv per state (Flipkart + B2B invoice series)
│   └── eco_gen.py               # eco.csv per state
├── validators/
│   └── output_validator.py      # 7 validation checks + validation_report.csv
├── utils/
│   └── file_discovery.py        # Auto-discover input files, load config
├── audit/                       # Standalone backtest audit tool
│   ├── run_audit.py             # 10 checks, generates markdown report
│   ├── templates/               # User puts previous month's actual filed CSVs here
│   ├── output/                  # User puts generated output CSVs to test here
│   └── reports/
│       └── audit_report.md      # Auto-generated after each run
├── portal/                      # Web portal (System B)
│   ├── backend/                 # FastAPI + SQLite
│   │   ├── run.py               # Entry point: uvicorn app.main:app
│   │   ├── requirements.txt     # fastapi, uvicorn, sqlalchemy, etc.
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI app, CORS, routers
│   │   │   ├── config.py        # Settings, project paths
│   │   │   ├── database.py      # SQLAlchemy + SQLite
│   │   │   ├── models/          # GSTIN, FilingSession, UploadLog
│   │   │   ├── schemas/         # Pydantic request/response schemas
│   │   │   ├── routes/
│   │   │   │   ├── gstins.py    # CRUD for GSTINs
│   │   │   │   ├── upload.py    # File upload + platform detection
│   │   │   │   ├── processing.py # Trigger pipeline, track sessions
│   │   │   │   └── results.py   # Browse states, preview CSV, download
│   │   │   └── services/
│   │   │       └── processing_bridge.py  # Imports System A, runs pipeline
│   │   ├── data/uploads/        # Uploaded files storage
│   │   ├── data/db/             # SQLite database
│   │   └── venv/                # Separate venv (FastAPI + pandas)
│   └── frontend/                # React + Vite + TypeScript + Tailwind
│       ├── src/
│       │   ├── App.tsx          # Router setup (4 routes)
│       │   ├── main.tsx         # Entry point
│       │   ├── lib/api.ts       # API client (all endpoints typed)
│       │   ├── components/
│       │   │   ├── Layout.tsx   # Sidebar + main content area
│       │   │   └── Sidebar.tsx  # Navigation sidebar
│       │   └── pages/
│       │       ├── Dashboard.tsx  # Stats + quick start
│       │       ├── GSTINs.tsx     # Add/toggle/delete GSTINs
│       │       ├── Upload.tsx     # Drag-drop upload + run pipeline
│       │       └── Review.tsx     # State tree + CSV table preview + download
│       └── node_modules/
├── Input files/                 # 17 source Excel files
├── Template files/              # 7 reference CSVs (exact GST portal format)
├── output/                      # Generated output per state
│   ├── 03-Punjab/
│   ├── 06-Haryana/
│   ├── 07-Delhi/                # Has all 7 CSVs (only state with E-Invoice + all platforms)
│   ├── 09-Uttar Pradesh/
│   ├── ... (14 states total)
│   └── validation_report.csv
└── claude_instructions/         # OLD docs (reference only, WRONG filenames)
```

---

## Input Files (17 total)
| Platform | Files | Key Details |
|----------|-------|-------------|
| Flipkart | `Flipkart_raw_gst_report_2.xlsx` (1 file) | 7 GSTINs, header row 1, 5 sheets |
| Amazon | `GSTR1-JANUARY-2026-A3SZBDZ05A1P39-*.xlsx` (14 files) | 1 per state, header=3 (skip 3 summary rows) |
| Meesho | `Meesho_gst_report.xlsx` (1 file) | GSTIN 07-Delhi only, sheet "80307" |
| E-Invoice | `EINV_<GSTIN>_<YEAR>.xlsx` (1 file currently) | Delhi only, header=3, dynamic multi-file |

---

## 14 Seller States
03-Punjab, 06-Haryana, 07-Delhi, 09-UP, 10-Bihar, 18-Assam, 19-West Bengal, 21-Odisha, 23-MP, 24-Gujarat, 27-Maharashtra, 29-Karnataka, 33-Tamil Nadu, 36-Telangana

---

## 7 Output Templates Per State

### 1. `hsn(b2b).csv` — HSN B2B (E-Invoice states only)
- **Source**: E-Invoice `hsn(b2b)` sheet directly
- **Columns (11)**: HSN, Description, UQC, Total Quantity, Total Value, Taxable Value, Integrated Tax Amount, Central Tax Amount, State/UT Tax Amount, Cess Amount, Rate
- **Generator**: `generators/hsn_generator.py`

### 2. `hsn(b2c).csv` — HSN B2C
- **Source**: Total HSN (Amazon + Flipkart + Meesho) MINUS E-Invoice HSN B2B
- **Columns (11)**: Same as hsn(b2b)
- **Logic**: Match on HSN+Rate, subtract numeric columns, round to 2 decimal places. States without E-Invoice: all HSN → B2C
- **UQC**: Converted to long format (PCS→PCS-PIECES, OTH→OTH-OTHERS, etc.)

### 3. `b2b,sez,de.csv` — B2B Invoices
- **Source**: Amazon B2B + E-Invoice B2B (`b2b, sez, de` sheet)
- **Columns (13)**: GSTIN/UIN of Recipient, Receiver Name, Invoice Number, Invoice date, Invoice Value, Place Of Supply, Reverse Charge, Applicable % of Tax Rate, Invoice Type, E-Commerce GSTIN, Rate, Taxable Value, Cess Amount
- **Generator**: `generators/gstr_b2b_gen.py`
- **Dedup**: By Invoice Number — keep E-Invoice version (has Receiver Name), drop Amazon duplicate
- **PoS normalization**: `re.sub(r'(\d{2})\s*-\s*', r'\1-', pos)` strips spaces around dash
- **Returns**: `b2b_by_state` dict for use by documents generator

### 4. `b2cs.csv` — B2C Supplies (aggregated)
- **Source**: Flipkart B2C intra (7A) + inter (7B) + Amazon B2C Small + B2C Large + Meesho raw
- **Columns (6)**: Type, Place Of Supply, Rate, Applicable % of Tax Rate, Taxable Value, Cess Amount
- **Generator**: `generators/gstr_b2cs_gen.py`
- **Logic**: Combine all B2C sources, normalize Place Of Supply, normalize rates to integers, aggregate by (Place Of Supply, Rate)

### 5. `cdnr1.csv` — Credit/Debit Notes
- **Source**: Amazon `B2B CN (cdnr)` sheet + E-Invoice `cdnr` sheet
- **Columns (13)**: GSTIN/UIN of Recipient, Receiver Name, Note Number, Note Date, Note Type, Place Of Supply, Reverse Charge, Note Supply Type, Note Value, Applicable % of Tax Rate, Rate, Taxable Value, Cess Amount
- **Generator**: `generators/creditnotes_gen.py`
- **Dedup**: By Note Number — keep E-Invoice version, drop Amazon duplicate
- **PoS normalization**: Same as B2B

### 6. `docs.csv` — Document Series
- **Source**: Flipkart Section 13 + derived invoice series from B2B data
- **Columns (5)**: Nature of Document, Sr. No. From, Sr. No. To, Total Number, Cancelled
- **Generator**: `generators/documents_gen.py`
- **Logic**: Flipkart docs + `_derive_invoice_series(b2b_df)` extracts series by prefix (IN-, KNYT-, LE/, etc.), computes min/max/count. Skips series already covered by Flipkart.

### 7. `eco.csv` — E-Commerce Operator
- **Source**: Flipkart Section 3 (GSTR-8) only
- **Columns (8)**: Nature of Supply, GSTIN of E-Commerce Operator, E-Commerce Operator Name, Net value of supplies, Integrated tax, Central tax, State/UT tax, Cess
- **Generator**: `generators/eco_gen.py`

---

## Source Column Names (Actual from Excel files)

### Amazon (header=3)
- **B2B**: GSTIN/UIN of Recipient, Receiver Name, Invoice Number, Invoice date, Invoice Value, Place Of Supply, Reverse Charge, Applicable % of Tax Rate, Invoice Type, E-Commerce GSTIN, Rate, Taxable Value, Cess Amount *(+ source_gstin added by reader)*
- **B2C Small**: Type, Place Of Supply, Applicable % of Tax Rate, Rate, Taxable Value, Cess Amount, E-Commerce GSTIN *(+ source_gstin)*
- **B2C Large**: Invoice Number, Invoice date, Invoice Value, Place Of Supply, Applicable % of Tax Rate, Rate, Taxable Value, Cess Amount, E-Commerce GSTIN *(+ source_gstin)*
- **B2B CN (cdnr)**: GSTIN/UIN of Recipient, Receiver Name, Note Number, Note Date, Note Type, Place Of Supply, Reverse Charge, Note Supply Type, Note Value, Applicable % of Tax Rate, Rate, Taxable Value, Cess Amount, Invoice/Advance Receipt Number, Invoice/Advance Receipt Date, Reason for Issuing Document *(+ source_gstin)*
- **HSN Summary**: HSN, Description, UQC, Total Quantity, Total Value, Taxable Value, Integrated Tax Amount, Central Tax Amount, State/UT Tax Amount, Cess Amount, Rate *(+ source_file, source_gstin)*
- **Sheet names in file**: GSTIN, B2B, B2B CN (cdnr), B2CL CN (cdnur), B2C Large, B2C Small, HSN Summary

### E-Invoice (header=3)
- **b2b, sez, de**: GSTIN/UIN of Recipient, Receiver Name, Invoice number, Invoice date, Invoice value, Place of Supply, Reverse Charge, Applicable % of Tax Rate, Invoice Type, E-Commerce GSTIN, Rate, Taxable Value, Integrated Tax, Central Tax, State/UT Tax, Cess Amount, IRN, IRN date, E-invoice status, ...
- **cdnr**: GSTIN/UIN of Recipient, Receiver Name, Note Number, Note Date, Note Type, Place of Supply, Reverse Charge, Note Supply Type, Note value, Applicable % of Tax Rate, Rate, Taxable Value, Integrated Tax, Central Tax, State/UT Tax, Cess Amount, IRN, ...
- **hsn(b2b)**: HSN, Description, UQC, Total Quantity, Total taxable value, Rate (%), Integrated tax, Central tax, State/UT tax, Cess

### Flipkart (header=1)
- **Section 7(A)(2) — B2C Intra**: GSTIN, Gross Taxable Value Rs., Taxable Sales Return Value Rs., Aggregate Taxable Value Rs., CGST %, CGST Amount Rs., SGST/UT %, SGST /UT Amount Rs., Cess %, CESS Amount Rs.
- **Section 7(B)(2) — B2C Inter**: GSTIN, Gross Taxable Value Rs., Taxable Sales Return Value Rs., Aggregate Taxable Value Rs., IGST %, IGST Amount Rs., Cess %, CESS Amount Rs., Delivered State (PoS), Delivered State Code
- **Section 12 — HSN**: GSTIN, HSN Number, Total Quantity in Nos., Total\n Value Rs., Total Taxable Value Rs., IGST Amount Rs., CGST Amount Rs., SGST Amount Rs., Cess Rs.
- **Section 13 — Documents**: GSTIN, Invoice Series From, Invoice Series \nTo, Total Number of Invoices, Cancelled if any, Net invoices Issued
- **Section 3 — ECO**: GSTIN, Seller ID issued by Flipkart.Com, GSTIN of Flipkart.Com, Gross Taxable Value Rs., Taxable Sales Return Value Rs., Net Taxable Value, TCS %, TCS IGST amount Rs., TCS CGST amount Rs., TCS SGST amount Rs., IGST Amount Rs., CGST Amount Rs., SGST Amount Rs., Invoice Qty\n(Net)

### Meesho (sheet "80307")
- Key columns (from config): hsn_code, gst_rate, total_taxable_sale_value, tax_amount, total_invoice_value, taxable_shipping, end_customer_state_new, quantity, gstin, order_date, sub_order_num

---

## Config (config.json) Key Sections
- `project`: month="January", year="2026"
- `file_patterns`: glob patterns for auto-discovery (skips `~$` temp files)
- `flipkart_sheets`, `amazon_sheets`, `meesho_sheets`, `einvoice_sheets`: sheet name mappings
- `meesho_columns`: column name mappings for Meesho raw data
- `empty_hsn_fill_map`: `{"5": "90211000", "18": "95069990"}`
- `output_templates`: column definitions for each output template

---

## Key Processing Rules
- **ALL rates must be integers** (5, 12, 18) — never decimals (0.05, 0.18)
- **Zero empty files policy**: only generate CSVs for states that have data
- **Amazon `source_gstin`**: added to ALL sheet types for per-state filtering (extracted from filename)
- **Flipkart B2C Inter state mapping**: `Delivered State (PoS)` is plain name → mapped via MEESHO_STATE_MAP (uppercase lookup) + extra entries for "ODISHA", "JAMMU AND KASHMIR"
- **Place Of Supply normalization in B2CS**: Amazon uses "&" (Jammu & Kashmir), Flipkart uses "and" → normalize by extracting state code and rebuilding from STATE_CODE_MAP
- **Meesho states**: normalized from plain uppercase ("DELHI") to GST format ("07-Delhi") via MEESHO_STATE_MAP
- **E-Invoice is dynamic**: add more EINV_*.xlsx files → auto-detected and keyed by state code

---

## Phase Status
- **Phase 1-4: COMPLETE** — File discovery, 4 readers, 3 processors, state detection
- **Phase 5: COMPLETE** — All 7 generators + main.py orchestrator
- **Phase 6: COMPLETE** — Validation & Reconciliation (`validators/output_validator.py`)
  - 7 automated checks: column headers, rate integrity, B2B row counts (dedup-aware), CN row counts (dedup-aware), HSN balance, no empty files, GSTIN format
  - Last run: 155 PASS, 0 FAIL, 0 WARN
  - Generates `output/validation_report.csv`
- **Phase 7: COMPLETE** — Bug fixes applied and verified
  - B2B/CDNR dedup by Invoice/Note Number (keep E-Invoice version)
  - PoS normalization (`23 - MP` → `23-MP`) in B2B + CDNR
  - HSN B2C rounding (`.round(2)` after subtraction)
  - Docs completion (derive invoice series from B2B data)
  - UQC long format mapping (PCS→PCS-PIECES, etc.)
  - Validator updated (checks dedup correctness, not raw row count match)
  - Audit results after fixes: 26 PASS, 3 FAIL, 1 WARN (from 18/8/4)
- **Portal Phase 0: COMPLETE** — .gitignore, portal skeleton
- **Portal Phase 1: COMPLETE** — FastAPI backend (config, database, models, routes, processing bridge)
- **Portal Phase 2: COMPLETE** — React frontend (Vite+TS+Tailwind, 4 pages: Dashboard, GSTINs, Upload, Review)
- **Portal Phase 3B: COMPLETE** — Processing bridge wired to frontend, both servers verified working

---

## Portal API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + project root |
| GET | `/api/gstins/` | List all GSTINs |
| POST | `/api/gstins/` | Add GSTIN (auto-detect state) |
| PUT | `/api/gstins/{id}` | Toggle active/inactive |
| DELETE | `/api/gstins/{id}` | Delete GSTIN |
| POST | `/api/upload/` | Upload Excel file (multipart, auto-detect platform) |
| GET | `/api/upload/` | List uploaded files |
| DELETE | `/api/upload/{id}` | Delete uploaded file |
| POST | `/api/processing/run` | Run pipeline (month + year) |
| GET | `/api/processing/status/{id}` | Get session status |
| GET | `/api/processing/history` | List all sessions |
| GET | `/api/results/{id}/states` | List states with output |
| GET | `/api/results/{id}/states/{code}/files/{name}` | CSV as JSON |
| GET | `/api/results/{id}/states/{code}/files/{name}/download` | Download CSV |

---

## Output Summary (After Bug Fixes)
| Template | States | Example (Delhi) |
|----------|--------|-----------------|
| hsn(b2b) | 1 (Delhi) | 88 rows |
| hsn(b2c) | 14 | 125 rows |
| b2b,sez,de | 14 | 143 rows (deduped from 274) |
| b2cs | 14 | 78 rows |
| cdnr1 | 11 | 18 rows (deduped from 34) |
| docs | 14 | 7 rows (Delhi, up from 1) |
| eco | 7 | 1 row |

---

## GST Backtest Audit Tool (`audit/`)

### Overview
Standalone script that compares generated output CSVs against previous month's actual template CSVs.
- **Script**: `audit/run_audit.py` — single file, only needs pandas, no imports from main project
- **Report output**: `audit/reports/audit_report.md` — designed for Claude consumption

### Usage
```
1. Copy previous month's CSVs → audit/templates/
2. Copy generated output CSVs → audit/output/
3. Run: python audit/run_audit.py
4. Read: audit/reports/audit_report.md
```

### 10 Automated Checks
| # | Check | Applies To | What It Does |
|---|-------|------------|--------------|
| 1 | Column Headers | All 7 files | Exact ordered column name comparison |
| 2 | Duplicate Invoices/Notes | b2b, cdnr | Groups by Invoice/Note Number, flags >1 occurrence |
| 3 | Place Of Supply Format | b2b, b2cs, cdnr | Detects mixed `XX-Name` vs `XX - Name` formats |
| 4 | Rate Integrity | All with Rate col | Checks values are standard integers (0, 5, 12, 18, 28) |
| 5 | Floating Point Precision | All numeric cols | Flags values with >2 decimal places |
| 6 | Row Count Comparison | All 7 files | Output rows vs template rows, shows diff |
| 7 | Taxable Value Totals | All with Taxable Value | Sum comparison, shows absolute diff and % change |
| 8 | UQC Format | HSN files | Detects short codes (PCS) vs long codes (PCS-PIECES) |
| 9 | Data Completeness | docs, eco | Docs: compares invoice series prefixes. Eco: compares operator GSTINs |
| 10 | Value-Level Comparison | b2b, cdnr | Matches by Invoice/Note Number, compares Taxable Value (±1.0 tolerance) |

### Delhi Audit Results After Bug Fixes
**Summary: 26 PASS, 3 FAIL, 1 WARN** (improved from 18 PASS, 8 FAIL, 4 WARN)
- All CRITICAL issues fixed (duplicates, PoS, precision, UQC, docs)
- Remaining 3 FAIL = cross-month data differences (different invoices between Jan vs Dec)
- Remaining 1 WARN = ECO missing Amazon/Meesho TCS data (not in input files)

---

## Next Steps (Approved Enhancement Plan)

### Feature 1: Git Commit
- Add `.claude/` to .gitignore, commit all existing work

### Feature 2: CSV → GSTR-1 JSON Converter
- New file: `generators/json_converter.py`
- Reads 7 CSV files per state → `gstr1.json` per state matching GSTN API schema
- JSON sections: b2b (grouped by ctin→inv→itms), b2cs, cdnr, hsn, doc_issue
- Tax split logic: inter-state `iamt=txval*rt/100`, intra-state `camt=samt=txval*rt/200`
- Invoice Type: "Regular B2B"→"R", "SEZ with payment"→"SEWP", "Deemed Exports"→"DE"
- Date: DD-Mon-YYYY → DD-MM-YYYY
- ECO skipped (GSTR-8, not GSTR-1)
- Integration: main.py Phase 8 + processing bridge

### Feature 3: Enhanced Review Page
- Backend: GET /api/results/{id}/validation, GET .../json, GET .../json/download
- Frontend: Validation summary panel, tab system (CSV | JSON | Validation), JSON preview

### Feature 4: Audit Integration in Portal
- Backend: POST /api/audit/upload-templates, POST /api/audit/run, GET /api/audit/report
- Frontend: Audit page with template upload, state selector, run button, report display
- Dependency: react-markdown for report rendering

### Feature 5: Multi-month Support
- Output to `output/{MM}_{YYYY}/` instead of flat `output/`
- Session-specific uploads: `data/uploads/{session_id}/`
- `file_discovery.py` gets `input_override` parameter
- CLI `main.py` unchanged (backward compatible)

---

## Environment Notes
- **Node.js**: v24.13.1, npm 11.8.0, at `C:\Program Files\nodejs`
- **Bash PATH**: `export PATH="/c/Program Files/nodejs:$PATH"`
- **PowerShell**: Use `;` not `&&` for chaining commands
- **Main venv**: `./venv/Scripts/python` (Python 3.14.3, pandas 3.0.0)
- **Portal venv**: `./portal/backend/venv/Scripts/python` (FastAPI 0.129, SQLAlchemy 2.0)
- **Start backend**: `cd portal/backend; .\venv\Scripts\python run.py` (PowerShell)
- **Start frontend**: `cd portal/frontend; npm run dev` (PowerShell)
