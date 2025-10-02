#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, csv, io, re, base64, mimetypes
from math import cos, sin, pi
from datetime import datetime

# =========================
# Configuration
# =========================
BASE_DIR   = "PATH TO YOUR BASE DIRECTORY"  # adjust as needed
HCL_DIR    = os.path.join(BASE_DIR, "NAME OF HCL DIRECTORY") # adjust as needed
# We’ll auto-find a Systems*.csv in the HCL_DIR
HEADER_IMG = os.path.join(BASE_DIR, "cover.png")  # optional header image, adjust as needed
OUT_HTML   = os.path.join(BASE_DIR, f"vcf9_cpu_support_report_{datetime.now().strftime('%Y%m%d')}.html")

# Inventory search (e.g., “Sep 2025 Host Inventory.csv” or similar)
INV_SEARCH_DIRS = [BASE_DIR]

DEBUG = True

# =========================
# File discovery
# =========================
def find_hcl_file():
    """Find Systems*.csv in the HCL_DIR (tolerates spaces)."""
    try:
        for fname in sorted(os.listdir(HCL_DIR)):
            low = fname.lower().replace(" ", "")
            if low.startswith("systems") and low.endswith(".csv"):
                path = os.path.join(HCL_DIR, fname)
                if DEBUG: print("[HCL] Using:", path)
                return path
    except FileNotFoundError:
        pass
    return None

def find_inventory_file():
    """Find a Host Inventory CSV (accepts 'inventory' or common typo 'invenotry')."""
    for folder in INV_SEARCH_DIRS:
        try:
            for fname in sorted(os.listdir(folder)):
                low = fname.lower().replace(" ", "")
                if fname.lower().endswith(".csv") and ("host" in low) and ("inventory" in low or "invenotry" in low):
                    path = os.path.join(folder, fname)
                    if DEBUG: print("[INV] Using:", path)
                    return path
        except FileNotFoundError:
            continue
    return None

# =========================
# Robust CSV loading
# =========================
def read_text_bytes(path):
    with open(path, "rb") as f: return f.read()

def decode_text_safely(raw_bytes):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try: return raw_bytes.decode(enc)
        except UnicodeDecodeError: continue
    return raw_bytes.decode("utf-8", errors="replace")

def normalise_key(k: str) -> str:
    if k is None: return ""
    k = str(k).replace("\ufeff", "")
    k = re.sub(r"\s+", " ", k).strip()
    return k.lower().replace(" ", "_")

def coerce_cell(v):
    if v is None: return ""
    if isinstance(v, list): return " | ".join(coerce_cell(x) for x in v)
    return str(v).strip()

def try_parse_with_delim(text, delim):
    f = io.StringIO(text, newline="")
    reader = csv.DictReader(f, delimiter=delim)
    rows = [dict(r) for r in reader]
    if not rows or len(rows[0].keys()) <= 1: return None, None
    valid_headers = [h for h in rows[0].keys() if h and str(h).strip()]
    norm_map = {h: normalise_key(h) for h in valid_headers}
    norm_headers = [norm_map[h] for h in valid_headers]
    norm_rows = []
    for r in rows:
        nr = {}
        for h, v in r.items():
            if h in norm_map: nr[norm_map[h]] = coerce_cell(v)
        norm_rows.append(nr)
    return norm_rows, norm_headers

def load_csv_robust(path):
    if not os.path.isfile(path): return [], []
    text = decode_text_safely(read_text_bytes(path))
    if not text: return [], []
    first_line = text.splitlines()[0] if text.splitlines() else ""
    prefer_pipe = ("|" in first_line and first_line.count("|") >= 1)
    delimiters = ["|", ",", ";", "\t"] if prefer_pipe else [",", ";", "\t", "|"]
    for d in delimiters:
        rows, headers = try_parse_with_delim(text, d)
        if rows:
            if DEBUG: print(f"[CSV] Using delimiter '{d}' for {os.path.basename(path)}")
            return rows, headers
    if "|" in first_line:
        rows, headers = try_parse_with_delim(text, "|")
        if rows: return rows, headers
    return [], []

def pick_column(headers, candidates):
    hset = set(headers)
    for cand in candidates:
        c = normalise_key(cand)
        if c in hset: return c
    for h in headers:
        for cand in candidates:
            c = normalise_key(cand)
            if h == c or h.startswith(c) or c in h: return h
    return None

# =========================
# Classification
# =========================
def classify_support(release_str: str) -> str:
    """
    OK if 'ESXi 9.0' appears. Otherwise treat as Blocked (8.x-only, deprecated, not listed, unknown).
    """
    if not release_str: return "Blocked"
    t = release_str.replace("\u00A0", " ").lower().strip()
    if "esxi 9.0" in t: return "OK"
    # Everything else treated as blocked for upgrade readiness (planning perspective)
    return "Blocked"

# =========================
# Matching helpers
# =========================
def norm_cpu(s: str) -> str:
    if not s: return ""
    x = s.replace("®","").replace("(R)","").replace("(r)","")
    x = re.sub(r"@\s*[\d\.]+\s*ghz", "", x, flags=re.I)
    return re.sub(r"\s+"," ", x).strip().lower()

def norm_model(s: str) -> str:
    if not s: return ""
    return re.sub(r"\s+"," ", s).strip().lower()

def vendor_from_model(model: str) -> str:
    if not model: return "Other"
    m = model.lower()
    if m.startswith("dell") or "vxrail" in m: return "Dell"
    if m.startswith("cisco"): return "Cisco"
    if m.startswith("hpe") or m.startswith("hewlett") or m.startswith("hp "): return "HPE / HP"
    if m.startswith("lenovo"): return "Lenovo"
    if m.startswith("vmware"): return "VMware"
    return "Other"

# =========================
# Presentation helpers
# =========================
def image_to_data_uri(path):
    try:
        if not os.path.isfile(path): return None
        mime, _ = mimetypes.guess_type(path)
        mime = mime or "image/png"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None

def css_styles():
    return """
    <style>
      :root{
        --blue:#7CB8FF; --red:#F4A6A6; --grey:#eef1f5;
        --ink:#0B1B2B; --muted:#556070; --link:#0B57D0; --bg:#fbfcfe;
      }
      html, body { height:100%; }
      body { margin:0; color:var(--ink); font-family:-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; background:#fff; }

      .banner { width:100%; max-height:120px; object-fit:cover; display:block; }

      /* Layout with fixed left sidebar */
      .layout { display:flex; min-height:100vh; }
      .sidebar {
        position:sticky; top:0; align-self:flex-start;
        width:220px; min-height:100vh; padding:18px 16px 28px; background:var(--bg);
        border-right:1px solid #eef0f2;
      }
      .sidebar h3 { margin:8px 0 10px; font-size:14px; color:#223; }
      .sidebar a { display:block; padding:8px 8px; margin:4px 0; text-decoration:none; color:var(--link); border-radius:8px; }
      .sidebar a:hover { background:#eef6ff; }
      .content { flex:1; padding:16px 24px 40px; }

      h1 { margin:14px 0 18px; font-size:26px; }
      h2 { margin-top:28px; font-size:18px; }
      h3 { margin-top:16px; font-size:15px; }
      p { line-height:1.55; }
      .muted, .footer { color:var(--muted); }
      .tiny { font-size:11px; color:#66707a; }

      .callout {
        background:#f0f7ff; border-left:4px solid #005599; padding:12px 14px; border-radius:6px; margin:14px 0;
      }

      table { width:100%; border-collapse:collapse; margin-top:10px; }
      th, td { padding:8px 10px; border-bottom:1px solid #eee; text-align:left; font-size:13px; }
      th { background:#f6f6f6; }

      .ok-row { background:#EAF5FF; }
      .blocked-row { background:#FDECEC; }

      .legend2 div { margin:4px 0; }
      .chip { display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:6px; vertical-align:middle; background:#e5e7eb; }
      .chip.ok { background:var(--blue); }
      .chip.blocked { background:var(--red); }

      .kpi { display:flex; align-items:center; gap:18px; flex-wrap:wrap; }
      .pie { width:160px; height:160px; }
      .vendor-title { margin-top:22px; font-size:16px; font-weight:600; }

      .footer { margin-top:28px; padding-top:12px; border-top:1px solid #e5e5e5; }
    </style>
    """

# ---------- PIE CHART (OK vs Blocked) ----------
def _polar(xc, yc, r, ang_deg):
    a = (ang_deg - 90) * (pi/180.0)
    return (xc + r*cos(a), yc + r*sin(a))

def _arc_path(xc, yc, r, start_deg, sweep_deg):
    end_deg = start_deg + sweep_deg
    x1, y1 = _polar(xc, yc, r, start_deg)
    x2, y2 = _polar(xc, yc, r, end_deg)
    laf = 1 if abs(sweep_deg) > 180 else 0
    sf = 1 if sweep_deg >= 0 else 0
    return f"M {xc},{yc} L {x1:.3f},{y1:.3f} A {r},{r} 0 {laf} {sf} {x2:.3f},{y2:.3f} Z"

def pie_svg_two(ok, blocked, size=160, colors=("var(--blue)", "var(--red)")):
    total = ok + blocked
    if total <= 0: total = 1
    cx = cy = size/2
    r = size*0.48

    p_ok = ok/total * 360.0
    p_blk = 360.0 - p_ok

    parts, start = [], 0.0
    if ok > 0:
        parts.append(f"<path d='{_arc_path(cx, cy, r, start, p_ok)}' fill='{colors[0]}'/>")
        start += p_ok
    if blocked > 0:
        parts.append(f"<path d='{_arc_path(cx, cy, r, start, p_blk)}' fill='{colors[1]}'/>")

    ring = f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#ffffff' stroke-width='1'/>"
    return f"<svg viewBox='0 0 {size} {size}' class='pie'>{''.join(parts)}{ring}</svg>"

# =========================
# Main
# =========================
def main():
    # Find input files
    hcl_file = find_hcl_file()
    if not hcl_file:
        print("[ERROR] Could not find Systems*.csv in", HCL_DIR)
        sys.exit(1)
    inv_file = find_inventory_file()

    # Load HCL systems CSV
    hcl_rows, hcl_headers = load_csv_robust(hcl_file)
    if not hcl_rows:
        print("[ERROR] Could not parse the HCL systems CSV.")
        sys.exit(1)

    # Map columns
    model_col = pick_column(hcl_headers, ["Model","Server Model","Product","Model Name"])
    cpu_col   = pick_column(hcl_headers, ["CPU Model","CPU","Processor"])
    code_col  = pick_column(hcl_headers, ["Code Name","Codename"])
    rel_col   = pick_column(hcl_headers, ["Supported Releases","Supported versions","Releases","SupportedRelease"])
    missing = [lab for lab,col in [("Model",model_col),("CPU Model",cpu_col),("Supported Releases",rel_col)] if not col]
    if missing:
        print("ERROR: Required columns not found in your HCL CSV:", ", ".join(missing))
        print("Found (normalised) headers:", hcl_headers); sys.exit(1)

    # Build enriched HCL dataset
    enriched = []
    for r in hcl_rows:
        model = r.get(model_col,""); cpu = r.get(cpu_col,"")
        code  = r.get(code_col,"") if code_col else ""
        rels  = r.get(rel_col,"")
        status = classify_support(rels)
        enriched.append({
            "Model": model,
            "CPU Model": cpu,
            "Code Name": code,
            "Supported Releases": rels,
            "Status": status,
            "Vendor": vendor_from_model(model)
        })

    # Inventory data (for server names in appendix)
    inv_rows, inv_headers = [], []
    if inv_file:
        inv_rows, inv_headers = load_csv_robust(inv_file)
        if not inv_rows:
            print("[WARN] Could not parse the Host Inventory CSV - Appendix will omit server names.")

    inv_name_col  = pick_column(inv_headers, ["Name","Hostname","Host Name"])
    inv_model_col = pick_column(inv_headers, ["Model"])
    inv_cpu_col   = pick_column(inv_headers, ["CPU Model","Processor"])

    # Build lookup for appendix: (model, cpu) -> rows
    hcl_lookup = {}
    for x in enriched:
        hcl_lookup.setdefault((norm_model(x["Model"]), norm_cpu(x["CPU Model"])), []).append(x)

    appendix = []
    if inv_rows and inv_name_col and inv_model_col and inv_cpu_col:
        for r in inv_rows:
            name = r.get(inv_name_col,""); imodel = r.get(inv_model_col,""); icpu = r.get(inv_cpu_col,"")
            k = (norm_model(imodel), norm_cpu(icpu))
            match = hcl_lookup.get(k)
            chosen = match[0] if match else None
            if not chosen:
                # relaxed: same model; CPU substring overlap either way
                nm, nc = k
                for key, cands in hcl_lookup.items():
                    km, kc = key
                    if km == nm and (nc in kc or kc in nc):
                        chosen = cands[0]; break
            if chosen:
                appendix.append({
                    "Name": name,
                    "Model": chosen["Model"] or imodel,
                    "CPU Model": chosen["CPU Model"] or icpu,
                    "Code Name": chosen["Code Name"],
                    "Supported Releases": chosen["Supported Releases"],
                    "Status": chosen["Status"]
                })
            else:
                appendix.append({
                    "Name": name, "Model": imodel, "CPU Model": icpu,
                    "Code Name": "", "Supported Releases": "", "Status": "Blocked"  # conservative for planning
                })
    else:
        for x in enriched:
            appendix.append({
                "Name": "",
                "Model": x["Model"],
                "CPU Model": x["CPU Model"],
                "Code Name": x["Code Name"],
                "Supported Releases": x["Supported Releases"],
                "Status": x["Status"]
            })

    # Summary counts (OK vs Blocked) for HCL-only section
    ok_count = sum(1 for x in enriched if x["Status"] == "OK")
    blocked_count = sum(1 for x in enriched if x["Status"] == "Blocked")
    total_count = ok_count + blocked_count if (ok_count + blocked_count) > 0 else 1
    pct_ok = f"{(ok_count/total_count*100):.1f}%"

    # Appendix counts (based on full inventory mapping)
    inv_ok = sum(1 for r in appendix if r["Status"] == "OK")
    inv_blocked = sum(1 for r in appendix if r["Status"] == "Blocked")
    inv_total = inv_ok + inv_blocked if (inv_ok + inv_blocked) > 0 else 1
    inv_pct_ok = f"{(inv_ok/inv_total*100):.1f}%"

    # Build HTML
    banner = image_to_data_uri(HEADER_IMG)

    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'>")
    html.append("<title>VCF 9.0 Hardware Compatibility — Hardware Compatibility Guide Snapshot</title>")
    html.append(css_styles())
    html.append("</head><body>")

    if banner:
        html.append(f"<img class='banner' src='{banner}' alt='Cover'>")

    html.append("<div class='layout'>")

    # Sidebar (sticky)
    html.append("""
      <nav class="sidebar" aria-label="Contents">
        <h3>Contents</h3>
        <a href="#overview">Report Overview</a>
        <a href="#lifecycle">VMware vSphere 8 Lifecycle and Upgrade Planning</a>
        <a href="#summary">Hardware Compatibility Guide Support Summary</a>
        <a href="#detail">Per-entry Detail (by Vendor)</a>
        <a href="#appendix">Appendix: Full Inventory</a>
      </nav>
    """)

    # Main content
    html.append("<main class='content'>")
    html.append("<h1>VCF 9.0 Hardware Compatibility — Hardware Compatibility Guide Snapshot</h1>")

    # Report Overview + BCG context callout
    html.append('<section id="overview">')
    html.append("<h2>Report Overview</h2>")
    html.append("""
    With the release of VMware Cloud Foundation (VCF) 9.0, 
    one of the pre-checks is to confirm hardware compatibility. This report provides a current snapshot of compatibility 
    based on inventory extracted from VCF Operations and verified against the official 
    <a href="https://compatibilityguide.broadcom.com/" target="_blank">Broadcom Hardware Compatibility Guide</a>.
    """)
    html.append("""
    <div class="callout">
      <b>Important context:</b><br>
      The Broadcom Compatibility Guide (BCG) has recently been updated to include a preliminary set of devices for VCF 9.0. 
      This is a company first, as the BCG is typically only released at GA, which can make planning hardware refresh more difficult.<br><br>
      It is very important to understand that VMware/Broadcom <b>does not certify hardware or I/O devices</b>. 
      OEM partners ultimately decide which devices to certify for each release, and they may choose not to re-certify devices 
      for reasons such as earlier end-of-sales or end-of-life support. This is not unique to VCF 9.0, and it applies both pre- and post-acquisition of VMware.<br><br>
    </div>
    <p>
      <b>Note:</b> This is a point-in-time view. The Broadcom Compatibility Guide is updated frequently. 
      It remains the customer’s responsibility to validate the hardware status directly against the official guide prior to upgrades or procurement.
      <br><br>
      References: <a href="https://compatibilityguide.broadcom.com/" target="_blank">Broadcom Compatibility Guide</a> &nbsp;|&nbsp; 
      <a href="https://knowledge.broadcom.com/external/article/318697" target="_blank">KB 318697</a> &nbsp;|&nbsp; 
      <a href="https://knowledge.broadcom.com/external/article/391170" target="_blank">KB 391170</a>
    </p>
    """)
    html.append("</section>")

    # vSphere 8 lifecycle
    html.append('<section id="lifecycle">')
    html.append("<h2>VMware vSphere 8 Lifecycle and Upgrade Planning</h2>")
    html.append("""
    <div class="callout">
      VMware vSphere 8.0 (released 11 October 2022) follows VMware’s standard lifecycle policy:<br>
      • <b>End of General Support (EoGS):</b> 11 October 2027<br>
      • <b>End of Technical Guidance (EoTG):</b> 11 October 2029<br><br>
   
    </div>
    """)
    html.append("</section>")

    # HCL Summary (pie OK vs Blocked)
    html.append('<section id="summary">')
    html.append("<h2>Hardware Compatibility Guide Support Summary</h2>")
    html.append("""
    This section summarises installation readiness for <b>vSphere 9.0</b> using the Broadcom Compatibility Guide. 
    <i>OK</i> means the server/CPU combination appears as installable on ESXi 9.0 in the guide. 
    <i>Blocked</i> means the guide caps support at ESXi 8.x or the CPU family is discontinued in 9.x, so the installer will block. 
    If a system does not show as OK, treat it as not ready for VCF 9.0 until confirmed otherwise with your OEM or the guide.
    """)
    pie = pie_svg_two(ok_count, blocked_count, size=160)
    html.append("<div class='kpi'>")
    html.append(pie)
    html.append(f"""
      <div class="legend2" aria-label="Summary figures">
        <div><span class="chip ok"></span> OK: <b>{ok_count}</b> ({pct_ok})</div>
        <div><span class="chip blocked"></span> Blocked: <b>{blocked_count}</b></div>
        <div>Total hardware models analysed: <b>{ok_count + blocked_count}</b></div>
      </div>
    """)
    html.append("</div>")
    html.append("</section>")

    # Detail by vendor
    html.append('<section id="detail">')
    html.append("<h2>Detail by Vendor</h2>")
    vendors = ["Dell","Cisco","HPE / HP","Lenovo","VMware","Other"]
    groups = {v: [] for v in vendors}
    for x in enriched: groups.setdefault(x["Vendor"], []).append(x)

    for v in vendors:
        items = groups.get(v, [])
        if not items: continue
        html.append(f"<div class='vendor-title'>{v}</div>")
        html.append("<table><thead><tr>"
                    "<th>Model</th><th>CPU Model</th><th>Code Name</th><th>Supported Releases</th><th>Status</th>"
                    "</tr></thead><tbody>")
        items.sort(key=lambda r: (r["Model"], r["CPU Model"]))
        for x in items:
            cls = "ok-row" if x["Status"] == "OK" else "blocked-row"
            html.append(
                f"<tr class='{cls}'>"
                f"<td>{x['Model']}</td>"
                f"<td>{x['CPU Model']}</td>"
                f"<td>{x['Code Name']}</td>"
                f"<td>{x['Supported Releases']}</td>"
                f"<td>{x['Status']}</td>"
                "</tr>"
            )
        html.append("</tbody></table>")
    html.append("</section>")

    # Appendix — full inventory with names + PIE
    html.append('<section id="appendix">')
    html.append("<h2>Appendix: Full Inventory with Server Names</h2>")
    html.append("""
    This appendix lists the full server inventory extracted from VCF Operations, matched against the Broadcom Compatibility Guide where possible.
    The chart below summarises the percentage of servers in the inventory that support vSphere 9.0 (OK) versus those that do not (Blocked).
    """)

    # Inventory pie chart (SVG)
    inv_pie_svg = pie_svg_two(inv_ok, inv_blocked, size=160)
    html.append("<div class='kpi'>")
    html.append(inv_pie_svg)
    html.append(f"""
      <div class="legend2" aria-label="Inventory summary">
        <div><span class="chip ok"></span> OK: <b>{inv_ok}</b> ({inv_pct_ok})</div>
        <div><span class="chip blocked"></span> Blocked: <b>{inv_blocked}</b></div>
        <div>Total in inventory: <b>{inv_ok + inv_blocked}</b></div>
      </div>
    """)
    html.append("</div>")

    # Inventory table
    html.append("<table><thead><tr>"
                "<th>Name</th><th>Model</th><th>CPU Model</th><th>Code Name</th><th>Supported Releases</th><th>Status</th>"
                "</tr></thead><tbody>")
    for r in appendix:
        cls = "ok-row" if r["Status"] == "OK" else "blocked-row"
        html.append(
            f"<tr class='{cls}'>"
            f"<td>{r.get('Name','')}</td>"
            f"<td>{r.get('Model','')}</td>"
            f"<td>{r.get('CPU Model','')}</td>"
            f"<td>{r.get('Code Name','')}</td>"
            f"<td>{r.get('Supported Releases','')}</td>"
            f"<td>{r.get('Status','Blocked')}</td>"
            "</tr>"
        )
    html.append("</tbody></table>")
    html.append("</section>")

    # Footer
    generated_when = datetime.now().strftime('%d %B %Y, %H:%M')
    html.append(f"""
      <div class="footer tiny">
        Generated: {generated_when} &nbsp;|&nbsp; Generated by YOUR_NAME_OR_ORG HERE
      </div>
    """)
    html.append("</main></div>")  # content + layout
    html.append("</body></html>")

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print("Report written to:\n ", OUT_HTML)

if __name__ == "__main__":
    main()
