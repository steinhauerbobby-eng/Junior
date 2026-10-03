"""
Local Excel MCP server — create and read Excel workbooks using openpyxl.
Saves files to the reports/ directory.
Run as: python src/data/excel_client.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

REPORTS_DIR = Path(__file__).parents[2] / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Color palette
HEADER_FILL = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
SUBJECT_FILL = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
ALT_FILL = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
SUBJECT_FONT = Font(bold=True, size=10)
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


def write_comps(ticker: str, data: list[dict], metrics: list[str]) -> dict:
    """
    Write a comparable company analysis to Excel.

    data: list of dicts, first entry is the subject company (ticker)
    metrics: ordered list of metric names matching keys in data dicts
    """
    filename = f"comps-{ticker}-{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = REPORTS_DIR / filename

    wb = openpyxl.Workbook()

    # --- Sheet 1: Comps Table ---
    ws = wb.active
    ws.title = "Comps"

    # Header row
    headers = ["Company"] + metrics + ["vs. Median"]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = THIN_BORDER
    ws.row_dimensions[1].height = 30

    # Data rows
    for row_idx, company in enumerate(data, start=2):
        is_subject = row_idx == 2
        fill = SUBJECT_FILL if is_subject else (ALT_FILL if row_idx % 2 == 0 else None)
        font = SUBJECT_FONT if is_subject else Font(size=10)

        ws.cell(row=row_idx, column=1, value=company.get("ticker", "")).font = font
        if fill:
            ws.cell(row=row_idx, column=1).fill = fill

        for col_idx, metric in enumerate(metrics, start=2):
            cell = ws.cell(row=row_idx, column=col_idx, value=company.get(metric))
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center")
            if fill:
                cell.fill = fill
            if is_subject:
                cell.font = SUBJECT_FONT

        # vs. Median column (placeholder — calculated after all rows written)
        ws.cell(row=row_idx, column=len(headers)).border = THIN_BORDER

    # Auto-size columns
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 20)

    ws.freeze_panes = "B2"

    # --- Sheet 2: Raw Data ---
    ws2 = wb.create_sheet("Raw Data")
    ws2.cell(row=1, column=1, value=f"Generated: {datetime.now().isoformat()}")
    ws2.cell(row=1, column=2, value=f"Subject: {ticker}")
    ws2.cell(row=2, column=1, value="Ticker")
    for col_idx, metric in enumerate(metrics, start=2):
        ws2.cell(row=2, column=col_idx, value=metric)
    for row_idx, company in enumerate(data, start=3):
        ws2.cell(row=row_idx, column=1, value=company.get("ticker", ""))
        for col_idx, metric in enumerate(metrics, start=2):
            ws2.cell(row=row_idx, column=col_idx, value=company.get(metric))

    wb.save(filepath)
    return {"file": str(filepath), "filename": filename, "rows": len(data)}


def write_generic(filename: str, sheets: list[dict]) -> dict:
    """
    Write a generic Excel workbook.
    sheets: list of {name, headers, rows} dicts
    """
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"
    filepath = REPORTS_DIR / filename
    wb = openpyxl.Workbook()

    for sheet_idx, sheet in enumerate(sheets):
        ws = wb.active if sheet_idx == 0 else wb.create_sheet()
        ws.title = sheet.get("name", f"Sheet{sheet_idx+1}")[:31]

        headers = sheet.get("headers", [])
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.border = THIN_BORDER

        for row_idx, row in enumerate(sheet.get("rows", []), start=2):
            for col_idx, val in enumerate(row, start=1):
                ws.cell(row=row_idx, column=col_idx, value=val).border = THIN_BORDER

        for col in ws.columns:
            max_len = max((len(str(cell.value or "")) for cell in col), default=10)
            ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 25)

    wb.save(filepath)
    return {"file": str(filepath), "filename": filename}


def read_excel(filename: str) -> dict:
    filepath = REPORTS_DIR / filename
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}
    wb = openpyxl.load_workbook(filepath)
    result = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = [[cell.value for cell in row] for row in ws.iter_rows()]
        result[sheet_name] = rows
    return {"file": str(filepath), "sheets": result}


def list_reports() -> dict:
    files = sorted(REPORTS_DIR.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True)
    return {
        "reports_dir": str(REPORTS_DIR),
        "files": [{"name": f.name, "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")} for f in files],
    }


TOOLS = {
    "write_comps": write_comps,
    "write_generic": write_generic,
    "read_excel": read_excel,
    "list_reports": list_reports,
}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            tool = request.get("tool")
            params = request.get("params", {})
            if tool in TOOLS:
                result = TOOLS[tool](**params)
                print(json.dumps({"result": result}), flush=True)
            else:
                print(json.dumps({"error": f"Unknown tool: {tool}"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
