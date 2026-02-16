# GST Automation - Standard Operating Procedure

## 1. Prerequisites

### Software Required
- **Python 3.10 or higher** (tested on Python 3.14.3)
- No other software needed — all dependencies are Python packages

### Python Packages (installed automatically)
| Package | Purpose |
|---------|---------|
| pandas | Data processing (DataFrames, CSV generation) |
| openpyxl | Reading Excel (.xlsx) files |

---

## 2. First-Time Setup (New System)

### Step 1: Install Python
- Download from https://python.org
- During install, check **"Add Python to PATH"**
- Verify: open terminal and run `python --version`

### Step 2: Copy the Project
Copy the entire `GST Project` folder to the new system. The folder structure must be preserved:
```
GST Project/
├── main.py
├── config.json
├── requirements.txt
├── readers/
├── processors/
├── generators/
├── validators/
├── utils/
├── Input files/        <-- put your Excel files here
├── Template files/     <-- reference templates (do not modify)
└── output/             <-- generated automatically
```

### Step 3: Create Virtual Environment & Install Dependencies

**Windows:**
```
cd "GST Project"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Mac/Linux:**
```
cd "GST Project"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Input File Naming & Placement

### Where to Put Files
All input Excel files go in the **`Input files/`** folder inside the project.

### File Naming Rules
Files are auto-detected by their names. The filename must contain the keyword shown below:

| Platform | Keyword in Filename | Format | Example |
|----------|-------------------|--------|---------|
| Flipkart | `Flipkart` | Any name with "Flipkart" | `Flipkart_raw_gst_report_2.xlsx` |
| Amazon | `A3SZBDZ05A1P39` | GSTIN appended after seller ID | `GSTR1-JANUARY-2026-A3SZBDZ05A1P39-07IFWPS9148C1ZK.xlsx` |
| Meesho | `Meesho` | Any name with "Meesho" | `Meesho_gst_report.xlsx` |
| E-Invoice | `EINV` | `EINV_<GSTIN>_<YEAR>.xlsx` | `EINV_07IFWPS9148C1ZK_2025-26.xlsx` |

### Platform-Specific Details

**Flipkart:**
- 1 file total (contains all GSTINs/states inside)
- Must have the word "Flipkart" anywhere in the filename
- Must be `.xlsx` format
- Required sheets: `Section 7(A)(2) in GSTR-1`, `Section 7(B)(2) in GSTR-1`, `Section 12 in GSTR-1`, `Section 13 in GSTR-1`, `Section 3 in GSTR-8`

**Amazon:**
- 1 file per state (14 files if selling in all 14 states)
- Must have `A3SZBDZ05A1P39` (your Amazon seller ID) in the filename
- The state GSTIN must appear after `A3SZBDZ05A1P39-` in the filename (e.g., `-07IFWPS9148C1ZK.xlsx`)
- Must be `.xlsx` format
- Required sheets: `B2B`, `B2C Small`, `B2C Large`, `HSN Summary`, `B2B CN (cdnr)`

**Meesho:**
- 1 file total
- Must have the word "Meesho" anywhere in the filename
- Must be `.xlsx` format
- Required sheet: `80307`
- Currently linked to Delhi (07) GSTIN only

**E-Invoice:**
- 1 file per state that has E-Invoice data
- Must have `EINV` in the filename
- Format: `EINV_<15-digit-GSTIN>_<financial-year>.xlsx`
- The GSTIN is extracted from between the underscores (first 2 digits = state code)
- Must be `.xlsx` format
- Required sheets: `b2b, sez, de`, `cdnr`, `hsn(b2b)`
- Optional: add more E-Invoice files for more states — they are auto-detected

### Important Notes
- Close Excel before running (open Excel files create `~$` temp files that are auto-skipped)
- Only `.xlsx` format is supported (not `.xls` or `.csv`)
- Files can have any prefix/suffix as long as the keyword is present

---

## 4. How to Run

### Quick Steps
1. Place all input Excel files in the `Input files/` folder
2. Close Excel (to avoid temp file issues)
3. Open terminal/command prompt in the project folder
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
5. Run: `python main.py`
6. Wait for it to complete (takes a few seconds)

### What You'll See
The pipeline runs through 7 phases:
```
PHASE 1: FILE DISCOVERY       — Lists all detected input files
PHASE 2: DATA LOADING         — Reads Flipkart, Amazon, Meesho, E-Invoice
PHASE 3: DATA NORMALIZATION   — Cleans HSN codes, normalizes rates
PHASE 4: STATE DETECTION      — Identifies your 14 seller states
PHASE 5: OUTPUT STRUCTURE     — Creates per-state output folders
PHASE 6: TEMPLATE GENERATION  — Generates 7 CSV templates per state
PHASE 7: VALIDATION           — Cross-checks everything (should show ALL PASS)
```

### Success Looks Like
```
COMPLETE
  Output: ...\output
  States: 14
  Templates: hsn(b2b), hsn(b2c), b2b, b2cs, cdnr1, docs, eco
  Validation: ALL PASS
```

---

## 5. Output

### Folder Structure
```
output/
├── 03-Punjab/
│   ├── b2b,sez,de.csv
│   ├── b2cs.csv
│   ├── cdnr1.csv
│   └── hsn(b2c).csv
├── 06-Haryana/
│   ├── b2b,sez,de.csv
│   ├── b2cs.csv
│   ├── cdnr1.csv
│   ├── docs.csv
│   ├── eco.csv
│   └── hsn(b2c).csv
├── 07-Delhi/                  <-- Most complete (has E-Invoice)
│   ├── b2b,sez,de.csv
│   ├── b2cs.csv
│   ├── cdnr1.csv
│   ├── docs.csv
│   ├── eco.csv
│   ├── hsn(b2b).csv          <-- Only for E-Invoice states
│   └── hsn(b2c).csv
├── ... (other states)
├── empty_hsn_report.csv       <-- Lists rows with missing HSN codes
└── validation_report.csv      <-- Summary of all generated files
```

### What Each File Is For
| File | GST Portal Section | Upload To |
|------|-------------------|-----------|
| `b2b,sez,de.csv` | B2B Invoices | GSTR-1 → B2B |
| `b2cs.csv` | B2C Small Supplies | GSTR-1 → B2C (Others) |
| `cdnr1.csv` | Credit/Debit Notes | GSTR-1 → CDNR |
| `hsn(b2b).csv` | HSN Summary (B2B) | GSTR-1 → HSN |
| `hsn(b2c).csv` | HSN Summary (B2C) | GSTR-1 → HSN |
| `docs.csv` | Document Summary | GSTR-1 → Documents |
| `eco.csv` | E-Commerce Operator | GSTR-1 → ECO |

### Not Every State Gets All 7 Files
- `hsn(b2b).csv` — only states with E-Invoice data (currently Delhi only)
- `docs.csv` — only states that sell on Flipkart
- `eco.csv` — only states that sell on Flipkart
- `cdnr1.csv` — only states with credit notes

---

## 6. Updating for a New Month

1. Download fresh reports from Flipkart, Amazon, Meesho, E-Invoice portal
2. Replace the old files in `Input files/` with new ones (same naming convention)
3. Open `config.json` and update:
   ```json
   "project": {
       "month": "February",
       "year": "2026",
       "month_short": "Feb"
   }
   ```
4. Run `python main.py`
5. Old output is overwritten automatically

---

## 7. Troubleshooting

| Problem | Solution |
|---------|----------|
| "No Flipkart files found" | Check filename contains "Flipkart" and file is in `Input files/` |
| "No Amazon files found" | Check filename contains "A3SZBDZ05A1P39" |
| "No Meesho files found" | Check filename contains "Meesho" |
| "No E-Invoice files found" | Check filename contains "EINV" |
| Validation shows FAIL | Read the console output — it says exactly what's wrong |
| `ModuleNotFoundError` | Make sure venv is activated (`venv\Scripts\activate`) |
| `pip install` fails | Try `python -m pip install -r requirements.txt` |
| Wrong state count | Check Amazon filenames have correct GSTINs after the seller ID |
| Excel temp file warnings | Close Excel before running the tool |
| Empty output for a state | That state has no data in the input files — this is normal |
