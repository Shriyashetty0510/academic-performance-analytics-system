import re
from datetime import datetime
from config.database import execute_query


# =====================================================
# EMAIL VALIDATION
# =====================================================

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# =====================================================
# UID GENERATOR (A001, S001, T001, P001)
# =====================================================

def generate_user_uid(role: str) -> str:
    prefixes = {
        "admin": "A",
        "teacher": "T",
        "student": "S",
        "parent": "P"
    }

    prefix = prefixes.get(role, "U")

    # Find last UID for this role
    res = execute_query(
        f"SELECT user_uid FROM users WHERE user_uid LIKE '{prefix}%' ORDER BY id DESC LIMIT 1"
    )

    if res:
        try:
            last_number = int(res[0]["user_uid"][1:])
            new_number = last_number + 1
        except:
            new_number = 1
    else:
        new_number = 1

    return f"{prefix}{new_number:03d}"


# =====================================================
# AUDIT LOGGING
# =====================================================

def log_activity(user_id: int, action: str, details: str = ""):
    try:
        execute_query("""
            INSERT INTO audit_logs (user_id, action, details, created_at)
            VALUES (%s, %s, %s, %s)
        """, (user_id, action, details, datetime.now()), fetch=False)
    except:
        pass
