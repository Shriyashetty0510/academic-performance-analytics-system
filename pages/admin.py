import pandas as pd
import streamlit as st
from config.database import execute_query
from utils.helpers import log_activity, generate_user_uid


# =====================================================
# ADMIN DASHBOARD
# =====================================================

def admin_dashboard():
    st.title("🏠 Admin Dashboard")

    try:
        col1, col2, col3, col4 = st.columns(4)

        users_result = execute_query(
            "SELECT COUNT(*) AS count FROM users"
        )

        pending_result = execute_query(
            "SELECT COUNT(*) AS count FROM users WHERE is_approved = FALSE"
        )

        students_result = execute_query(
            "SELECT COUNT(*) AS count FROM users WHERE role = 'student'"
        )

        teachers_result = execute_query(
            "SELECT COUNT(*) AS count FROM users WHERE role = 'teacher'"
        )

        total = users_result[0]["count"] if users_result else 0
        pending = pending_result[0]["count"] if pending_result else 0
        students = students_result[0]["count"] if students_result else 0
        teachers = teachers_result[0]["count"] if teachers_result else 0

        with col1:
            st.metric("👥 Total Users", total)

        with col2:
            st.metric("⏳ Pending Approvals", pending)

        with col3:
            st.metric("🎓 Students", students)

        with col4:
            st.metric("👨‍🏫 Teachers", teachers)

        st.markdown("---")

        st.subheader("Recent Users")

        recent_users = execute_query("""
            SELECT user_uid, name, email, role, is_approved
            FROM users
            ORDER BY id DESC
            LIMIT 10
        """)

        if recent_users:
            df = pd.DataFrame(recent_users)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No users found.")

    except Exception as e:
        st.error(f"Admin Dashboard Error: {e}")


# =====================================================
# APPROVE USERS
# =====================================================

def approve_users():
    st.title("📋 User Approvals")

    pending = execute_query("""
        SELECT u.id, u.user_uid, u.name, u.email, u.role, u.created_at,
               sp.department, sp.year, sp.phone
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id = u.id
        WHERE u.is_approved = FALSE
        ORDER BY u.created_at DESC
    """)

    if not pending:
        st.success("🎉 No pending approvals!")
        return

    st.info(f"📌 {len(pending)} user(s) waiting for approval.")

    for user in pending:
        with st.expander(f"👤 {user['name']} - {user['role'].title()} (ID: {user['user_uid']})"):

            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**Email:** {user['email']}")
                st.write(f"**Role:** {user['role']}")
                st.write(f"**Registered:** {user['created_at']}")

                if user["role"] == "student":
                    st.write(f"**Department:** {user['department']}")
                    st.write(f"**Year:** {user['year']}")

            with col2:
                if st.button("✅ Approve", key=f"approve_{user['id']}"):

                    execute_query(
                         "UPDATE users SET is_approved = TRUE WHERE id = %s",
                         (user["id"],),
                         fetch=False
                        )

                    execute_query("""
                        INSERT INTO notifications
                        (user_id, message, type, is_read)
                        VALUES (%s, %s, %s, FALSE)
                    """, (
                              user["id"],
                              "Your account has been approved by the administrator.",
                              "success"
                        ), fetch=False)

                    log_activity(
                        st.session_state.user["id"],
                        "approve_user",
                        f"Approved {user['email']}"
                    )

                    st.success("Approved successfully!")
                    st.rerun()

                if st.button("❌ Reject", key=f"reject_{user['id']}"):
                    execute_query("DELETE FROM users WHERE id = %s", (user["id"],), fetch=False)
                    log_activity(st.session_state.user["id"], "reject_user", f"Rejected {user['email']}")
                    st.warning("User rejected!")
                    st.rerun()


# =====================================================
# MANAGE COURSES
# =====================================================

def manage_courses():
    st.title("📚 Course Management")

    tab1, tab2, tab3 = st.tabs([
        "📖 View Courses",
        "➕ Add New Course",
        "🎓 Enroll Students"
    ])

    # =====================================================
    # VIEW COURSES
    # =====================================================
    with tab1:

        courses = execute_query("""
            SELECT c.id,
                   c.course_code,
                   c.course_name,
                   u.name AS teacher
            FROM courses c
            LEFT JOIN users u
            ON c.teacher_id = u.id
        """)

        if courses:
            df = pd.DataFrame(courses)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No courses found.")

    # =====================================================
    # ADD COURSE
    # =====================================================
    with tab2:

        course_code = st.text_input("Course Code")
        course_name = st.text_input("Course Name")

        teachers = execute_query("""
            SELECT id, name
            FROM users
            WHERE role='teacher'
            AND is_approved=TRUE
        """)

        if teachers:

            teacher_map = {
                t["name"]: t["id"]
                for t in teachers
            }

            selected_teacher = st.selectbox(
                "Assign Teacher",
                list(teacher_map.keys())
            )

            if st.button("Add Course"):

                execute_query("""
                    INSERT INTO courses
                    (course_code, course_name, teacher_id)
                    VALUES (%s, %s, %s)
                """, (
                    course_code,
                    course_name,
                    teacher_map[selected_teacher]
                ), fetch=False)

                st.success("🎉 Course added successfully!")
                st.rerun()

        else:
            st.warning("No approved teachers available.")

    # =====================================================
    # ENROLL STUDENTS
    # =====================================================
    with tab3:

        st.subheader("🎓 Enroll Student To Course")

        students = execute_query("""
            SELECT id, user_uid, name
            FROM users
            WHERE role='student'
            AND is_approved=TRUE
            ORDER BY name
        """)

        courses = execute_query("""
            SELECT id, course_code, course_name
            FROM courses
            ORDER BY course_code
        """)

        if not students:
            st.warning("No approved students found.")
            return

        if not courses:
            st.warning("No courses available.")
            return

        student_map = {
            f"{s['user_uid']} - {s['name']}": s["id"]
            for s in students
        }

        course_map = {
            f"{c['course_code']} - {c['course_name']}": c["id"]
            for c in courses
        }

        selected_student = st.selectbox(
            "Select Student",
            list(student_map.keys())
        )

        selected_course = st.selectbox(
            "Select Course",
            list(course_map.keys())
        )

        if st.button("Enroll Student"):

            existing = execute_query("""
                SELECT *
                FROM student_courses
                WHERE student_id=%s
                AND course_id=%s
            """, (
                student_map[selected_student],
                course_map[selected_course]
            ))

            if existing:
                st.warning("⚠️ Student already enrolled in this course.")
            else:

                execute_query("""
                    INSERT INTO student_courses
                    (student_id, course_id)
                    VALUES (%s, %s)
                """, (
                    student_map[selected_student],
                    course_map[selected_course]
                ), fetch=False)

                st.success("🎉 Student enrolled successfully!")
                st.rerun()

        st.markdown("---")
        st.subheader("📋 Current Enrollments")

        enrollments = execute_query("""
            SELECT u.user_uid,
                   u.name AS student_name,
                   c.course_code,
                   c.course_name
            FROM student_courses sc
            JOIN users u
                ON sc.student_id = u.id
            JOIN courses c
                ON sc.course_id = c.id
            ORDER BY u.name
        """)

        if enrollments:
            st.dataframe(
                pd.DataFrame(enrollments),
                use_container_width=True
            )
        else:
            st.info("No enrollments found.")


#PARENT MANAGEMENT
def parent_management():
    st.title("👨‍👩‍👧 Parent Management")

    parents = execute_query("""
        SELECT id, name, user_uid
        FROM users
        WHERE role='parent'
        AND is_approved=TRUE
        ORDER BY name
    """)

    students = execute_query("""
        SELECT id, name, user_uid
        FROM users
        WHERE role='student'
        AND is_approved=TRUE
        ORDER BY name
    """)

    if not parents:
        st.warning("No approved parents found.")
        return

    if not students:
        st.warning("No approved students found.")
        return

    parent_map = {
        f"{p['user_uid']} - {p['name']}": p["id"]
        for p in parents
    }

    student_map = {
        f"{s['user_uid']} - {s['name']}": s["id"]
        for s in students
    }

    selected_parent = st.selectbox(
        "Select Parent",
        list(parent_map.keys())
    )

    selected_student = st.selectbox(
        "Select Student",
        list(student_map.keys())
    )

    if st.button("Link Parent & Student"):

        existing = execute_query("""
            SELECT *
            FROM parent_child_links
            WHERE parent_id=%s
            AND child_id=%s
        """, (
            parent_map[selected_parent],
            student_map[selected_student]
        ))

        if existing:
            st.warning("Parent already linked to this student.")
        else:
            execute_query("""
                INSERT INTO parent_child_links
                (parent_id, child_id)
                VALUES (%s, %s)
            """, (
                parent_map[selected_parent],
                student_map[selected_student]
            ), fetch=False)

            st.success("🎉 Parent linked successfully!")
            st.rerun()

    st.markdown("---")
    st.subheader("Current Parent-Student Links")

    links = execute_query("""
        SELECT
            p.user_uid AS parent_uid,
            p.name AS parent_name,
            s.user_uid AS student_uid,
            s.name AS student_name
        FROM parent_child_links pcl
        JOIN users p ON pcl.parent_id = p.id
        JOIN users s ON pcl.child_id = s.id
        ORDER BY parent_name
    """)

    if links:
        st.dataframe(pd.DataFrame(links), use_container_width=True)
    else:
        st.info("No parent-child links found.")


# =====================================================
# BULK IMPORT / EXPORT
# =====================================================

def bulk_import_export():
    st.title("📦 Bulk Operations")

    tab1, tab2 = st.tabs(["📥 Import Students", "📤 Export Students"])

    # ---------------------------- IMPORT -------------------------------
    with tab1:
        st.write("Upload CSV file containing students.")

        file = st.file_uploader("Choose CSV", type=["csv"])

        if file:
            df = pd.read_csv(file)
            st.dataframe(df.head())

            if st.button("Import"):
                count = 0

                for _, row in df.iterrows():
                    try:
                        user_uid = generate_user_uid("student")

                        user_id = execute_query("""
                            INSERT INTO users (user_uid, name, email, password_hash, role, is_approved)
                            VALUES (%s, %s, %s, %s, 'student', TRUE)
                        """, (
                            user_uid,
                            row["name"],
                            row["email"],
                            str(row.get("password", "default123"))
                        ), fetch=False)

                        execute_query("""
                            INSERT INTO student_profiles (user_id, department, year, phone)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            user_id,
                            row.get("department"),
                            row.get("year", 1),
                            row.get("phone")
                        ), fetch=False)

                        count += 1

                    except:
                        continue

                log_activity(st.session_state.user["id"], "bulk_import", f"Imported {count} students")

                st.success(f"🎉 Successfully imported {count} students!")

    # ---------------------------- EXPORT -------------------------------
    with tab2:
        if st.button("Export All Students"):
            rows = execute_query("""
                SELECT u.user_uid, u.name, u.email, sp.department, sp.year, sp.phone
                FROM users u
                LEFT JOIN student_profiles sp ON sp.user_id = u.id
                WHERE u.role = 'student'
            """)

            if rows:
                df = pd.DataFrame(rows)
                st.download_button(
                    "Download CSV",
                    df.to_csv(index=False),
                    "students_export.csv",
                    "text/csv"
                )
                st.success("Export completed.")
            else:
                st.info("No students found.")
