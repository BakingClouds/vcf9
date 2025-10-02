# VCF 9.0 Hardware Compatibility Report Generator
This repository contains a Python script (vcf9_cpu_support_report.py) that generates an HTML hardware compatibility report for VMware Cloud Foundation (VCF) 9.0, based on:

    •	Customer inventory data (exported from VCF Operations)
    •	Broadcom Hardware Compatibility Guide (HCL) exports
    •	Official knowledge base references
 
## 🔧 Requirements

    •	Python 3.9+ (tested on 3.11)
    •	Recommended: run inside a Python virtual environment
    •	Packages: only the standard library is used (no extra installs required)

**Optional: A header image (cover.png) for branding (otherwise it will be skipped).**
 
### 📂 Required Files and Folder Structure

    Customer/
    └── VCF Hardware Support/
        ├── vcf9_cpu_support_report.py          # The script
        ├── VCFcover.png                        # Optional cover/banner image
        ├── Compatibility Matrix Output/
        │   └── Systems_Servers.csv             # HCL export from Broadcom site
        └── Sep 2025 Host Inventory.csv         # Host inventory export from VCF Operations

#### 1. Broadcom HCL Export
- Navigate to the Broadcom Compatibility Guide
- Export Servers (Systems) as CSV.
- Save it inside Compatibility Matrix Output/ as Systems_Servers.csv.
- The script will auto-detect any file starting with Systems and ending with .csv.

#### 2. Customer Inventory Export
- From VCF Operations, export the Host Inventory (must include at least the columns: Name, Model, CPU Model).
- Save it in the VCF Hardware Support/ folder.
- The script accepts filenames containing Host + Inventory (case-insensitive).

        Example: Sep 2025 Host Inventory.csv
        If you accidentally export as Invenotry, the script will still detect it.

## ▶️ How to Run

1.	Clone/download this repository.
2.	Place the required files in the structure above.
3.	Activate your virtual environment (optional but recommended):

        python3 -m venv .venv
        source .venv/bin/activate

4.	Run the script:

        python3 vcf9_cpu_support_report.py

5.	Output:

        A report will be generated as HTML in the same folder:
        vcf9_cpu_support_report_YYYYMMDD.html

## 📊 Report Contents

The generated report includes:
1.	Cover banner (if cover.png provided)
2.	Sidebar navigation for easy browsing
3.	Report Overview
  - Context for VCF 9.0 hardware compatibility
  - Links to Broadcom Compatibility Guide

### 🎨 Status Colours

- ✅ OK → Server/CPU listed as supporting ESXi 9.0 in the HCL.
- ❌ Blocked → Server/CPU capped at ESXi 8.x, discontinued, or not listed.
 
### 📌 Notes
- The Broadcom Hardware Compatibility Guide is frequently updated.
- This report is a point-in-time snapshot and should not replace direct validation with the HCL before upgrades or procurement.
- The output is HTML — you can open it in any browser, share with your team, or print to PDF.

