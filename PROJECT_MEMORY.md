# GST Automation Project - Complete Reference

## Project Overview
- **Purpose**: GST return automation for multi-state Indian business (14 states)
- **Flow**: Reads data from Flipkart, Amazon, Meesho, E-Invoice Excel files → Generates 7 CSV templates + gstr1.json per state for GST portal filing
- **Architecture**: `readers/ → processors/ → generators/ → json_converter` → `output/{state_code}-{State Name}/`
- **Entry point**: `python main.py` (CLI) or portal at localhost:5173
- **Environment**: Python 3.14.3, pandas 3.0.0, openpyxl 3.1.5 (venv/)

---

## Directory Structure
```
GST Project/
├── main.py                      # Full pipeline orchestrator (Phases 1-8)
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
│   ├── eco_gen.py               # eco.csv per state
│   └── json_converter.py        # CSV → GSTN-compliant gstr1.json per state
├── validators/
│   └── output_validator.py      # 7 validation checks + validation_report.csv
├── utils/
│   └── file_discovery.py        # Auto-discover input files, load config (supports input_override)
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
│   │   │   ├── main.py          # FastAPI app, CORS, 5 routers
│   │   │   ├── config.py        # Settings, project paths
│   │   │   ├── database.py      # SQLAlchemy + SQLite
│   │   │   ├── models/          # GSTIN, FilingSession, UploadLog
│   │   │   ├── schemas/         # Pydantic request/response schemas
│   │   │   ├── routes/
│   │   │   │   ├── gstins.py    # CRUD for GSTINs
│   │   │   │   ├── upload.py    # File upload + platform detection
│   │   │   │   ├── processing.py # Trigger pipeline (multi-month), track sessions
│   │   │   │   ├── results.py   # Browse states, CSV/JSON preview, validation, download
│   │   │   │   └── audit.py     # Upload templates, run audit, view report
│   │   │   └── services/
│   │   │       └── processing_bridge.py  # Imports System A, runs pipeline (multi-month)
│   │   ├── data/uploads/        # Uploaded files storage
│   │   ├── data/db/             # SQLite database
│   │   └── venv/                # Separate venv (FastAPI + pandas)
│   └── frontend/                # React + Vite + TypeScript + Tailwind
│       ├── src/
│       │   ├── App.tsx          # Router setup (5 routes)
│       │   ├── main.tsx         # Entry point
│       │   ├── lib/api.ts       # API client (all endpoints typed)
│       │   ├── components/
│       │   │   ├── Layout.tsx   # Sidebar + main content area
│       │   │   └── Sidebar.tsx  # Navigation sidebar (5 active + 2 disabled)
│       │   └── pages/
│       │       ├── Dashboard.tsx  # Stats + analytics + quick start (enhanced with Tailwind v4)
│       │       ├── GSTINs.tsx     # Add/toggle/delete GSTINs
│       │       ├── Upload.tsx     # Drag-drop upload + run pipeline
│       │       ├── Review.tsx     # 3 tabs: CSV Data, JSON Preview, Validation Details
│       │       └── Audit.tsx      # Upload templates, run audit, view report
│       └── node_modules/
├── Input files/                 # 17 source Excel files
├── Template files/              # 7 reference CSVs (exact GST portal format)
├── output/                      # Generated output per state (CLI)
│   ├── {MM}_{YYYY}/            # Multi-month output (Portal)
│   │   ├── 03-Punjab/
│   │   ├── 07-Delhi/           # Has all 8 files (7 CSVs + gstr1.json)
│   │   └── ...
│   ├── 03-Punjab/              # Direct output (CLI)
│   ├── 07-Delhi/
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

## 8 Output Files Per State

### 1-7: CSV Templates (same as before)
1. `hsn(b2b).csv` — HSN B2B (E-Invoice states only, 11 columns)
2. `hsn(b2c).csv` — HSN B2C (Total HSN minus E-Invoice HSN B2B, 11 columns)
3. `b2b,sez,de.csv` — B2B Invoices (Amazon + E-Invoice, deduped, 13 columns)
4. `b2cs.csv` — B2C Supplies aggregated (6 columns)
5. `cdnr1.csv` — Credit/Debit Notes (Amazon + E-Invoice, deduped, 13 columns)
6. `docs.csv` — Document Series (Flipkart + derived from B2B, 5 columns)
7. `eco.csv` — E-Commerce Operator (Flipkart only, 8 columns)

### 8: `gstr1.json` — GSTN-compliant JSON
- **Generator**: `generators/json_converter.py`
- **Sections**: b2b (grouped ctin→inv→itms), b2cs (sply_ty INTRA/INTER), cdnr, hsn, doc_issue
- **Tax split**: inter-state `iamt=txval*rt/100`, intra-state `camt=samt=txval*rt/200`
- **Invoice Type codes**: "Regular B2B"→"R", "SEZ with payment"→"SEWP", "Deemed Exp"→"DE"
- **Date format**: DD-Mon-YYYY → DD-MM-YYYY
- **Filing period**: MMYYYY from config (e.g. "012026")
- **ECO**: skipped (GSTR-8, not GSTR-1)
- **Entry points**: `generate_all_json(folders, states_dict, config)` or `generate_json_for_state(folder, gstin, fp, state_code)`

---

## Phase Status — ALL COMPLETE
- **Phases 1-4**: File discovery, readers, processors, state detection
- **Phase 5**: 7 CSV generators + main.py orchestrator
- **Phase 6**: Validation (155 PASS, 0 FAIL, 0 WARN)
- **Phase 7**: Bug fixes (dedup, PoS normalization, HSN rounding, UQC, docs)
- **Portal Phases 0-3B**: Backend + frontend + processing bridge
- **Feature 1**: Git commit (`6573656`, 81 files) — git user: yashvibercoder <guptayash369@gmail.com>
- **Feature 2**: JSON converter — 14 gstr1.json files generated
- **Feature 3**: Enhanced Review page (3 tabs: CSV Data, JSON Preview, Validation Details)
- **Feature 4**: Audit integration in portal (template upload, run, report)
- **Feature 5**: Multi-month support (output/{MM}_{YYYY}/, session-specific uploads)
- **Feature 6**: Dashboard enhancement — visual polish (Tailwind v4 theme tokens, card transitions, gradient backgrounds) + analytics (tax liability summary, rate distribution bar, state-wise breakdown table, validation banner)

## Related Files
- [skills.md](skills.md) — Claude Code skills catalog, recommendations, and usage history

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
| POST | `/api/processing/run` | Run pipeline (month + year → output/{MM}_{YYYY}/) |
| GET | `/api/processing/status/{id}` | Get session status |
| GET | `/api/processing/history` | List all sessions |
| GET | `/api/results/{id}/states` | List states with output (includes json_files) |
| GET | `/api/results/{id}/states/{code}/files/{name}` | CSV as JSON |
| GET | `/api/results/{id}/states/{code}/files/{name}/download` | Download CSV |
| GET | `/api/results/{id}/validation` | Validation report as structured JSON |
| GET | `/api/results/{id}/states/{code}/json` | gstr1.json content |
| GET | `/api/results/{id}/states/{code}/json/download` | Download gstr1.json |
| GET | `/api/results/{id}/analytics` | Aggregated tax analytics (state-wise + rate breakdown) |
| POST | `/api/audit/upload-templates` | Upload previous month's CSVs |
| GET | `/api/audit/templates` | List uploaded templates |
| DELETE | `/api/audit/templates` | Clear all templates |
| POST | `/api/audit/run?state_code=07` | Run audit for a state |
| GET | `/api/audit/report` | Get audit report markdown |

---

## Key Processing Rules
- **ALL rates must be integers** (5, 12, 18) — never decimals (0.05, 0.18)
- **Zero empty files policy**: only generate CSVs for states that have data
- **Dedup**: B2B/CDNR by Invoice/Note Number — keep E-Invoice version (has Receiver Name)
- **PoS normalization**: `re.sub(r'(\d{2})\s*-\s*', r'\1-', pos)` in B2B + CDNR
- **HSN rounding**: `.round(2)` after B2B subtraction
- **UQC**: 47-entry map to long format (PCS→PCS-PIECES, etc.)
- **E-Invoice is dynamic**: add more EINV_*.xlsx files → auto-detected per state

---

## GST Backtest Audit Tool (`audit/`)
- **Script**: `audit/run_audit.py` — standalone, only needs pandas
- **10 checks**: headers, dupes, PoS, rates, precision, rows, totals, UQC, completeness, values
- **Portal integration**: `portal/backend/app/routes/audit.py` (5 endpoints)
- **Delhi results after fixes**: 26 PASS, 3 FAIL, 1 WARN

---

## Environment Notes
- **Git**: user yashvibercoder <guptayash369@gmail.com> (repo-local config)
- **Node.js**: v24.13.1, npm 11.8.0, at `C:\Program Files\nodejs`
- **Bash PATH**: `export PATH="/c/Program Files/nodejs:$PATH"`
- **PowerShell**: Use `;` not `&&` for chaining commands
- **Main venv**: `./venv/Scripts/python` (Python 3.14.3, pandas 3.0.0)
- **Portal venv**: `./portal/backend/venv/Scripts/python` (FastAPI 0.129, SQLAlchemy 2.0)
- **Start backend**: `cd portal/backend; .\venv\Scripts\python run.py` (PowerShell)
- **Start frontend**: `cd portal/frontend; npm run dev` (PowerShell)
