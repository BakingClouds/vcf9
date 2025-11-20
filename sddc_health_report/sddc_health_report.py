#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import base64
import mimetypes
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser

# =========================
# Configuration
# =========================
BASE_DIR = "/Users/talicia/sddc-health"
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
HEADER_IMG = os.path.join(BASE_DIR, "cover.png")  # PNG header image
OUT_HTML = os.path.join(BASE_DIR, f"sddc_health_unified_report_{datetime.now().strftime('%Y%m%d')}.html")

DEBUG = True

# =========================
# HTML Table Parser
# =========================
class VersionHealthTableParser(HTMLParser):
    """Parse HTML tables to extract Version Health Status data."""
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.in_header = False
        self.current_tag = None
        self.current_cell = []
        self.current_row = []
        self.headers = []
        self.rows = []
        self.table_found = False
        self.version_health_section = False
        
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ("th", "td") and self.in_row:
            self.in_cell = True
            self.current_tag = tag
            self.current_cell = []
            
    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_tag == "th" and self.current_row:
                # Check if this is the Version Health Status table
                headers_text = " ".join(self.current_row).lower()
                if "component" in headers_text and "resource" in headers_text and "version" in headers_text:
                    self.headers = self.current_row
                    self.table_found = True
                    if DEBUG:
                        print(f"[DEBUG] Found Version Health Status table with headers: {self.headers}")
            elif self.current_tag == "td" and self.table_found and self.current_row:
                self.rows.append(self.current_row[:])
            self.current_row = []
        elif tag in ("th", "td") and self.in_cell:
            self.in_cell = False
            cell_text = "".join(self.current_cell).strip()
            self.current_row.append(cell_text)
            self.current_cell = []
            
    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)

# =========================
# File Discovery
# =========================
def find_daily_report_folders():
    """Find all daily report folders matching pattern YYYY-MM-DD."""
    folders = []
    if not os.path.exists(REPORTS_DIR):
        if DEBUG:
            print(f"[WARN] Reports directory does not exist: {REPORTS_DIR}")
        return folders
    
    # Pattern for YYYY-MM-DD
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    for item in os.listdir(REPORTS_DIR):
        item_path = os.path.join(REPORTS_DIR, item)
        if os.path.isdir(item_path) and date_pattern.match(item):
            folders.append(item_path)
    
    folders.sort(reverse=True)  # Most recent first
    if DEBUG:
        print(f"[DEBUG] Found {len(folders)} daily report folders")
    return folders

def find_htm_files(folder_path):
    """Find all *.htm files in the given folder."""
    htm_files = []
    if not os.path.exists(folder_path):
        return htm_files
    
    for item in os.listdir(folder_path):
        if item.lower().endswith('.htm'):
            htm_files.append(os.path.join(folder_path, item))
    
    return htm_files

# =========================
# HTML Parsing
# =========================
def extract_sddc_name(html_content):
    """Extract SDDC name from HTML content."""
    # Try multiple patterns to find SDDC name
    # Priority order: specific SDDC patterns first, then fallback to title
    patterns = [
        # Look for "SDDC: Name" or "SDDC Name:" patterns
        r'SDDC[:\s]+([A-Za-z0-9\-_]+(?:\s*[A-Za-z0-9\-_]+)*)',
        # Look for "SDDC-Name" in title/headers
        r'<title>[^<]*(SDDC[^\s<]+(?:\s*[^\s<]+)?)[^<]*</title>',
        r'<h1>[^<]*(SDDC[^\s<]+(?:\s*[^\s<]+)?)[^<]*</h1>',
        r'<h2>[^<]*(SDDC[^\s<]+(?:\s*[^\s<]+)?)[^<]*</h2>',
        # Look for any mention in headers that might indicate SDDC
        r'<h[12]>[^<]*\s+([A-Za-z]+\-\d+)[^<]*</h[12]>',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            sddc_name = match.group(1).strip()
            # Clean up the name
            sddc_name = re.sub(r'\s+', ' ', sddc_name)
            # Remove common prefixes/suffixes
            sddc_name = re.sub(r'^(Health Check Report|Report)\s*[-:]?\s*', '', sddc_name, flags=re.IGNORECASE)
            sddc_name = re.sub(r'\s*(Health Check Report|Report)$', '', sddc_name, flags=re.IGNORECASE)
            
            if sddc_name and sddc_name.lower() not in ['health check', 'report']:
                if DEBUG:
                    print(f"[DEBUG] Extracted SDDC name: {sddc_name}")
                return sddc_name
    
    # If no SDDC name found, return a default
    return "Unknown SDDC"

def parse_htm_file(file_path):
    """Parse HTM file and extract SDDC name and Version Health Status table."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        # Extract SDDC name
        sddc_name = extract_sddc_name(html_content)
        
        # Parse Version Health Status table
        parser = VersionHealthTableParser()
        parser.feed(html_content)
        
        if not parser.table_found:
            if DEBUG:
                print(f"[WARN] No Version Health Status table found in {os.path.basename(file_path)}")
            return None
        
        return {
            'sddc_name': sddc_name,
            'file_path': file_path,
            'date': os.path.basename(os.path.dirname(file_path)),
            'headers': parser.headers,
            'rows': parser.rows
        }
    
    except Exception as e:
        if DEBUG:
            print(f"[ERROR] Failed to parse {file_path}: {e}")
        return None

# =========================
# Presentation helpers
# =========================
def image_to_data_uri(path):
    """Convert image file to data URI."""
    try:
        if not os.path.isfile(path):
            return None
        mime, _ = mimetypes.guess_type(path)
        mime = mime or "image/png"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None

def css_styles():
    """Return CSS styles for the HTML report."""
    return """
    <style>
      :root{
        --blue:#7CB8FF; --red:#F4A6A6; --grey:#eef1f5;
        --ink:#0B1B2B; --muted:#556070; --link:#0B57D0; --bg:#fbfcfe;
      }
      html, body { height:100%; }
      body { margin:0; color:var(--ink); font-family:-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; background:#fff; }

      .banner { width:100%; max-height:120px; object-fit:cover; display:block; margin-bottom:20px; }

      .container { max-width:1400px; margin:0 auto; padding:20px 40px; }

      h1 { margin:14px 0 18px; font-size:26px; color:#223; }
      h2 { margin-top:32px; margin-bottom:16px; font-size:20px; color:#334; border-bottom:2px solid var(--blue); padding-bottom:8px; }
      h3 { margin-top:20px; margin-bottom:12px; font-size:16px; color:#445; }
      p { line-height:1.6; color:var(--muted); }
      
      .report-meta { background:var(--grey); padding:16px; border-radius:8px; margin:20px 0; }
      .report-meta p { margin:6px 0; }

      .sddc-section { margin:40px 0; padding:24px; background:#f9fafb; border-radius:8px; border-left:4px solid var(--blue); }
      .sddc-name { font-size:22px; font-weight:600; color:#223; margin-bottom:16px; }
      .sddc-date { font-size:13px; color:var(--muted); margin-bottom:12px; }

      table { width:100%; border-collapse:collapse; margin-top:16px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
      th, td { padding:10px 12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:13px; }
      th { background:#f6f8fa; font-weight:600; color:#24292f; }
      tbody tr:hover { background:#f6f8fa; }
      
      .component-col { font-weight:500; color:#0969da; }
      .version-col { font-family:monospace; font-size:12px; background:#f6f8fa; padding:4px 6px; border-radius:3px; }

      .footer { margin-top:40px; padding-top:16px; border-top:1px solid #e5e7eb; text-align:center; color:var(--muted); font-size:12px; }
      
      .toc { background:#f9fafb; padding:20px; border-radius:8px; margin:24px 0; }
      .toc h2 { margin-top:0; border:none; padding:0; }
      .toc ul { list-style:none; padding:0; }
      .toc li { margin:8px 0; }
      .toc a { color:var(--link); text-decoration:none; }
      .toc a:hover { text-decoration:underline; }
    </style>
    """

# =========================
# Main
# =========================
def main():
    print("=" * 60)
    print("SDDC Health Unified Report Generator")
    print("=" * 60)
    
    # Find all daily report folders
    daily_folders = find_daily_report_folders()
    
    if not daily_folders:
        print(f"[ERROR] No daily report folders found in {REPORTS_DIR}")
        print("Expected folder pattern: YYYY-MM-DD")
        sys.exit(1)
    
    print(f"\nProcessing {len(daily_folders)} daily report folder(s)...")
    
    # Collect all SDDC data
    sddc_data = {}
    
    for folder in daily_folders:
        folder_date = os.path.basename(folder)
        if DEBUG:
            print(f"\n[DEBUG] Processing folder: {folder_date}")
        
        htm_files = find_htm_files(folder)
        if DEBUG:
            print(f"[DEBUG] Found {len(htm_files)} HTM files")
        
        for htm_file in htm_files:
            data = parse_htm_file(htm_file)
            if data:
                sddc_name = data['sddc_name']
                
                # Group by SDDC name
                if sddc_name not in sddc_data:
                    sddc_data[sddc_name] = []
                
                sddc_data[sddc_name].append(data)
    
    if not sddc_data:
        print("[ERROR] No Version Health Status tables found in any HTM files")
        sys.exit(1)
    
    print(f"\nFound data for {len(sddc_data)} SDDC(s)")
    
    # Generate HTML report
    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'>")
    html.append("<title>SDDC Health Unified Report - Bill of Materials per SDDC</title>")
    html.append(css_styles())
    html.append("</head><body>")
    
    # Header image
    banner = image_to_data_uri(HEADER_IMG)
    if banner:
        html.append(f"<img class='banner' src='{banner}' alt='Header'>")
    
    html.append("<div class='container'>")
    
    # Title
    html.append("<h1>SDDC Health Unified Report</h1>")
    html.append("<p>Bill of Materials (BOM) per SDDC - Version Health Status</p>")
    
    # Report metadata
    html.append("<div class='report-meta'>")
    html.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
    html.append(f"<p><strong>Report Folders Processed:</strong> {len(daily_folders)}</p>")
    html.append(f"<p><strong>SDDCs Found:</strong> {len(sddc_data)}</p>")
    html.append("</div>")
    
    # Table of Contents
    html.append("<div class='toc'>")
    html.append("<h2>Table of Contents</h2>")
    html.append("<ul>")
    for sddc_name in sorted(sddc_data.keys()):
        anchor = re.sub(r'[^a-zA-Z0-9]+', '-', sddc_name).lower().strip('-')
        html.append(f"<li><a href='#{anchor}'>{sddc_name}</a></li>")
    html.append("</ul>")
    html.append("</div>")
    
    # SDDC sections
    for sddc_name in sorted(sddc_data.keys()):
        anchor = re.sub(r'[^a-zA-Z0-9]+', '-', sddc_name).lower().strip('-')
        reports = sddc_data[sddc_name]
        
        html.append(f"<div class='sddc-section' id='{anchor}'>")
        html.append(f"<div class='sddc-name'>{sddc_name}</div>")
        
        # Process each report for this SDDC
        for report in reports:
            html.append(f"<div class='sddc-date'>Report Date: {report['date']}</div>")
            
            # Build table
            if report['rows']:
                html.append("<table>")
                html.append("<thead><tr>")
                for header in report['headers']:
                    html.append(f"<th>{header}</th>")
                html.append("</tr></thead>")
                html.append("<tbody>")
                
                for row in report['rows']:
                    html.append("<tr>")
                    for i, cell in enumerate(row):
                        # Add special styling for component and version columns
                        if i == 0:  # First column (Component)
                            html.append(f"<td class='component-col'>{cell}</td>")
                        elif i == len(row) - 1:  # Last column (Version)
                            html.append(f"<td><span class='version-col'>{cell}</span></td>")
                        else:
                            html.append(f"<td>{cell}</td>")
                    html.append("</tr>")
                
                html.append("</tbody></table>")
            else:
                html.append("<p><em>No version data available</em></p>")
        
        html.append("</div>")  # sddc-section
    
    # Footer
    html.append("<div class='footer'>")
    html.append("<p>SDDC Health Unified Report | Generated from daily health check reports</p>")
    html.append(f"<p>Report locations: {REPORTS_DIR}</p>")
    html.append("</div>")
    
    html.append("</div>")  # container
    html.append("</body></html>")
    
    # Write output
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    
    print(f"\n{'=' * 60}")
    print("Report generated successfully!")
    print(f"Output file: {OUT_HTML}")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    main()
