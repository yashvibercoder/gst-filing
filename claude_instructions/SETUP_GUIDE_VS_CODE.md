# GST Automation - Visual Studio Setup Guide

## PROJECT FOLDER STRUCTURE

Your project should be organized as follows:

```
C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\
├── config.json                          # Configuration file
├── main.py                              # Main orchestrator script
│
├── readers/                             # Platform-specific readers (modular)
│   ├── __init__.py
│   ├── base_reader.py                  # Base class (interface template)
│   ├── flipkart_reader.py              # Flipkart implementation
│   ├── amazon_reader.py                # Amazon implementation
│   ├── einvoice_reader.py              # E-Invoice implementation
│   ├── meesho_reader.py                # (Future - just add when needed)
│   ├── blinkit_reader.py               # (Future - just add when needed)
│   └── offline_b2b_reader.py           # (Future - just add when needed)
│
├── utils/                               # Utility modules
│   ├── __init__.py
│   ├── file_discovery.py               # Auto-discovers input files
│   ├── normalizer.py                   # (Phase 3 - Data normalization)
│   ├── consolidator.py                 # (Phase 5 - Data consolidation)
│   └── validator.py                    # (Phase 7 - Validation)
│
├── processors/                          # Data processing modules
│   ├── __init__.py
│   ├── state_detector.py               # (Phase 4 - State detection)
│   └── hsn_cleaner.py                  # HSN code cleaning (remove letters)
│
├── generators/                          # Template generators (Phase 6)
│   ├── __init__.py
│   ├── gstr_b2b_gen.py                 # B2B template generator
│   ├── gstr_b2cs_gen.py                # B2CS template generator
│   ├── hsn_b2b_gen.py                  # HSN B2B template generator
│   ├── hsn_b2c_gen.py                  # HSN B2C template generator
│   ├── documents_gen.py                # Documents template generator
│   ├── creditnotes_gen.py              # Credit notes generator
│   └── eco_gen.py                      # ECO template generator
│
├── output/                              # Output folder (auto-created)
│   └── Jan26/                          # Monthly folder (auto-created)
│       ├── Andhra_Pradesh/             # State folders (auto-created)
│       ├── Arunachal_Pradesh/
│       ├── ... (64 state folders)
│       └── West_Bengal/
│
├── logs/                                # Log files (auto-created)
│   └── execution_log_Jan_2026.txt
│
├── input/                               # Input files folder (YOUR DATA GOES HERE)
│   ├── Flipkart_raw_gst_eport.xlsx
│   ├── GSTR1JANUARY2026A3SZBDZ05A1P39XX.xlsx (14 Amazon files)
│   ├── E_Invoice_HSN_B2B_January_2026.xlsx (when available)
│   ├── B2B_Invoices_January_2026.xlsx (when available)
│   ├── Meesho_raw_gst_January_2026.xlsx (future)
│   └── Blinkit_raw_gst_January_2026.xlsx (future)
│
├── requirements.txt                     # Python dependencies
├── .gitignore                           # Git ignore file
├── README.md                            # Project documentation
├── PHASE_1_COMPLETE.md                 # Phase 1 summary
├── SETUP_GUIDE.md                      # This file
└── DEVELOPMENT_ROADMAP.md              # Phase by phase roadmap
```

---

## SETUP STEPS FOR VISUAL STUDIO CODE

### Step 1: Create Folder Structure

Create the following folders manually in Windows Explorer:
```
C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\
├── readers/
├── utils/
├── processors/
├── generators/
├── output/
├── logs/
└── input/
```

### Step 2: Download Python Files

Copy these Python files from the current session to your project folder:
```
From: /home/claude/gst_automation/
To:   C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\

Copy:
- main.py
- config.json
- readers/__init__.py
- readers/base_reader.py
- readers/flipkart_reader.py
- readers/amazon_reader.py
- readers/einvoice_reader.py
- utils/__init__.py
- utils/file_discovery.py
- PHASE_1_COMPLETE.md
```

### Step 3: Create Missing Files

Create these empty files (for future phases):
```
utils/
  - __init__.py (already exists)
  - normalizer.py (create empty)
  - consolidator.py (create empty)
  - validator.py (create empty)

processors/
  - __init__.py (create empty)
  - state_detector.py (create empty)
  - hsn_cleaner.py (create empty)

generators/
  - __init__.py (create empty)
  - gstr_b2b_gen.py (create empty)
  - gstr_b2cs_gen.py (create empty)
  - hsn_b2b_gen.py (create empty)
  - hsn_b2c_gen.py (create empty)
  - documents_gen.py (create empty)
  - creditnotes_gen.py (create empty)
  - eco_gen.py (create empty)
```

### Step 4: Create requirements.txt

Create a file: `requirements.txt`
```
pandas>=2.0.0
openpyxl>=3.10.0
```

### Step 5: Create .gitignore

Create a file: `.gitignore`
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

### Step 6: Update config.json

Edit `config.json` and update the input folder path:
```json
{
  "input_folder": "input",  // <- Change from "/mnt/project" to "input"
  "output_base_folder": "output",
  // ... rest stays same
}
```

### Step 7: Prepare Input Folder

Copy your input files to: `input/`
```
C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\input\
├── Flipkart_raw_gst_eport.xlsx
├── GSTR1JANUARY2026A3SZBDZ05A1P39XX.xlsx (all 14 Amazon files)
├── E_Invoice_HSN_B2B_January_2026.xlsx (when ready)
└── B2B_Invoices_January_2026.xlsx (when ready)
```

---

## OPEN IN VISUAL STUDIO CODE

### Step 1: Open Folder
- File → Open Folder
- Navigate to: `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project`
- Click "Select Folder"

### Step 2: Install Python Extension
- Go to Extensions (Ctrl+Shift+X)
- Search for "Python"
- Install "Python" by Microsoft
- Also install "Pylance" for better code completion

### Step 3: Select Python Interpreter
- Ctrl+Shift+P (Command Palette)
- Type: "Python: Select Interpreter"
- Choose: "Python 3.x.x" (your installed Python version)

### Step 4: Create Virtual Environment (Optional but Recommended)
- Ctrl+Shift+P
- Type: "Python: Create Environment"
- Choose "venv"
- VS Code creates and activates it automatically

### Step 5: Install Dependencies
- Open Terminal: Ctrl+` (backtick)
- Run: `pip install -r requirements.txt`

---

## FOLDER ORGANIZATION EXPLAINED

### `readers/` - Modular Platform Readers
**Why modular?** Each platform is independent. Add new ones without changing code.

Files you have now:
- `base_reader.py` - Template/interface (defines what all readers must implement)
- `flipkart_reader.py` - Reads Flipkart files
- `amazon_reader.py` - Reads Amazon files
- `einvoice_reader.py` - Reads E-Invoice files

Files to add later (just create new files):
- `meesho_reader.py` - Month 3
- `blinkit_reader.py` - Month 6
- `offline_b2b_reader.py` - Month 9

**No changes needed to main.py!** It auto-detects readers.

### `utils/` - Utility Functions
Currently has:
- `file_discovery.py` - Auto-finds input files

To be added:
- `normalizer.py` - Phase 3 (data normalization)
- `consolidator.py` - Phase 5 (consolidate platforms)
- `validator.py` - Phase 7 (validation & reconciliation)

### `processors/` - Data Processing
To be added:
- `state_detector.py` - Phase 4 (detect states dynamically)
- `hsn_cleaner.py` - Clean HSN codes (remove letters)

### `generators/` - Template Generators
To be added (Phase 6):
- `gstr_b2b_gen.py` - Generate B2B template
- `gstr_b2cs_gen.py` - Generate B2CS template
- `hsn_b2b_gen.py` - Generate HSN B2B
- `hsn_b2c_gen.py` - Generate HSN B2C
- `documents_gen.py` - Generate Documents
- `creditnotes_gen.py` - Generate Credit Notes
- `eco_gen.py` - Generate ECO template

### `input/` - Your Data
Put your input files here:
- 1 Flipkart file
- 14 Amazon files
- E-Invoice file (when ready)
- Offline B2B file (when ready)

### `output/` - Generated Files
Auto-created with structure:
```
output/
├── Jan26/ (January 2026)
│   ├── Andhra_Pradesh/
│   │   ├── AP_Andhra_Pradesh_GSTR_B2CS_Jan_2026.csv
│   │   ├── AP_Andhra_Pradesh_GSTR_B2B_Jan_2026.csv
│   │   └── ... (7 templates per state)
│   └── ... (64 state folders)
```

---

## HOW TO RUN IN VISUAL STUDIO

### Method 1: Using Terminal

```bash
# Make sure you're in the project folder
cd C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project

# Run main.py
python main.py
```

### Method 2: Using VS Code Run Button
- Open `main.py`
- Click ▶️ (Run) button in top right
- Output appears in Terminal

### Method 3: Using Debug
- Press F5 (Debug)
- Choose "Python" as environment
- Debug mode starts

---

## EXPECTED OUTPUT

When you run `python main.py`, you should see:

```
================================================================================
GST AUTOMATION - INITIALIZATION
================================================================================
Month: January 2026
Input folder: input
Output folder: output

================================================================================
PHASE 1: FILE DISCOVERY
================================================================================

✓ FLIPKART
  ✓ Flipkart_raw_gst_eport.xlsx
  Total: 1 file(s)

✓ AMAZON
  ✓ GSTR1JANUARY2026A3SZBDZ05A1P3903IFWPS9148C1ZS.xlsx
  ... (14 files total)
  Total: 14 file(s)

✓ PHASE 2: LOADING DATA FROM PLATFORMS
✓ PHASE 3: DATA NORMALIZATION
✓ PHASE 4: STATE DETECTION
✓ PHASE 5: OUTPUT STRUCTURE CREATION
⏳ PHASE 6: TEMPLATE GENERATION (coming next)

================================================================================
AUTOMATION COMPLETE!
================================================================================
```

---

## NEXT STEPS FOR CLAUDE CODE

### Phase 6: Template Generation
When ready in Claude Code:
1. Implement `generators/gstr_b2b_gen.py`
2. Implement `generators/gstr_b2cs_gen.py`
3. Implement `generators/hsn_b2b_gen.py`
4. Implement `generators/hsn_b2c_gen.py`
5. Implement `generators/documents_gen.py`
6. Implement `generators/creditnotes_gen.py`
7. Implement `generators/eco_gen.py`

### Phase 7: Validation
1. Implement `utils/validator.py`
2. Add validation logic to main.py

### Phase 8: Output & Cleanup
1. Complete audit logging
2. Generate final CSV files
3. Test with real data

---

## TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'pandas'"
**Solution:**
```bash
pip install pandas openpyxl
```

### Issue: "Cannot find input files"
**Solution:**
- Check `input/` folder exists
- Verify file names match patterns in `config.json`
- Run from correct directory

### Issue: "Python not found"
**Solution:**
- Install Python from python.org
- Make sure to add Python to PATH during installation
- Restart VS Code

### Issue: "UnicodeDecodeError" reading Excel files
**Solution:**
- Make sure pandas and openpyxl are latest versions:
```bash
pip install --upgrade pandas openpyxl
```

---

## QUICK REFERENCE

### File Discovery Patterns (in config.json)
```json
"file_patterns": {
  "flipkart": "*Flipkart*.xlsx",
  "amazon": "*A3SZBDZ05A1P39*.xlsx",
  "einvoice": "*[Ee]Invoice*.xlsx",
  "meesho": "*Meesho*.xlsx",
  "blinkit": "*Blinkit*.xlsx",
  "offline_b2b": "*B2B*.xlsx"
}
```

### Excel Sheets to Read
```json
"flipkart_sheets": {
  "b2c_intrastate": "Section 7(A)(2) in GSTR-1",
  "b2c_interstate": "Section 7(B)(2) in GSTR-1",
  "hsn": "Section 12 in GSTR-1",
  "documents": "Section 13 in GSTR-1",
  "eco": "Section 3 in GSTR-8"
},
"amazon_sheets": {
  "b2c_small": "B2C Small",
  "b2c_large": "B2C Large",
  "b2b": "B2B",
  "hsn": "HSN Summary"
}
```

---

## YOU'RE READY! 🚀

Your project is set up for Visual Studio Code. You now have:

✅ Modular architecture (LEGO blocks, not glued bricks)
✅ Auto-discovery of input files (no file list needed)
✅ Configuration-driven setup (easy to modify)
✅ Phase 1-5 foundation complete
✅ Placeholder files for Phases 6-8

All you need to do is:
1. Copy files to your local folder
2. Put input files in `input/` folder
3. Run `python main.py`
4. Then use Claude Code in VS to implement Phases 6-8

Good luck! 🎉

