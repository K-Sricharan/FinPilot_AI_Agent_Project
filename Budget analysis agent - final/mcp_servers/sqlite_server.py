"""
SQLite MCP Server
------------------
Owns the transactions database. The agent never writes SQL files or opens
the DB directly - it calls these tools instead.

Exposes tools:
  - insert_transactions(transactions)   -> bulk insert categorized rows
  - query_summary(category, month)      -> totals, optionally filtered
  - monthly_comparison(month_a, month_b)-> category-by-category diff
  - list_recurring_merchants()          -> merchants appearing 2+ months running
  - run_query(sql)                      -> read-only escape hatch (SELECT only)
"""

import os
import re
import sqlite3
from typing import Optional

from mcp.server.fastmcp import FastMCP

DB_PATH = os.environ.get(
    "BUDGET_AGENT_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "transactions.db"),
)

mcp = FastMCP("sqlite-mcp")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            month TEXT,
            merchant TEXT,
            description TEXT,
            category TEXT,
            amount REAL,
            source_file TEXT
        )
        """
    )
    return conn


@mcp.tool()
def insert_transactions(transactions: list[dict], source_file: Optional[str] = None) -> dict:
    """Bulk-insert categorized transactions.

    Each transaction dict should have: date, merchant, description,
    category, amount. `month` is derived automatically from date
    (format YYYY-MM) so trend queries work without extra input.
    """
    conn = _conn()
    inserted = 0
    for t in transactions:
        month = _extract_month(t.get("date"))
        conn.execute(
            "INSERT INTO transactions (date, month, merchant, description, category, amount, source_file) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                t.get("date"),
                month,
                t.get("merchant"),
                t.get("description"),
                t.get("category"),
                t.get("amount"),
                source_file,
            ),
        )
        inserted += 1
    conn.commit()
    conn.close()
    return {"inserted": inserted}


def _extract_month(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    m = re.search(r"(\d{4})-(\d{2})", date_str)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return date_str[:7] if len(date_str) >= 7 else None


@mcp.tool()
def query_summary(category: Optional[str] = None, month: Optional[str] = None) -> dict:
    """Get total spend, optionally filtered by category and/or month (YYYY-MM).
    Also returns a per-category breakdown when no category filter is given."""
    conn = _conn()
    where, params = [], []
    if category:
        where.append("category = ?")
        params.append(category)
    if month:
        where.append("month = ?")
        params.append(month)
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    total = conn.execute(f"SELECT COALESCE(SUM(amount),0) FROM transactions {clause}", params).fetchone()[0]

    breakdown = conn.execute(
        f"SELECT category, SUM(amount), COUNT(*) FROM transactions {clause} GROUP BY category ORDER BY SUM(amount) DESC",
        params,
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "breakdown": [{"category": c, "total": t, "count": n} for c, t, n in breakdown],
    }


@mcp.tool()
def monthly_comparison(month_a: str, month_b: str) -> dict:
    """Compare category spend between two months (YYYY-MM each). Returns
    per-category totals for both months and the percentage change."""
    conn = _conn()

    def totals_for(month):
        rows = conn.execute(
            "SELECT category, SUM(amount) FROM transactions WHERE month = ? GROUP BY category", (month,)
        ).fetchall()
        return {c: t for c, t in rows}

    a, b = totals_for(month_a), totals_for(month_b)
    conn.close()

    categories = sorted(set(a) | set(b))
    comparison = []
    for cat in categories:
        va, vb = a.get(cat, 0) or 0, b.get(cat, 0) or 0
        pct = ((vb - va) / va * 100) if va else (100.0 if vb else 0.0)
        comparison.append({"category": cat, month_a: va, month_b: vb, "pct_change": round(pct, 1)})
    return {"month_a": month_a, "month_b": month_b, "comparison": comparison}


@mcp.tool()
def list_recurring_merchants(min_months: int = 2) -> list[dict]:
    """Detect likely subscriptions: merchants with a charge in at least
    `min_months` distinct months, with roughly the same amount each time."""
    conn = _conn()
    rows = conn.execute(
        """
        SELECT merchant, COUNT(DISTINCT month) as months, AVG(amount) as avg_amount,
               MIN(amount) as min_amount, MAX(amount) as max_amount
        FROM transactions
        WHERE merchant IS NOT NULL
        GROUP BY merchant
        HAVING months >= ?
        ORDER BY months DESC
        """,
        (min_months,),
    ).fetchall()
    conn.close()
    return [
        {
            "merchant": m,
            "months_seen": mo,
            "avg_amount": round(avg, 2),
            "amount_range": [mn, mx],
        }
        for m, mo, avg, mn, mx in rows
    ]


@mcp.tool()
def run_query(sql: str) -> list[dict]:
    """Read-only escape hatch for ad-hoc questions the other tools don't
    cover. Only SELECT statements against the `transactions` table are
    allowed - anything else is rejected."""
    stripped = sql.strip().rstrip(";")
    if not re.match(r"(?is)^select\b", stripped):
        raise ValueError("Only SELECT queries are permitted.")
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|attach|pragma)\b", stripped):
        raise ValueError("Query contains a disallowed keyword.")

    conn = _conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(stripped)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    mcp.run(transport="stdio")
