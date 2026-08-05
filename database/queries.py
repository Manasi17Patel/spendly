"""Pure query helpers for the Spendly profile page.

Functions in this module call get_db() internally and close the connection
before returning. All SQL is parameterised; all amounts are returned as raw
floats and formatted by the route.
"""

from database.db import get_db


_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def get_user_by_id(user_id):
    """Return {name, email, member_since} for the user, or None.
    member_since is formatted as 'Month YYYY' (e.g. 'July 2026').
    """
    from database.db import get_user_by_id as _db_get_user_by_id
    row = _db_get_user_by_id(user_id)
    if row is None:
        return None
    created_at = row.get("created_at") or ""
    member_since = ""
    if len(created_at) >= 7 and created_at[4] == "-" and created_at[:4].isdigit():
        try:
            year = int(created_at[:4])
            month = int(created_at[5:7])
            if 1 <= month <= 12:
                member_since = f"{_MONTH_NAMES[month - 1]} {year}"
        except ValueError:
            member_since = ""
    return {
        "name": row.get("name", ""),
        "email": row.get("email", ""),
        "member_since": member_since,
    }


def get_summary_stats(user_id):
    """Return {total_spent: float, transaction_count: int, top_category: str}.
    When the user has no expenses, returns {total_spent: 0, transaction_count: 0, top_category: '—'}.
    """
    conn = get_db()
    try:
        total_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        total_spent = float(total_row[0] or 0)

        count_row = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        transaction_count = int(count_row[0] or 0)

        top_category = "—"
        if transaction_count > 0:
            top_row = conn.execute(
                "SELECT category FROM expenses WHERE user_id = ? "
                "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if top_row is not None:
                top_category = top_row[0]

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category,
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    """Return up to `limit` most-recent expenses for `user_id`, newest date first.
    Each dict: {date, description, category, amount} (amount is raw float; formatting is the route's job).
    Returns [] when the user has no expenses.
    """
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT date, description, category, amount FROM expenses "
            "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_category_breakdown(user_id):
    """Return per-category spending for the user, ordered by amount desc.
    Each dict: {name, amount, pct}. pct is an int 0–100; the rows together sum to exactly 100.
    Returns [] when the user has no expenses.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,),
        ).fetchall()
        if not rows:
            return []
        grand_total = sum(float(r["total"]) for r in rows)
        if grand_total <= 0:
            return []
        # Compute raw percentages, round to int
        result = []
        running_sum = 0
        for r in rows:
            amt = float(r["total"])
            raw_pct = (amt / grand_total) * 100
            result.append({"name": r["category"], "amount": amt, "pct": int(round(raw_pct))})
            running_sum += result[-1]["pct"]
        # Adjust the largest category to absorb any rounding remainder so percentages sum to 100
        remainder = 100 - running_sum
        if remainder != 0 and result:
            result[0]["pct"] += remainder
        return result
    finally:
        conn.close()
