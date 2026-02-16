# VS CODE SETUP CHECKLIST - Manual Folder Structure

## YOUR TARGET LOCATION:
```
C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\
```

---

## STEP 1: CREATE MAIN FOLDER STRUCTURE

Using Windows File Explorer, create these folders:

```
C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\
│
├── readers/
├── utils/
├── processors/
├── generators/
├── input/
├── output/
└── logs/
```

**How to create:**
1. Right-click on "GST Project" folder
2. New → Folder
3. Name it "readers"
4. Repeat for: utils, processors, generators, input, output, logs

---

## STEP 2: COPY ALL PYTHON FILES

All Python files are available in the outputs folder from this Claude session.

### Download and place these files:

**Root Level (GST Project folder):**
- [ ] main.py
- [ ] config.json
- [ ] requirements.txt
- [ ] .gitignore
- [ ] README.md

**In readers/ folder:**
- [ ] __init__.py
- [ ] base_reader.py
- [ ] flipkart_reader.py
- [ ] amazon_reader.py
- [ ] einvoice_reader.py

**In utils/ folder:**
- [ ] __init__.py
- [ ] file_discovery.py

**In processors/ folder:**
- [ ] __init__.py
- [ ] state_detector.py
- [ ] hsn_cleaner.py

**In generators/ folder:**
- [ ] __init__.py
- [ ] gstr_b2b_gen.py
- [ ] gstr_b2cs_gen.py
- [ ] hsn_b2b_gen.py
- [ ] hsn_b2c_gen.py
- [ ] documents_gen.py
- [ ] creditnotes_gen.py
- [ ] eco_gen.py

---

## STEP 3: COPY YOUR INPUT FILES

Place your Excel files in the `input/` folder:

- [ ] Flipkart_raw_gst_eport.xlsx
- [ ] All 14 Amazon GSTR files (GSTR1JANUARY2026A3SZBDZ05A1P39XX.xlsx)

**Final structure:**
```
GST Project/
├── input/
│   ├── Flipkart_raw_gst_eport.xlsx
│   ├── GSTR1JANUARY2026A3SZBDZ05A1P3903IFWPS9148C1ZS.xlsx
│   ├── GSTR1JANUARY2026A3SZBDZ05A1P3906IFWPS9148C1ZM.xlsx
│   ├── ... (12 more Amazon files)
│   └── GSTR1JANUARY2026A3SZBDZ05A1P3929IFWPS9148C2ZD.xlsx
```

---

## STEP 4: OPEN IN VS CODE

1. Launch Visual Studio Code
2. File → Open Folder
3. Navigate to: `C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project`
4. Click "Select Folder"

---

## STEP 5: VS CODE SETUP

### Install Python Extension:
1. Ctrl+Shift+X (Extensions panel)
2. Search: "Python"
3. Click "Install" on "Python" by Microsoft
4. Also install "Pylance" for better code support

### Set Python Interpreter:
1. Ctrl+Shift+P (Command Palette)
2. Type: "Python: Select Interpreter"
3. Choose: Your Python 3.10+ version

### Create Virtual Environment:
1. Ctrl+` (open terminal)
2. Run: `python -m venv venv`
3. When prompted: Click "Yes" to activate

### Install Dependencies:
1. In terminal: `pip install -r requirements.txt`
2. Wait for pandas and openpyxl to install

---

## STEP 6: TEST THE SETUP

1. Open terminal: Ctrl+`
2. Run: `python main.py`
3. You should see: ✅ AUTOMATION COMPLETE!

---

## FINAL FOLDER STRUCTURE

After all files are copied:

```
C:\Users\swapn\OneDrive\Desktop\VS\Claude projects\GST Project\
│
├── config.json                          ✓
├── main.py                              ✓
├── requirements.txt                     ✓
├── .gitignore                           ✓
├── README.md                            ✓
│
├── readers/                             (5 files)
│   ├── __init__.py
│   ├── base_reader.py
│   ├── flipkart_reader.py
│   ├── amazon_reader.py
│   └── einvoice_reader.py
│
├── utils/                               (2 files)
│   ├── __init__.py
│   └── file_discovery.py
│
├── processors/                          (3 files)
│   ├── __init__.py
│   ├── state_detector.py
│   └── hsn_cleaner.py
│
├── generators/                          (8 files - placeholders for Phase 6)
│   ├── __init__.py
│   ├── gstr_b2b_gen.py
│   ├── gstr_b2cs_gen.py
│   ├── hsn_b2b_gen.py
│   ├── hsn_b2c_gen.py
│   ├── documents_gen.py
│   ├── creditnotes_gen.py
│   └── eco_gen.py
│
├── input/                               (Your Excel files)
│   ├── Flipkart_raw_gst_eport.xlsx
│   └── GSTR1JANUARY2026A3SZBDZ05A1P39XX.xlsx (14 files)
│
├── output/                              (Auto-created by script)
│   └── Jan26/ (auto-created)
│
└── logs/                                (Auto-created by script)
```

---

## WHAT'S READY FOR CLAUDE CODE

✅ **Phase 1-5 Complete:** File discovery, data loading, state detection
✅ **Modular Architecture:** Ready to add Meesho, Blinkit without code changes
✅ **Placeholder Files:** All 7 template generators waiting for implementation
✅ **Configuration:** config.json controls everything
✅ **Ready for Phase 6:** Implement template generators in Claude Code

---

## HOW TO CONTINUE WITH CLAUDE CODE

Once everything is set up:

1. Open any placeholder generator file (e.g., `generators/gstr_b2b_gen.py`)
2. Open Claude Code in VS Code
3. Tell Claude Code: "Implement the B2B template generator"
4. Claude Code will write the code for you!

Repeat for each of the 7 generators.

---

## YOU'RE ALL SET! 🎉

All files are prepared in the outputs folder. Just copy them to your VS Code project folder and you're ready to use Claude Code for Phase 6!

