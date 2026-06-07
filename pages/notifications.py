import streamlit as st
from config.database import execute_query


# =====================================================
# NOTIFICATIONS CENTER
# =====================================================

def notifications_center(user_id):
    st.title("🔔 Notifications")

    # Fetch latest notifications
    notifications = execute_query("""
        SELECT id, message, type, created_at, is_read
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 30
    """, (user_id,))

    if not notifications:
        st.info("📭 No notifications available.")
        return

    # Display unread count
    unread_count = sum(1 for n in notifications if not n["is_read"])
    if unread_count > 0:
        st.warning(f"📬 You have **{unread_count} unread** notification(s).")

    # Render notifications
    for notif in notifications:
        icon = "🔔" if not notif["is_read"] else "📌"
        read_status = "**NEW**" if not notif["is_read"] else "Read"

        with st.expander(f"{icon} {notif['message'][:40]}...  —  {read_status}"):
            st.write(f"**Message:** {notif['message']}")
            st.write(f"**Type:** {notif['type']}")
            st.write(f"**Time:** {notif['created_at']}")

            # Mark as read
            if not notif["is_read"]:
                if st.button("Mark as Read", key=f"mark_{notif['id']}"):
                    execute_query("""
                        UPDATE notifications
                        SET is_read = TRUE
                        WHERE id = %s
                    """, (notif["id"],), fetch=False)
                    st.rerun()
