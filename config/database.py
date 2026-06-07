import mysql.connector
import streamlit as st

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aazz123@@',
    'database': 'epic1',
    'charset': 'utf8mb4'
}

def get_connection():
    """Create and return a DB connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return None


def execute_query(query, params=None, fetch=True):
    """Run SQL query safely"""
    conn = get_connection()
    if not conn:
        return [] if fetch else None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            return cursor.lastrowid

    except mysql.connector.Error as err:
        st.error(f"Query failed: {err}")
        if conn:
            conn.rollback()
        return [] if fetch else None

    finally:
        if conn:
            cursor.close()
            conn.close()
