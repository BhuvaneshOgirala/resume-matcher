from hashlib import sha256
from typing import TypedDict

from supabase import create_client

DAILY_USER_LIMIT = 20
DAILY_GLOBAL_LIMIT = 100


class UsageReservation(TypedDict):
    allowed: bool
    user_comparisons: int
    user_remaining: int
    global_comparisons: int
    global_remaining: int
    limit_reason: str | None


def reserve_daily_comparison(
    user_subject: str,
    supabase_url: str,
    service_role_key: str,
) -> UsageReservation:
    """Atomically reserve one daily user and app-wide comparison."""
    subject = user_subject.strip()
    if not subject:
        raise ValueError("A signed-in account identifier is required.")
    if not supabase_url.strip() or not service_role_key.strip():
        raise ValueError("Usage storage is not configured.")

    user_hash = sha256(subject.encode("utf-8")).hexdigest()
    client = create_client(supabase_url.strip(), service_role_key.strip())
    response = client.rpc(
        "reserve_daily_comparison",
        {"p_user_hash": user_hash},
    ).execute()
    if not isinstance(response.data, list) or not response.data:
        raise RuntimeError("The usage service returned an invalid response.")

    row = response.data[0]
    if not isinstance(row, dict):
        raise RuntimeError("The usage service returned an invalid response.")
    if not isinstance(row.get("allowed"), bool):
        raise RuntimeError("The usage service returned an invalid response.")
    int_fields = (
        "user_comparisons",
        "user_remaining",
        "global_comparisons",
        "global_remaining",
    )
    if any(
        isinstance(row.get(field), bool) or not isinstance(row.get(field), int)
        for field in int_fields
    ):
        raise RuntimeError("The usage service returned an invalid response.")
    reason = row.get("limit_reason")
    if reason is not None and (
        not isinstance(reason, str) or reason not in {"user", "global"}
    ):
        raise RuntimeError("The usage service returned an invalid response.")

    return {
        "allowed": row["allowed"],
        "user_comparisons": row["user_comparisons"],
        "user_remaining": row["user_remaining"],
        "global_comparisons": row["global_comparisons"],
        "global_remaining": row["global_remaining"],
        "limit_reason": reason,
    }
