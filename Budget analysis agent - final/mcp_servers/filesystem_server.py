"""
Filesystem MCP Server
----------------------
Gives the agent secure, read-only access to a local "Documents" folder
containing bank statements, credit card statements, and expense sheets.

Exposes tools:
  - list_documents()            -> list files available to read
  - read_statement(filename)    -> parses PDF / CSV / XLSX into structured
                                    transaction rows (date, description, amount)

"""

import os
import sys

import pdfplumber
import pandas as pd
from mcp.server.fastmcp import FastMCP

# Root folder the server is allowed to read from. Nothing outside this
# directory is ever touched - keeps the "secure" promise in the spec.
DOCUMENTS_DIR = os.environ.get(
    "BUDGET_AGENT_DOCUMENTS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents"),
)

mcp = FastMCP("filesystem-mcp")


def _safe_path(filename: str) -> str:
    """Resolve filename inside DOCUMENTS_DIR only, blocking path traversal."""
    full = os.path.abspath(os.path.join(DOCUMENTS_DIR, filename))
    root = os.path.abspath(DOCUMENTS_DIR)
    if not (full == root or full.startswith(root + os.sep)):
        raise ValueError("Access outside the documents directory is not allowed.")
    if not os.path.exists(full):
        raise FileNotFoundError(f"{filename} not found in documents directory.")
    return full


def _parse_csv(path: str) -> list[dict]:
    df = pd.read_csv(path)
    return _normalize_dataframe(df)


def _parse_excel(path: str) -> list[dict]:
    df = pd.read_excel(path)
    return _normalize_dataframe(df)


def _normalize_dataframe(df: pd.DataFrame) -> list[dict]:
    """Best-effort mapping of arbitrary bank export columns onto
    date / description / amount, since every bank names columns differently."""
    cols = {c.lower().strip(): c for c in df.columns}

    def find(*candidates):
        for cand in candidates:
            for lower, orig in cols.items():
                if cand in lower:
                    return orig
        return None

    date_col = find("date")
    desc_col = find("description", "merchant", "narration", "particulars", "details")
    amount_col = find("amount", "debit", "value", "withdrawal")

    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "date": str(r[date_col]) if date_col else None,
                "description": str(r[desc_col]) if desc_col else None,
                "amount": _to_float(r[amount_col]) if amount_col else None,
            }
        )
    return rows


def _to_float(val) -> float | None:
    try:
        return float(str(val).replace(",", "").replace("₹", "").strip())
    except (ValueError, TypeError):
        return None


def _parse_pdf(path: str) -> list[dict]:
    """Pulls tables out of a PDF bank statement. Only table-based extraction
    is supported here - scanned/image PDFs would need OCR added."""
    rows: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                header = [str(h).lower().strip() if h else "" for h in table[0]]
                for line in table[1:]:
                    record = dict(zip(header, line))
                    date_val = next((v for k, v in record.items() if "date" in k), None)
                    desc_val = next(
                        (v for k, v in record.items() if any(x in k for x in ["desc", "particular", "narration", "merchant"])),
                        None,
                    )
                    amt_val = next((v for k, v in record.items() if any(x in k for x in ["amount", "debit", "withdraw"])), None)
                    if date_val or desc_val or amt_val:
                        rows.append({"date": date_val, "description": desc_val, "amount": _to_float(amt_val)})
    return rows


@mcp.tool()
def list_documents() -> list[dict]:
    """List every statement/expense file available in the documents folder,
    with its size in bytes and detected type."""
    if not os.path.isdir(DOCUMENTS_DIR):
        return []
    out = []
    for f in sorted(os.listdir(DOCUMENTS_DIR)):
        full = os.path.join(DOCUMENTS_DIR, f)
        if os.path.isfile(full):
            out.append(
                {
                    "filename": f,
                    "size_bytes": os.path.getsize(full),
                    "type": os.path.splitext(f)[1].lstrip(".").lower(),
                }
            )
    return out


@mcp.tool()
def read_statement(filename: str) -> dict:
    """Read a bank statement / credit card statement / expense sheet and
    return its transactions as structured rows: date, description, amount.

    Supports .pdf, .csv, .xlsx, .xls. Column names vary bank to bank; this
    tool does its best to map them onto a common schema.
    """
    path = _safe_path(filename)
    ext = os.path.splitext(path)[1].lower()

    if ext == ".csv":
        transactions = _parse_csv(path)
    elif ext in (".xlsx", ".xls"):
        transactions = _parse_excel(path)
    elif ext == ".pdf":
        transactions = _parse_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return {
        "filename": filename,
        "transaction_count": len(transactions),
        "transactions": transactions,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
