# VCF 9.0 CPU Support Report

Generate a point-in-time HTML report summarizing server CPU support status for vSphere 9.0 (as part of VCF 9.0 planning) using:
- A Hardware Compatibility Guide (HCL) Systems CSV export, and
- An optional host inventory CSV (from VCF Operations or similar).

The report includes:
- High-level overview and context,
- vSphere 8 lifecycle information for upgrade planning,
- HCL support summary (OK vs Blocked) with a pie chart,
- Detailed tables grouped by vendor,
- Appendix tying your inventory hostnames to HCL support with another pie chart.

Source file:
- vcf9_cpu_support_report/vcf9_cpu_support_report.py

Repository:
- https://github.com/BakingClouds/vcf9

## Features

- Robust CSV parsing with auto-detection of common delimiters (comma, semicolon, tab, pipe) and encodings (UTF-8, UTF-8 BOM, cp1252, latin-1).
- Flexible column name matching (handles different header spellings and spacing).
- Server/vendor grouping and clear OK vs Blocked classification for ESXi 9.0 installability.
- Optional header image (cover.png).
- Clean, self-contained HTML output (no external dependencies).

## How it decides “OK” vs “Blocked”

A system is considered:
- OK: if the “Supported Releases” text contains “ESXi 9.0”.
- Blocked: otherwise (including 8.x only, discontinued in 9.x, not listed, or unknown).

This is a conservative planning view: if it’s not explicitly listed as ESXi 9.0 installable, it’s treated as Blocked.

## Inputs

1) HCL Systems CSV (required)
- Place a file matching Systems*.csv inside your HCL directory.
- Required columns (case/spacing flexible):
  - Model (e.g., “Model”, “Server Model”, “Product”, “Model Name”)
  - CPU Model (e.g., “CPU Model”, “CPU”, “Processor”)
  - Supported Releases (e.g., “Supported Releases”, “Supported versions”, “Releases”, “SupportedRelease”)
- Optional:
  - Code Name (e.g., “Code Name”, “Codename”)

2) Host Inventory CSV (optional)
- If present, used to produce an appendix with hostnames and a second pie chart.
- The script searches in INV_SEARCH_DIRS (defaults to [BASE_DIR]) for a CSV with “host”, and “inventory” OR the common typo “invenotry” in the filename.
- Expected columns (flexible names):
  - Name or Hostname
  - Model
  - CPU Model or Processor

## Output

- A standalone HTML file written to:
  - vcf9_cpu_support_report_YYYYMMDD.html in BASE_DIR
- Sections included:
  - Report Overview and context (with links to the Broadcom Compatibility Guide and KBs)
  - vSphere 8 lifecycle summary
  - HCL Support Summary (pie chart + counts)
  - Detail by Vendor (tables, OK/Blocked row highlighting)
  - Appendix: Full Inventory with Server Names (if inventory provided), plus a pie chart

## Requirements

- Python 3.8+ (standard library only)
- No third-party packages required

## Setup

Open vcf9_cpu_support_report/vcf9_cpu_support_report.py and edit the configuration at the top:

```python
BASE_DIR   = "PATH TO YOUR BASE DIRECTORY"      # e.g., "/Users/me/reports/vcf9"
HCL_DIR    = os.path.join(BASE_DIR, "NAME OF HCL DIRECTORY")  # e.g., "/Users/me/reports/vcf9/hcl"
HEADER_IMG = os.path.join(BASE_DIR, "cover.png")  # optional; leave as-is or remove file if not used
OUT_HTML   = os.path.join(BASE_DIR, f"vcf9_cpu_support_report_{datetime.now().strftime('%Y%m%d')}.html")

INV_SEARCH_DIRS = [BASE_DIR]  # folders to search for your Host Inventory CSV
DEBUG = True                  # prints extra parsing details
```

Directory example:
- BASE_DIR/
  - hcl/
    - Systems_BCG_export.csv
  - Sep 2025 Host Inventory.csv  (optional)
  - cover.png                    (optional)

## Running

From the repository root (or any working directory), run:

```bash
python3 vcf9_cpu_support_report/vcf9_cpu_support_report.py
```

Then open the generated HTML file reported at the end of the run.

## CSV Examples

HCL (Systems*.csv):
```csv
Model,CPU Model,Code Name,Supported Releases
Dell PowerEdge R650,Intel Xeon Gold 6338 (Ice Lake),Ice Lake,ESXi 7.0 U3; ESXi 8.0 U2; ESXi 9.0
HPE ProLiant DL380 Gen10,Intel Xeon Silver 4214,Cascade Lake,ESXi 6.7 U3; ESXi 7.0 U3; ESXi 8.0 U2
```

Inventory (host inventory CSV):
```csv
Name,Model,CPU Model
esx01.lab.local,Dell PowerEdge R650,Intel Xeon Gold 6338 @ 2.0GHz
esx02.lab.local,HPE ProLiant DL380 Gen10,Intel Xeon Silver 4214 CPU @ 2.2GHz
```

Notes:
- CPU clock speeds like “@ 2.2GHz” are stripped when matching to the HCL.
- Matching first tries exact normalized model+CPU, then a relaxed check (same model, CPU substring overlap).
- If no match is found, the host is listed and conservatively marked Blocked.

## Customizing the look

- The HTML embeds CSS for a clean report; you can tweak the css_styles() function.
- Add or remove content blocks in the HTML assembly section as needed.
- Replace or remove the cover image (HEADER_IMG).

## Troubleshooting

- ERROR: Could not find Systems*.csv
  - Ensure HCL_DIR points to a folder containing a file named like Systems_...csv (spaces are okay).
- ERROR: Required columns not found in your HCL CSV
  - Check the HCL headers and the “Inputs” section above. The script prints normalized headers to help.
- WARN: Could not parse the Host Inventory CSV
  - The report still generates without the appendix names/pie; verify the file is in INV_SEARCH_DIRS and has expected columns.
- Delimiter/encoding issues
  - The parser auto-detects comma/semicolon/tab/pipe and UTF-8/UTF-8 BOM/cp1252/latin-1. If the file is very unusual, re-export as UTF-8 CSV.

## Limitations and Notes

- Classification is string-based: only entries explicitly listing “ESXi 9.0” are considered OK.
- The Broadcom Compatibility Guide is updated frequently; always validate final decisions against the official guide:
  - https://compatibilityguide.broadcom.com/
- Vendors are inferred from the model string and may show as “Other” if unknown.

## License

See repository license (if provided). If none, consult the repository owner.

---
Maintained by BakingClouds. Contributions and improvements welcome.
