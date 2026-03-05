# GST Filing — How to Install & Use

---

## What is this?

A web app that automates GST return filing.
You upload your sales data (Excel files), it generates all the required GST templates automatically.
Open it in any browser — no internet needed after setup.

---

## STEP 1 — Install Git (one time only)

Git is needed to download the software.

1. Open **PowerShell** (search for it in the Start menu)
2. Paste this and press Enter:
   ```
   winget install --id Git.Git -e
   ```
3. Wait for it to finish
4. **Close PowerShell and open it again** (important!)

---

## STEP 2 — Download the software (one time only)

In PowerShell, paste these **one line at a time** and press Enter after each:

```
git clone https://github.com/yashvibercoder/gst-filing.git
```
```
cd gst-filing
```
```
install.bat
```

> `install.bat` will automatically install Python, Node.js, and everything else needed.
> It may ask you to **close and reopen PowerShell once** during install — just do that and run `install.bat` again.

This takes about **5–10 minutes** the first time.

---

## STEP 3 — Run the app

Every time you want to use the app:

1. Go to the `gst-filing` folder
2. Double-click **`start-portal.bat`**
3. A browser window will open automatically at **http://localhost:8000**
4. Select your company and start using it

> Keep the black command window open while using the app. Close it when done.

---

## STEP 4 — Using the app

1. **Login page** → Click your company name (or create one first)
2. **Upload** → Upload your Excel sales files (Flipkart, Amazon, Meesho, E-Invoice)
3. **Process** → Click "Run" to generate GST returns
4. **Review** → View generated files, download as ZIP
5. **Audit** → Compare against previous month templates

---

## Getting updates (when a new version is released)

1. Open PowerShell inside the `gst-filing` folder
2. Run these two commands:
   ```
   git pull
   ```
   ```
   setup.bat
   ```
3. Then start normally with `start-portal.bat`

> You only need to run `setup.bat` after an update if told to. Otherwise just `git pull` is enough.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `start-portal.bat` opens and closes immediately | Run it from inside the folder, not from desktop |
| Browser shows "Not Found" | Wait 5 seconds and refresh. Backend may still be starting |
| Port already in use error | Restart your PC and try again |
| `git` not found | Restart PowerShell after installing Git |
| `python` not found | Restart PowerShell after installing Python |

---

## Folder structure (what goes where)

```
gst-filing/
├── Input files/        ← Put your Excel files here (created automatically)
├── output/             ← Generated GST files appear here
├── start-portal.bat    ← Double-click to start the app
├── install.bat         ← Run once during setup
└── setup.bat           ← Run after updates
```

---

*For issues, contact the person who shared this software with you.*
