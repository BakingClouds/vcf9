# Welcome to vcf9 repo
Repository created for VMware VCF9 helper scripts

## Available Scripts

### 1. VCF 9.0 Hardware Compatibility Report Generator
**Location:** `vcf9_cpu_support_report/`

Generates an HTML hardware compatibility report for VMware Cloud Foundation (VCF) 9.0, based on customer inventory data and Broadcom Hardware Compatibility Guide (HCL) exports.

[See README](vcf9_cpu_support_report/README.md) for detailed usage instructions.

### 2. SDDC Health Unified Report Generator
**Location:** `sddc_health_report/`

Generates a unified HTML report from daily SDDC health check files. Searches for `*.htm` files in daily report folders and consolidates the "Version Health Status" information into a single, easy-to-read HTML report showing the Bill of Materials (BOM) per SDDC.

**Features:**
- Searches daily report folders (YYYY-MM-DD format)
- Extracts SDDC names from HTM files
- Parses "Version Health Status" tables (Component, Resource, Version)
- Generates unified HTML report with modern styling
- Supports optional PNG header image
- Groups data by SDDC with table of contents

[See README](sddc_health_report/README.md) for detailed usage instructions.

# Disclaimer

This project is provided "as is" without warranty of any kind, express or implied.
Use of this software is at your own risk. The authors and contributors are not responsible for any damage, data loss, or other issues that may result from using or modifying this code.

## No Warranty
- The project is distributed for educational and informational purposes only. It may contain errors or incomplete functionality.
 
## No Liability
- Under no circumstances shall the authors or contributors be held liable for any claim, damages, or other liability arising from the use of this project.

## Use at Your Own Risk
- Always review and test the code in a safe environment before deploying in production.

## Third-Party Dependencies
- This project may rely on third-party libraries or tools. Each has its own license and terms of use which you must review and comply with.

# Contributions
**Contributions are welcome, but by submitting code you agree it may be distributed under this project’s license.**

