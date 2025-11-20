# SDDC Health Unified Report Generator

This Python script generates a unified HTML report from daily SDDC health check files. It searches for `*.htm` files in daily report folders and consolidates the "Version Health Status" information into a single, easy-to-read HTML report showing the Bill of Materials (BOM) per SDDC.

## 🔧 Requirements

- **Python 3.9+** (tested on 3.11)
- **Standard library only** - no additional packages required
- **Optional:** A header image (`cover.png`) for branding

## 📂 Folder Structure

The script expects the following folder structure:

```
/Users/talicia/sddc-health/
├── sddc_health_report.py          # This script
├── cover.png                      # Optional header image (PNG format)
└── reports/                       # Daily report folders
    ├── 2025-01-15/               # Daily folder (YYYY-MM-DD format)
    │   ├── sddc1-health.htm
    │   ├── sddc2-health.htm
    │   └── ...
    ├── 2025-01-16/
    │   ├── sddc1-health.htm
    │   └── ...
    └── 2025-01-17/
        └── ...
```

### Requirements:

1. **Daily Report Folders**: Must follow the `YYYY-MM-DD` naming pattern
2. **HTM Files**: Each folder should contain `*.htm` files with SDDC health reports
3. **Version Health Status Table**: Each HTM file should contain a table with the section "Version Health Status" that includes columns:
   - Component
   - Resource
   - Version

Example table entry:
```
Component | Resource       | Version
----------|----------------|------------------
ESXI      | ESX.internal   | 8.0.2-22380479
```

## ⚙️ Configuration

Edit the following variables at the top of the script to match your environment:

```python
BASE_DIR = "/Users/talicia/sddc-health"        # Base directory
REPORTS_DIR = os.path.join(BASE_DIR, "reports") # Daily reports location
HEADER_IMG = os.path.join(BASE_DIR, "cover.png") # Optional header image
```

## ▶️ How to Run

1. **Ensure your folder structure is set up** as described above

2. **Run the script:**
   ```bash
   python3 sddc_health_report.py
   ```

3. **Output:**
   - The script will generate an HTML file in the base directory
   - Filename format: `sddc_health_unified_report_YYYYMMDD.html`
   - Example: `sddc_health_unified_report_20250120.html`

## 📊 Report Features

The generated HTML report includes:

### 1. **Header Banner**
   - Optional PNG image at the top of the report
   - Automatically embedded as base64 data URI

### 2. **Report Overview**
   - Generation timestamp
   - Number of folders processed
   - Number of SDDCs found

### 3. **Table of Contents**
   - Quick navigation links to each SDDC section
   - Alphabetically sorted

### 4. **SDDC Sections**
   - One section per SDDC
   - Each section shows:
     - SDDC name
     - Report date
     - Version Health Status table with:
       - Component (highlighted in blue)
       - Resource
       - Version (monospace font for better readability)

### 5. **Modern Styling**
   - Clean, professional appearance
   - Responsive design
   - Color-coded components
   - Hover effects on table rows
   - Easy-to-read typography

## 🔍 How It Works

1. **Scans** the reports directory for folders matching the `YYYY-MM-DD` pattern
2. **Searches** each folder for `*.htm` files
3. **Extracts** the SDDC name from each HTM file (looks for "SDDC" in title, headers, or content)
4. **Parses** the "Version Health Status" table from each HTM file
5. **Groups** data by SDDC name
6. **Generates** a unified HTML report with all information consolidated

## 🐛 Debug Mode

The script includes debug output by default. To disable it:

```python
DEBUG = False
```

With debug enabled, you'll see:
- Folders being processed
- HTM files found
- SDDC names extracted
- Tables discovered
- Any warnings or errors

## 📝 Example Output

```
============================================================
SDDC Health Unified Report Generator
============================================================

Processing 3 daily report folder(s)...

[DEBUG] Processing folder: 2025-01-17
[DEBUG] Found 2 HTM files
[DEBUG] Extracted SDDC name: SDDC-Production-01
[DEBUG] Found Version Health Status table with headers: ['Component', 'Resource', 'Version']
[DEBUG] Extracted SDDC name: SDDC-Production-02
[DEBUG] Found Version Health Status table with headers: ['Component', 'Resource', 'Version']

Found data for 2 SDDC(s)

============================================================
Report generated successfully!
Output file: /Users/talicia/sddc-health/sddc_health_unified_report_20250120.html
============================================================
```

## 🎨 Customization

### Styling
The CSS styles are defined in the `css_styles()` function. You can customize:
- Colors (see CSS variables in `:root`)
- Font families
- Table styling
- Section layouts

### SDDC Name Detection
If the script doesn't detect your SDDC names correctly, you can modify the patterns in the `extract_sddc_name()` function.

### Table Detection
The script looks for tables with headers containing "component", "resource", and "version". Modify the `VersionHealthTableParser` class if your tables use different column names.

## 🚨 Troubleshooting

### No folders found
- Verify the `REPORTS_DIR` path is correct
- Ensure folders follow the `YYYY-MM-DD` naming pattern
- Check folder permissions

### No tables found
- Ensure HTM files contain a "Version Health Status" table
- Check that the table has columns: Component, Resource, Version
- Verify the HTML structure is valid

### SDDC name is "Unknown SDDC"
- The script couldn't find "SDDC" in the HTM file
- Add the SDDC name to the title, h1, or h2 tags
- Or modify the `extract_sddc_name()` function to use a different pattern

## 📄 License

This script is part of the vcf9 repository and follows the same disclaimer and licensing terms.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows the existing style
- Debug output is helpful
- Error handling is robust
- Documentation is updated
