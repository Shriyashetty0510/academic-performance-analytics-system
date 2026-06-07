import bcrypt
from datetime import datetime
from config.database import execute_query
from utils.helpers import generate_user_uid, log_activity


# =====================================================
# REGISTER USER  (Uses bcrypt hashing)
# =====================================================

def register_user(name, email, password, role, phone=None, department=None, year=None):
    """
    Register new user securely with bcrypt password hashing.
    """

    try:
        # Generate unique user UID
        user_uid = generate_user_uid(role)

        # Hash password with bcrypt
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insert into users table
        user_id = execute_query(
            """
            INSERT INTO users (user_uid, name, email, password_hash, role, is_approved)
            VALUES (%s, %s, %s, %s, %s, FALSE)
            """,
            (user_uid, name, email, hashed_pw, role),
            fetch=False
        )

        # Insert into student profile table (if student)
        if role == "student" and user_id:
            execute_query(
                """
                INSERT INTO student_profiles (user_id, department, year, phone)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, department, year, phone),
                fetch=False
            )

        # Log registration
        log_activity(user_id, "user_registered", f"Role={role}")

        return True, user_uid

    except Exception as e:
        return False, str(e)


# =====================================================
# LOGIN USER (bcrypt verification)
# =====================================================

def authenticate_user(email, password):
    """
    Authenticate user by verifying bcrypt password hashes.
    """

    # Fetch user by email
    result = execute_query(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )

    if not result:
        return None

    user = result[0]

    # Compare bcrypt hashed password
    try:
        print("INPUT PASSWORD:", password)
        print("HASH FROM DB:", user['password_hash'])
        print("CHECK RESULT:", bcrypt.checkpw(
        password.encode(),
        user['password_hash'].encode()
        ))

        if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        #if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            if user['is_approved']:

                log_activity(user['id'], "user_login")

                return {
                    "id": user["id"],
                    "user_uid": user["user_uid"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"]
                }

    except Exception:
        return None

    return None
