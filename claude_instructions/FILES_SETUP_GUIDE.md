# FILE-BY-FILE SETUP GUIDE FOR VISUAL STUDIO CODE

This guide shows exactly what to copy where.

---

## STEP 1: COPY THE MAIN ORCHESTRATOR

**From:** Python code below
**To:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\main.py`

Already created - see main.py in the outputs folder

---

## STEP 2: COPY CONFIGURATION FILE

**From:** JSON code below
**To:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\config.json`

Already created - see config.json in the outputs folder

---

## STEP 3: CREATE READERS FOLDER STRUCTURE

### File 1: readers/__init__.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\readers\__init__.py`
**Content:**
```python
# Readers package
```

### File 2: readers/base_reader.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\readers\base_reader.py`

Already created - see base_reader.py in outputs

---

## STEP 4: CREATE UTILS FOLDER STRUCTURE

### File: utils/__init__.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\utils\__init__.py`
**Content:**
```python
# Utils package
```

### File: utils/file_discovery.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\utils\file_discovery.py`

Already created - see file_discovery.py in outputs

---

## STEP 5: CREATE PROCESSORS FOLDER (EMPTY FOR NOW)

### File: processors/__init__.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\processors\__init__.py`
**Content:**
```python
# Processors package
```

### File: processors/state_detector.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\processors\state_detector.py`
**Content:**
```python
"""
State Detector Module
To be implemented in Phase 4
"""

# Placeholder for Phase 4
```

### File: processors/hsn_cleaner.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\processors\hsn_cleaner.py`
**Content:**
```python
"""
HSN Cleaner Module
Removes letters from HSN codes
"""

import re

def clean_hsn_code(hsn_value):
    """
    Extract only numeric digits from HSN
    
    Example:
        95069990aa → 95069990
        42032110 → 42032110
    """
    if not hsn_value:
        return None
    
    # Convert to string
    hsn_str = str(hsn_value).strip()
    
    # Extract only digits
    hsn_clean = ''.join(c for c in hsn_str if c.isdigit())
    
    return int(hsn_clean) if hsn_clean else None

# To be integrated into Phase 3
```

---

## STEP 6: CREATE GENERATORS FOLDER (PLACEHOLDERS)

### File: generators/__init__.py
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\generators\__init__.py`
**Content:**
```python
# Generators package
```

### File: generators/gstr_b2b_gen.py
**Location:** `.../generators/gstr_b2b_gen.py`
**Content:**
```python
"""
GSTR B2B Template Generator
Phase 6 Implementation

Template: B2B Invoices
Source: Amazon B2B + E-Invoice B2B
Columns: GSTIN, Invoice#, Date, Value, Place of Supply, Rate, Taxable Value, etc.
"""

# Implementation coming in Phase 6
```

### File: generators/gstr_b2cs_gen.py
**Location:** `.../generators/gstr_b2cs_gen.py`
**Content:**
```python
"""
GSTR B2CS Template Generator
Phase 6 Implementation

Template: B2C Summary
Source: Flipkart 7A + 7B + Amazon B2C Small/Large
Aggregate by: (State, Tax Rate)
"""

# Implementation coming in Phase 6
```

### File: generators/hsn_b2b_gen.py
**Location:** `.../generators/hsn_b2b_gen.py`
**Content:**
```python
"""
HSN B2B Template Generator
Phase 6 Implementation

Template: B2B HSN Summary
Source: E-Invoice HSN data
Columns: HSN, Description, UQC, Qty, Value, Taxable, IGST, CGST, SGST, Cess
"""

# Implementation coming in Phase 6
```

### File: generators/hsn_b2c_gen.py
**Location:** `.../generators/hsn_b2c_gen.py`
**Content:**
```python
"""
HSN B2C Template Generator
Phase 6 Implementation

Template: B2C HSN Summary
Source: Flipkart Sec 12 + Amazon HSN (minus E-Invoice HSN)
Filter: Exclude B2B HSN codes
"""

# Implementation coming in Phase 6
```

### File: generators/documents_gen.py
**Location:** `.../generators/documents_gen.py`
**Content:**
```python
"""
Documents Template Generator
Phase 6 Implementation

Template: Invoice Series
Source: Flipkart Section 13
Calculation: Total - Cancelled = Net
"""

# Implementation coming in Phase 6
```

### File: generators/creditnotes_gen.py
**Location:** `.../generators/creditnotes_gen.py`
**Content:**
```python
"""
Credit Notes Template Generator
Phase 6 Implementation

Template: Credit/Debit Notes
Source: Amazon credit note sheets + B2B returns
"""

# Implementation coming in Phase 6
```

### File: generators/eco_gen.py
**Location:** `.../generators/eco_gen.py`
**Content:**
```python
"""
ECO Template Generator
Phase 6 Implementation

Template: E-Commerce Operator
Source: Flipkart Section 3 + Amazon E-Commerce GSTIN column
"""

# Implementation coming in Phase 6
```

---

## STEP 7: CREATE SUPPORT FILES

### File: requirements.txt
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\requirements.txt`
**Content:**
```
pandas>=2.0.0
openpyxl>=3.10.0
```

### File: .gitignore
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\.gitignore`
**Content:**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
output/
logs/
input/
*.xlsx
*.csv
.DS_Store
```

### File: README.md
**Location:** `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\README.md`
**Content:**
```markdown
# GST Automation Project

Automated GST return filing for multi-state Indian businesses using Flipkart, Amazon, and other marketplace data.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Add input files to `input/` folder

3. Run automation:
   ```bash
   python main.py
   ```

4. Output files in `output/Jan26/` (or current month)

## Project Structure

- `main.py` - Main orchestrator
- `readers/` - Platform-specific data readers (modular)
- `utils/` - Utility functions
- `processors/` - Data processing modules
- `generators/` - Template generators (Phase 6)
- `input/` - Your input files
- `output/` - Generated CSV files
- `config.json` - Configuration

## Phases

- Phase 1: File Discovery ✅
- Phase 2: Data Loading ✅
- Phase 3: Normalization (placeholder)
- Phase 4: State Detection (placeholder)
- Phase 5: Output Structure (placeholder)
- Phase 6: Template Generation (placeholder)
- Phase 7: Validation (placeholder)
- Phase 8: Output & Audit (placeholder)

## For Claude Code Development

Open this folder in VS Code and continue with Phase 6.
All foundation work is complete!
```

---

## FOLDER STRUCTURE SUMMARY

After copying all files, your folder should look like:

```
C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\
│
├── config.json
├── main.py
├── requirements.txt
├── .gitignore
├── README.md
├── SETUP_GUIDE_VS_CODE.md
├── PHASE_1_COMPLETE.md
│
├── readers/
│   ├── __init__.py
│   ├── base_reader.py
│   ├── flipkart_reader.py
│   ├── amazon_reader.py
│   └── einvoice_reader.py
│
├── utils/
│   ├── __init__.py
│   └── file_discovery.py
│
├── processors/
│   ├── __init__.py
│   ├── state_detector.py
│   └── hsn_cleaner.py
│
├── generators/
│   ├── __init__.py
│   ├── gstr_b2b_gen.py
│   ├── gstr_b2cs_gen.py
│   ├── hsn_b2b_gen.py
│   ├── hsn_b2c_gen.py
│   ├── documents_gen.py
│   ├── creditnotes_gen.py
│   └── eco_gen.py
│
├── input/                    (Create this folder)
│   ├── Flipkart_raw_gst_eport.xlsx
│   └── GSTR1JANUARY2026A3SZBDZ05A1P39XX.xlsx (all 14 files)
│
├── output/                   (Auto-created when you run)
│   └── Jan26/
│
└── logs/                     (Auto-created when you run)
```

---

## INSTALLATION CHECKLIST

- [ ] Install Python 3.10+ from python.org
- [ ] Install VS Code from code.visualstudio.com
- [ ] Create folder: `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project`
- [ ] Copy all Python files listed above
- [ ] Copy config.json, requirements.txt, .gitignore, README.md
- [ ] Create `input/` folder
- [ ] Copy Excel files to `input/` folder
- [ ] Open folder in VS Code
- [ ] Install Python extension in VS Code
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate: `venv\Scripts\activate` (Windows)
- [ ] Install packages: `pip install -r requirements.txt`
- [ ] Run: `python main.py`

---

## YOU'RE ALL SET! 🚀

Everything is ready for Claude Code development in Visual Studio.

Next step: Open VS Code and continue with Phase 6!

