# ============================================
# COMPLETE APAS APPLICATION - FIXED VERSION
# Academic Performance Analytics System
# ============================================

import streamlit as st
import mysql.connector
import pandas as pd
import re
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ============================================
# DATABASE CONFIGURATION
# ============================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Aazz123@@',  # Change this to your password
    'database': 'epic11',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

def execute_query(query, params=None, fetch=True):
    """Execute SQL query with error handling"""
    conn = get_db_connection()
    if not conn:
        return [] if fetch else None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid
    except mysql.connector.Error as err:
        st.error(f"Query error: {err}")
        if conn:
            conn.rollback()
        return [] if fetch else None
    finally:
        if conn:
            cursor.close()
            conn.close()# ============================================
# AUTHENTICATION (FIXED ORDER)
# ============================================

import hashlib

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def hash_password(password):
    """Simple hash function for passwords"""
    return hashlib.sha256(password.encode()).hexdigest()

def log_activity(user_id, action, details=""):
    """Log user activity for audit"""
    try:
        if user_id > 0:
            execute_query("""
                INSERT INTO audit_logs (user_id, action, details, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, action, details, datetime.now()), fetch=False)
    except:
        pass

def check_session_timeout():
    """Check session timeout - 10 minutes"""
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
        return True

    time_elapsed = (datetime.now() - st.session_state.last_activity).seconds

    if time_elapsed > 600:
        st.warning("⚠️ Session expired. Please login again.")
        logout()
        st.rerun()
        return False

    st.session_state.last_activity = datetime.now()
    return True

def generate_user_uid(role):
    """Generate unique user ID"""
    prefix = {'student': 'S', 'teacher': 'T', 'parent': 'P', 'admin': 'A'}.get(role, 'U')

    result = execute_query(
        f"SELECT user_uid FROM users WHERE user_uid LIKE '{prefix}%' ORDER BY id DESC LIMIT 1"
    )

    if result:
        try:
            last_num = int(result[0]['user_uid'][1:])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}{new_num:03d}"

def register_user(name, email, password, role, phone=None, department=None, year=None):
    """Register new user"""
    try:
        user_uid = generate_user_uid(role)

        # Hash the password
        password_hash = hash_password(password)

        user_id = execute_query("""
            INSERT INTO users (user_uid, name, email, password_hash, role, is_approved)
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """, (user_uid, name, email, password_hash, role), fetch=False)

        if role == 'student' and user_id:
            execute_query("""
                INSERT INTO student_profiles (user_id, department, year, phone)
                VALUES (%s, %s, %s, %s)
            """, (user_id, department, year, phone), fetch=False)

        log_activity(user_id, 'user_registered', f"Role: {role}")
        return True, user_uid
    except Exception as e:
        return False, str(e)

def authenticate_user(email, password):
    """Authenticate user"""
    users = execute_query("SELECT * FROM users WHERE email = %s", (email,))

    if not users:
        return None

    user = users[0]

    # Hash the input password and compare
    password_hash = hash_password(password)

    if user['password_hash'] == password_hash:
        if user['is_approved']:
            log_activity(user['id'], 'user_login')
            return {
                'id': user['id'],
                'user_uid': user['user_uid'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }

    return None

def logout():
    """Logout user"""
    if st.session_state.get('user'):
        log_activity(st.session_state.user['id'], 'user_logout')

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.last_activity = None

# ============================================
# LOGIN PAGE
# ============================================

def login_page():
    """Display login and registration page"""
    st.title("🎓 APAS - Academic Performance Analytics System")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Welcome Back!")

            email = st.text_input("📧 Email", key="login_email")
            password = st.text_input("🔒 Password", type="password", key="login_pw")

            if st.button("🚀 Login", use_container_width=True, type="primary"):
                if email and password:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.session_state.last_activity = datetime.now()
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials or account not approved")
                else:
                    st.warning("⚠️ Enter email and password")

    with tab2:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Create New Account")

            name = st.text_input("👤 Full Name", key="reg_name")
            email = st.text_input("📧 Email", key="reg_email")
            password = st.text_input("🔒 Password (min 6 chars)", type="password", key="reg_pw")
            confirm_pw = st.text_input("🔒 Confirm Password", type="password", key="reg_confirm")
            role = st.selectbox("👥 Register as", ["student", "teacher", "parent"], key="reg_role")

            if role == "student":
                st.markdown("#### Student Information")
                department = st.selectbox("🏫 Department",
                    ["Computer Science", "Electronics", "Mechanical", "Civil", "Other"])
                year = st.selectbox("📅 Year", [1, 2, 3, 4])
                phone = st.text_input("📱 Phone", key="reg_phone")
            else:
                department = year = phone = None

            if st.button("📝 Register", use_container_width=True, type="primary"):
                errors = []

                if not name or len(name) < 3:
                    errors.append("Name must be at least 3 characters")
                if not validate_email(email):
                    errors.append("Invalid email format")
                if execute_query("SELECT id FROM users WHERE email = %s", (email,)):
                    errors.append("Email already registered")
                if len(password) < 6:
                    errors.append("Password must be at least 6 characters")
                if password != confirm_pw:
                    errors.append("Passwords do not match")

                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    success, message = register_user(name, email, password, role,
                                                    phone, department, year)
                    if success:
                        st.success(f"✅ Registration successful! Your ID: **{message}**")
                        st.warning("⏳ Awaiting admin approval")
                        st.balloons()
                    else:
                        st.error(f"❌ Registration failed: {message}")

# ============================================
# ADMIN FUNCTIONS
# ============================================

def admin_dashboard():
    """Admin dashboard"""
    st.title("🏠 Admin Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total = execute_query("SELECT COUNT(*) as count FROM users")[0]['count']
        st.metric("👥 Total Users", total)

    with col2:
        pending = execute_query("SELECT COUNT(*) as count FROM users WHERE is_approved = FALSE")[0]['count']
        st.metric("⏳ Pending Approvals", pending)

    with col3:
        students = execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'student'")[0]['count']
        st.metric("🎓 Students", students)

    with col4:
        teachers = execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'teacher'")[0]['count']
        st.metric("👨‍🏫 Teachers", teachers)

def approve_users():
    """Approve pending registrations"""
    st.title("📋 User Approvals")

    pending = execute_query("""
        SELECT u.id, u.user_uid, u.name, u.email, u.role, u.created_at,
               sp.department, sp.year, sp.phone
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id = u.id
        WHERE u.is_approved = FALSE
        ORDER BY u.created_at DESC
    """)

    if pending:
        st.info(f"📊 {len(pending)} pending registration(s)")

        for user in pending:
            with st.expander(f"👤 {user['name']} - {user['role'].title()} (ID: {user['user_uid']})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Role:** {user['role'].title()}")
                    st.write(f"**Registered:** {user['created_at']}")
                    if user['role'] == 'student':
                        st.write(f"**Department:** {user['department']}")
                        st.write(f"**Year:** {user['year']}")

                with col2:
                    if st.button("✅ Approve", key=f"app_{user['id']}"):
                        execute_query("UPDATE users SET is_approved = TRUE WHERE id = %s",
                                    (user['id'],), fetch=False)
                        log_activity(st.session_state.user['id'], 'user_approved',
                                   f"Approved: {user['email']}")
                        st.success(f"✅ Approved {user['name']}")
                        st.rerun()

                    if st.button("❌ Reject", key=f"rej_{user['id']}"):
                        execute_query("DELETE FROM users WHERE id = %s", (user['id'],), fetch=False)
                        log_activity(st.session_state.user['id'], 'user_rejected',
                                   f"Rejected: {user['email']}")
                        st.warning(f"❌ Rejected {user['name']}")
                        st.rerun()
    else:
        st.success("✅ No pending approvals")

def manage_courses():
    """Manage courses"""
    st.title("📚 Course Management")

    tab1, tab2 = st.tabs(["View Courses", "Add Course"])

    with tab1:
        courses = execute_query("""
            SELECT c.id, c.course_code, c.course_name, u.name as teacher_name
            FROM courses c
            LEFT JOIN users u ON c.teacher_id = u.id
        """)

        if courses:
            df = pd.DataFrame(courses)
            st.dataframe(df, use_container_width=True)

    with tab2:
        course_code = st.text_input("Course Code", "CS101")
        course_name = st.text_input("Course Name", "Introduction to Programming")

        teachers = execute_query("SELECT id, name FROM users WHERE role = 'teacher' AND is_approved = TRUE")
        if teachers:
            teacher_names = {t['name']: t['id'] for t in teachers}
            teacher = st.selectbox("Assign Teacher", list(teacher_names.keys()))

            if st.button("➕ Add Course"):
                execute_query("""
                    INSERT INTO courses (course_code, course_name, teacher_id)
                    VALUES (%s, %s, %s)
                """, (course_code, course_name, teacher_names[teacher]), fetch=False)
                st.success("✅ Course added!")
                st.rerun()
        else:
            st.warning("No approved teachers available")

def bulk_import_export():
    """Bulk data operations"""
    st.title("📦 Bulk Operations")

    tab1, tab2 = st.tabs(["Import Data", "Export Data"])

    with tab1:
        st.subheader("Import Students from CSV")
        uploaded = st.file_uploader("Upload CSV file", type=['csv'])

        if uploaded:
            df = pd.read_csv(uploaded)
            st.dataframe(df.head())

            if st.button("Import"):
                count = 0
                for _, row in df.iterrows():
                    try:
                        user_uid = generate_user_uid('student')

                        user_id = execute_query("""
                            INSERT INTO users (user_uid, name, email, password_hash, role, is_approved)
                            VALUES (%s, %s, %s, %s, 'student', TRUE)
                        """, (user_uid, row['name'], row['email'], str(row.get('password', 'default123'))), fetch=False)

                        if user_id:
                            execute_query("""
                                INSERT INTO student_profiles (user_id, department, year, phone)
                                VALUES (%s, %s, %s, %s)
                            """, (user_id, row.get('department'), row.get('year', 1),
                                 row.get('phone')), fetch=False)
                            count += 1
                    except:
                        continue

                log_activity(st.session_state.user['id'], 'bulk_import', f"Imported {count} students")
                st.success(f"✅ Imported {count} students")

    with tab2:
        st.subheader("Export Data")

        if st.button("📥 Export All Students"):
            students = execute_query("""
                SELECT u.user_uid, u.name, u.email, sp.department, sp.year, sp.phone
                FROM users u
                LEFT JOIN student_profiles sp ON sp.user_id = u.id
                WHERE u.role = 'student'
            """)

            if students:
                df = pd.DataFrame(students)
                csv_data = df.to_csv(index=False)
                st.download_button("Download CSV", csv_data, "students.csv", "text/csv")
                log_activity(st.session_state.user['id'], 'data_export', "Exported students")

# ============================================
# TEACHER FUNCTIONS
# ============================================

def teacher_dashboard(teacher_id):
    """Teacher dashboard"""
    st.title("🏠 Teacher Dashboard")

    courses = execute_query("""
        SELECT course_code, course_name FROM courses WHERE teacher_id = %s
    """, (teacher_id,))

    st.subheader("📚 My Courses")
    if courses:
        for course in courses:
            st.info(f"**{course['course_code']}** - {course['course_name']}")
    else:
        st.warning("No courses assigned")

def mark_attendance(teacher_id):
    """Mark attendance"""
    st.title("📝 Mark Attendance")

    courses = execute_query("""
        SELECT id, course_code, course_name FROM courses WHERE teacher_id = %s
    """, (teacher_id,))

    if not courses:
        st.warning("No courses assigned")
        return

    course_names = {f"{c['course_code']} - {c['course_name']}": c['id'] for c in courses}
    selected = st.selectbox("Select Course", list(course_names.keys()))
    course_id = course_names[selected]

    students = execute_query("""
        SELECT u.id, u.name, u.user_uid
        FROM users u
        JOIN student_courses sc ON sc.student_id = u.id
        WHERE sc.course_id = %s
    """, (course_id,))

    if students:
        attendance_date = st.date_input("Date", date.today())

        attendance = {}
        for student in students:
            status = st.radio(
                f"{student['user_uid']} - {student['name']}",
                ["Present", "Absent", "Late"],
                horizontal=True,
                key=f"att_{student['id']}"
            )
            attendance[student['id']] = status

        if st.button("💾 Save Attendance"):
            for student_id, status in attendance.items():
                execute_query("""
                    INSERT INTO attendance_records
                    (student_id, course_id, teacher_id, attendance_date, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (student_id, course_id, teacher_id, attendance_date, status), fetch=False)

            log_activity(teacher_id, 'attendance_marked', f"Course: {selected}")
            st.success("✅ Attendance saved!")
    else:
        st.info("No students enrolled")

def enter_grades(teacher_id):
    """Enter grades"""
    st.title("📊 Enter Grades")

    courses = execute_query("""
        SELECT id, course_code, course_name FROM courses WHERE teacher_id = %s
    """, (teacher_id,))

    if not courses:
        st.warning("No courses assigned")
        return

    course_names = {f"{c['course_code']} - {c['course_name']}": c['id'] for c in courses}
    selected = st.selectbox("Select Course", list(course_names.keys()))
    course_id = course_names[selected]

    students = execute_query("""
        SELECT u.id, u.name, u.user_uid
        FROM users u
        JOIN student_courses sc ON sc.student_id = u.id
        WHERE sc.course_id = %s
    """, (course_id,))

    if students:
        for student in students:
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"{student['user_uid']} - {student['name']}")

            with col2:
                percent = st.number_input("Percentage", 0, 100,
                                        key=f"pct_{student['id']}",
                                        label_visibility="collapsed")

            with col3:
                if percent >= 90:
                    grade, gpa = 'A+', 4.0
                elif percent >= 80:
                    grade, gpa = 'A', 4.0
                elif percent >= 70:
                    grade, gpa = 'B+', 3.5
                elif percent >= 60:
                    grade, gpa = 'B', 3.0
                elif percent >= 50:
                    grade, gpa = 'C', 2.0
                else:
                    grade, gpa = 'F', 0.0

                if st.button("Save", key=f"save_{student['id']}"):
                    execute_query("""
                        INSERT INTO grades (student_id, course_id, grade, percent, gpa_value)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE grade=%s, percent=%s, gpa_value=%s
                    """, (student['id'], course_id, grade, percent, gpa,
                         grade, percent, gpa), fetch=False)

                    log_activity(teacher_id, 'grade_entered',
                               f"Student: {student['user_uid']}, Grade: {grade}")
                    st.success("✅")

# ============================================
# STUDENT FUNCTIONS
# ============================================

def student_dashboard(student_id):
    """Student dashboard"""
    st.title("🏠 Student Dashboard")

    info = execute_query("""
        SELECT u.name, u.user_uid, sp.department, sp.year
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id = u.id
        WHERE u.id = %s
    """, (student_id,))

    if info:
        st.info(f"**{info[0]['department']}** - Year {info[0]['year']}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📚 My Courses")
        courses = execute_query("""
            SELECT c.course_code, c.course_name
            FROM courses c
            JOIN student_courses sc ON sc.course_id = c.id
            WHERE sc.student_id = %s
        """, (student_id,))

        if courses:
            for course in courses:
                st.success(f"{course['course_code']} - {course['course_name']}")

    with col2:
        st.subheader("📊 Performance")

        gpa_result = execute_query(
            "SELECT AVG(gpa_value) as gpa FROM grades WHERE student_id = %s",
            (student_id,)
        )

        if gpa_result and gpa_result[0]['gpa']:
            gpa = float(gpa_result[0]['gpa'])
            st.metric("🎯 GPA", f"{gpa:.2f}")

        att = execute_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
            FROM attendance_records WHERE student_id = %s
        """, (student_id,))

        if att and att[0]['total'] > 0:
            pct = (att[0]['present'] / att[0]['total']) * 100
            st.metric("📅 Attendance", f"{pct:.1f}%")

def view_attendance(student_id):
    """View attendance details"""
    st.title("👁️ My Attendance")

    courses = execute_query("""
        SELECT c.id, c.course_code, c.course_name
        FROM courses c
        JOIN student_courses sc ON sc.course_id = c.id
        WHERE sc.student_id = %s
    """, (student_id,))

    if not courses:
        st.warning("No courses enrolled")
        return

    course_names = {f"{c['course_code']} - {c['course_name']}": c['id'] for c in courses}
    selected = st.selectbox("Select Course", list(course_names.keys()))
    course_id = course_names[selected]

    records = execute_query("""
        SELECT attendance_date, status
        FROM attendance_records
        WHERE student_id = %s AND course_id = %s
        ORDER BY attendance_date DESC
    """, (student_id, course_id))

    if records:
        df = pd.DataFrame(records)
        st.dataframe(df, use_container_width=True)

        present = len(df[df['status'] == 'Present'])
        total = len(df)
        percentage = (present / total * 100) if total > 0 else 0
        st.metric("Attendance Percentage", f"{percentage:.1f}%")
    else:
        st.info("No attendance records yet")

def view_grades(student_id):
    """View grades and GPA"""
    st.title("📊 My Grades & GPA")

    grades = execute_query("""
        SELECT c.course_code, c.course_name, g.grade, g.percent, g.gpa_value
        FROM grades g
        JOIN courses c ON g.course_id = c.id
        WHERE g.student_id = %s
    """, (student_id,))

    if grades:
        df = pd.DataFrame(grades)

        gpa = df['gpa_value'].mean()
        avg_percent = df['percent'].mean()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("🎯 Overall GPA", f"{gpa:.2f} / 4.0")
        with col2:
            st.metric("📊 Average %", f"{avg_percent:.1f}%")

        st.markdown("---")
        st.dataframe(df, use_container_width=True)

        fig = px.bar(df, x='course_code', y='gpa_value',
                    title='Course-wise GPA',
                    labels={'course_code': 'Course', 'gpa_value': 'GPA'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📝 No grades yet")

# ============================================
# PARENT FUNCTIONS
# ============================================

def parent_dashboard(parent_id):
    """Parent dashboard"""
    st.title("👨‍👩‍👧 Parent Dashboard")

    children = execute_query("""
        SELECT u.id, u.name, u.user_uid
        FROM users u
        JOIN parent_child_links pcl ON pcl.child_id = u.id
        WHERE pcl.parent_id = %s
    """, (parent_id,))

    if not children:
        st.warning("No children linked to your account")
        st.info("Contact admin to link student accounts")
        return

    child_names = {f"{c['user_uid']} - {c['name']}": c['id'] for c in children}
    selected = st.selectbox("Select Child", list(child_names.keys()))
    child_id = child_names[selected]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Academic Performance")

        gpa = execute_query(
            "SELECT AVG(gpa_value) as gpa FROM grades WHERE student_id = %s",
            (child_id,)
        )

        if gpa and gpa[0]['gpa']:
            st.metric("GPA", f"{float(gpa[0]['gpa']):.2f}")

    with col2:
        st.subheader("📅 Attendance")

        att = execute_query("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
            FROM attendance_records WHERE student_id = %s
        """, (child_id,))

        if att and att[0]['total'] > 0:
            pct = (att[0]['present'] / att[0]['total']) * 100
            st.metric("Attendance", f"{pct:.1f}%")

    st.subheader("📚 Recent Grades")
    grades = execute_query("""
        SELECT c.course_name, g.grade, g.percent
        FROM grades g
        JOIN courses c ON g.course_id = c.id
        WHERE g.student_id = %s
        LIMIT 5
    """, (child_id,))

    if grades:
        df = pd.DataFrame(grades)
        st.dataframe(df, use_container_width=True)

# ============================================
# REPORTS & ANALYTICS
# ============================================

def generate_reports():
    """Generate reports"""
    st.title("📊 Reports & Analytics")

    tab1, tab2 = st.tabs(["Attendance Report", "GPA Report"])

    with tab1:
        st.subheader("📅 Attendance Report")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=date.today())

        if st.button("📊 Generate Attendance Report"):
            data = execute_query("""
                SELECT u.user_uid, u.name,
                       COUNT(*) as total_classes,
                       SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present,
                       ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) as percentage
                FROM attendance_records a
                JOIN users u ON a.student_id = u.id
                WHERE a.attendance_date BETWEEN %s AND %s
                GROUP BY u.id
                ORDER BY u.name
            """, (start_date, end_date))

            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)

                csv_data = df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv_data,
                                 f"attendance_{start_date}_{end_date}.csv", "text/csv")

                log_activity(st.session_state.user['id'], 'report_generated',
                           f"Attendance report: {start_date} to {end_date}")
            else:
                st.warning("No data found for selected period")

    with tab2:
        st.subheader("🎯 GPA Report")

        if st.button("📊 Generate GPA Report"):
            data = execute_query("""
                SELECT u.user_uid, u.name,
                       sp.department, sp.year,
                       ROUND(AVG(g.gpa_value), 2) as gpa,
                       COUNT(DISTINCT g.course_id) as courses
                FROM users u
                LEFT JOIN student_profiles sp ON sp.user_id = u.id
                LEFT JOIN grades g ON g.student_id = u.id
                WHERE u.role = 'student' AND u.is_approved = TRUE
                GROUP BY u.id
                ORDER BY gpa DESC
            """)

            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)

                fig = px.histogram(df, x='gpa', nbins=20,
                                  title='GPA Distribution',
                                  labels={'gpa': 'GPA', 'count': 'Number of Students'})
                st.plotly_chart(fig, use_container_width=True)

                csv_data = df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv_data, "gpa_report.csv", "text/csv")

                log_activity(st.session_state.user['id'], 'report_generated', "GPA report")
            else:
                st.warning("No data available")

def predictive_analytics():
    """Predict at-risk students"""
    st.title("📈 Predictive Analytics - At-Risk Students")

    st.info("🔍 Identifying students who may need academic support")

    at_risk = execute_query("""
        SELECT u.user_uid, u.name,
               ROUND(AVG(g.gpa_value), 2) as gpa,
               ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) /
                      COUNT(a.id)) * 100, 2) as attendance_pct
        FROM users u
        LEFT JOIN grades g ON g.student_id = u.id
        LEFT JOIN attendance_records a ON a.student_id = u.id
        WHERE u.role = 'student' AND u.is_approved = TRUE
        GROUP BY u.id
        HAVING gpa < 2.5 OR attendance_pct < 75
        ORDER BY gpa ASC, attendance_pct ASC
    """)

    if at_risk:
        st.warning(f"⚠️ {len(at_risk)} student(s) identified as at-risk")

        df = pd.DataFrame(at_risk)

        def calculate_risk(row):
            if row['gpa'] < 2.0 or row['attendance_pct'] < 60:
                return '🔴 High Risk'
            elif row['gpa'] < 2.5 or row['attendance_pct'] < 75:
                return '🟡 Medium Risk'
            else:
                return '🟢 Low Risk'

        df['risk_level'] = df.apply(calculate_risk, axis=1)

        st.dataframe(df, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['attendance_pct'],
            y=df['gpa'],
            mode='markers+text',
            text=df['user_uid'],
            textposition="top center",
            marker=dict(size=12, color='red'),
            name='At-Risk Students'
        ))
        fig.update_layout(
            title='Student Risk Assessment',
            xaxis_title='Attendance %',
            yaxis_title='GPA',
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

        if st.button("📧 Notify Teachers & Advisors"):
            for student in at_risk:
                log_activity(st.session_state.user['id'], 'at_risk_alert_sent',
                           f"Student: {student['user_uid']}")
            st.success("✅ Notifications sent to relevant teachers and advisors")
    else:
        st.success("✅ No students currently identified as at-risk")

# ============================================
# NOTIFICATIONS
# ============================================

def notifications_center():
    """Notification center"""
    st.title("🔔 Notifications")

    user = st.session_state.user

    notifications = execute_query("""
        SELECT n.message, n.type, n.created_at, n.is_read
        FROM notifications n
        WHERE n.user_id = %s
        ORDER BY n.created_at DESC
        LIMIT 20
    """, (user['id'],))

    if notifications:
        unread = sum(1 for n in notifications if not n['is_read'])
        if unread > 0:
            st.info(f"📬 You have {unread} unread notification(s)")

        for notif in notifications:
            icon = "📌" if notif['is_read'] else "🔔"
            status = "Read" if notif['is_read'] else "**NEW**"

            with st.expander(f"{icon} {notif['message'][:50]}... - {status}"):
                st.write(f"**Message:** {notif['message']}")
                st.write(f"**Type:** {notif['type']}")
                st.write(f"**Time:** {notif['created_at']}")

                if not notif['is_read']:
                    if st.button("Mark as Read", key=f"read_{notif['created_at']}"):
                        execute_query("""
                            UPDATE notifications SET is_read = TRUE
                            WHERE user_id = %s AND created_at = %s
                        """, (user['id'], notif['created_at']), fetch=False)
                        st.rerun()
    else:
        st.info("📭 No notifications")

# ============================================
# ASSIGNMENT TRACKING
# ============================================

def assignment_tracking():
    """Track assignments"""
    st.title("📝 Assignment Tracking")

    user = st.session_state.user

    if user['role'] == 'teacher':
        st.subheader("Create Assignment")

        courses = execute_query("""
            SELECT id, course_code, course_name FROM courses WHERE teacher_id = %s
        """, (user['id'],))

        if courses:
            course_names = {f"{c['course_code']} - {c['course_name']}": c['id'] for c in courses}
            selected = st.selectbox("Select Course", list(course_names.keys()))
            course_id = course_names[selected]

            title = st.text_input("Assignment Title")
            description = st.text_area("Description")
            deadline = st.date_input("Deadline", min_value=date.today())

            if st.button("➕ Create Assignment"):
                execute_query("""
                    INSERT INTO assignments (course_id, title, description, deadline, created_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, (course_id, title, description, deadline, user['id']), fetch=False)
                st.success("✅ Assignment created!")
                st.rerun()

        st.markdown("---")
        st.subheader("Assignment Submissions")

        submissions = execute_query("""
            SELECT a.title, u.name as student_name,
                   asub.submitted_at, asub.status,
                   a.deadline
            FROM assignment_submissions asub
            JOIN assignments a ON a.id = asub.assignment_id
            JOIN users u ON u.id = asub.student_id
            JOIN courses c ON c.id = a.course_id
            WHERE c.teacher_id = %s
            ORDER BY asub.submitted_at DESC
        """, (user['id'],))

        if submissions:
            df = pd.DataFrame(submissions)
            st.dataframe(df, use_container_width=True)

    elif user['role'] == 'student':
        st.subheader("My Assignments")

        assignments = execute_query("""
            SELECT a.id, a.title, a.description, a.deadline,
                   c.course_name,
                   asub.submitted_at, asub.status
            FROM assignments a
            JOIN courses c ON c.id = a.course_id
            JOIN student_courses sc ON sc.course_id = c.id
            LEFT JOIN assignment_submissions asub ON asub.assignment_id = a.id
                AND asub.student_id = %s
            WHERE sc.student_id = %s
            ORDER BY a.deadline ASC
        """, (user['id'], user['id']))

        if assignments:
            for assign in assignments:
                deadline_passed = assign['deadline'] < date.today()
                submitted = assign['submitted_at'] is not None

                status_icon = "✅" if submitted else ("⚠️" if deadline_passed else "📌")

                with st.expander(f"{status_icon} {assign['title']} - {assign['course_name']}"):
                    st.write(f"**Description:** {assign['description']}")
                    st.write(f"**Deadline:** {assign['deadline']}")

                    if submitted:
                        st.success(f"✅ Submitted on {assign['submitted_at']}")
                    elif deadline_passed:
                        st.error("⚠️ Deadline passed!")
                    else:
                        if st.button("Submit Assignment", key=f"submit_{assign['id']}"):
                            execute_query("""
                                INSERT INTO assignment_submissions
                                (assignment_id, student_id, submitted_at, status)
                                VALUES (%s, %s, %s, 'submitted')
                            """, (assign['id'], user['id'], datetime.now()), fetch=False)
                            st.success("✅ Assignment submitted!")
                            st.rerun()
        else:
            st.info("No assignments yet")
def course_enrollment(student_id):
    """Student Course Enrollment Page"""
    st.title("📚 Course Enrollment")

    # Fetch all available courses
    available_courses = execute_query("""
        SELECT c.id, c.course_code, c.course_name, u.name as teacher_name
        FROM courses c
        LEFT JOIN users u ON c.teacher_id = u.id
    """)

    # Fetch student enrolled courses
    enrolled = execute_query("""
        SELECT c.id, c.course_code, c.course_name
        FROM student_courses sc
        JOIN courses c ON sc.course_id = c.id
        WHERE sc.student_id = %s
    """, (student_id,))

    enrolled_ids = {c['id'] for c in enrolled}

    st.subheader("📘 My Enrolled Courses")
    if enrolled:
        for c in enrolled:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"{c['course_code']} - {c['course_name']}")
            with col2:
                if st.button("❌ Drop", key=f"drop_{c['id']}"):
                    execute_query(
                        "DELETE FROM student_courses WHERE student_id=%s AND course_id=%s",
                        (student_id, c['id']),
                        fetch=False
                    )
                    st.success("Dropped Successfully!")
                    st.rerun()
    else:
        st.info("Not enrolled in any course yet.")

    st.markdown("---")
    st.subheader("📚 Available Courses")

    for course in available_courses:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{course['course_code']} - {course['course_name']}**")
            st.caption(f"👨‍🏫 Teacher: {course['teacher_name']}")
        with col2:
            if course['id'] in enrolled_ids:
                st.button("Enrolled", disabled=True, key=f"en_{course['id']}")
            else:
                if st.button("Enroll", key=f"enroll_{course['id']}"):
                    execute_query("""
                        INSERT INTO student_courses (student_id, course_id)
                        VALUES (%s, %s)
                    """, (student_id, course['id']), fetch=False)
                    st.success("Enrolled Successfully!")
                    st.rerun()
def admin_announcements():
    """Admin Announcements + Role-Based Notifications"""
    st.title("📢 Admin Announcements")

    st.subheader("Send Announcement")

    message = st.text_area("Announcement Message")

    target = st.selectbox(
        "Send To",
        ["All Users", "Students", "Teachers", "Parents"]
    )

    if st.button("📤 Send Announcement"):
        if not message.strip():
            st.error("Message cannot be empty")
            return

        # Map roles
        role_map = {
            "Students": "student",
            "Teachers": "teacher",
            "Parents": "parent"
        }

        if target == "All Users":
            users = execute_query("SELECT id FROM users WHERE is_approved = TRUE")
        else:
            users = execute_query(
                "SELECT id FROM users WHERE role = %s AND is_approved = TRUE",
                (role_map[target],)
            )

        # Insert notifications
        for u in users:
            execute_query("""
                INSERT INTO notifications (user_id, message, type, created_at, is_read)
                VALUES (%s, %s, %s, %s, 0)
            """, (u['id'], message, "announcement", datetime.now()), fetch=False)

        st.success(f"Sent to {len(users)} user(s)")
        log_activity(st.session_state.user['id'], "announcement_sent", f"Target: {target}")
        st.balloons()

    st.markdown("---")
    st.subheader("📋 Recent Announcements")

    recent = execute_query("""
        SELECT message, created_at FROM notifications
        WHERE type = 'announcement'
        ORDER BY created_at DESC LIMIT 20
    """)

    if recent:
        for ann in recent:
            with st.expander(f"📢 {ann['created_at']}"):
                st.write(ann['message'])
    else:
        st.info("No announcements found")
def manage_user_roles():
    """Admin can change user roles"""
    st.title("🧩 Manage User Roles")

    users = execute_query("""
        SELECT id, user_uid, name, email, role, is_approved
        FROM users ORDER BY role, name
    """)

    if not users:
        st.info("No users found")
        return

    df = pd.DataFrame(users)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("Change User Role")

    user_list = {f"{u['user_uid']} - {u['name']} ({u['role']})": u['id'] for u in users}
    selected_user = st.selectbox("Select User", list(user_list.keys()))

    new_role = st.selectbox("New Role", ["admin", "teacher", "student", "parent"])

    if st.button("Update Role"):
        user_id = user_list[selected_user]

        execute_query(
            "UPDATE users SET role = %s WHERE id = %s",
            (new_role, user_id), fetch=False
        )

        st.success("Role Updated Successfully!")
        log_activity(st.session_state.user['id'], "role_changed", f"User ID: {user_id}")
        st.rerun()
def require_role(allowed_roles):
    """Block unauthorized access"""
    user = st.session_state.user
    if user['role'] not in allowed_roles:
        st.error("❌ Access Denied.")
        st.stop()

# ============================================
# MAIN APPLICATION
# ============================================

def initialize_session():
    """Initialize session state"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = None

def create_navigation(role):
    """Create role-based navigation menu"""

    if role == 'admin':
       return st.radio("📋 Navigation", [
        "🏠 Dashboard",
        "📋 Approve Users",
        "📢 Announcements",     # NEW
        "🧩 Manage Roles",       # NEW
        "📚 Manage Courses",
        "📦 Bulk Operations",
        "📊 Reports",
        "📈 Analytics",
        "🔔 Notifications"
    ], label_visibility="collapsed")

    elif role == 'teacher':
        return st.radio("📋 Navigation", [
            "🏠 Dashboard",
            "📝 Mark Attendance",
            "📊 Enter Grades",
            "📝 Assignments",
            "📊 Reports",
            "🔔 Notifications"
        ], label_visibility="collapsed")

    elif role == 'student':
       return st.radio("📋 Navigation", [
        "🏠 Dashboard",
        "📚 Course Enrollment",   # NEW
        "👁️ View Attendance",
        "📊 My Grades & GPA",
        "📝 Assignments",
        "🔔 Notifications"
    ], label_visibility="collapsed")


    elif role == 'parent':
        return st.radio("📋 Navigation", [
            "🏠 Dashboard",
            "📊 Child's Performance",
            "🔔 Notifications"
        ], label_visibility="collapsed")

def route_page(page, user):
    """Route to appropriate page"""

    if page == "🏠 Dashboard" and user['role'] == 'admin':
        admin_dashboard()
    elif page == "📋 Approve Users":
        approve_users()
    elif page == "📢 Announcements":
        require_role(['admin'])
        admin_announcements()
    elif page == "🧩 Manage Roles":
        require_role(['admin'])
        manage_user_roles()
    elif page == "📚 Manage Courses":
        manage_courses()
    elif page == "📦 Bulk Operations":
        bulk_import_export()
    elif page == "📊 Reports" and user['role'] in ['admin', 'teacher']:
        generate_reports()
    elif page == "📈 Analytics":
        predictive_analytics()
    elif page == "🏠 Dashboard" and user['role'] == 'teacher':
        teacher_dashboard(user['id'])
    elif page == "📝 Mark Attendance":
        mark_attendance(user['id'])
    elif page == "📊 Enter Grades":
        enter_grades(user['id'])
    elif page == "🏠 Dashboard" and user['role'] == 'student':
        student_dashboard(user['id'])
    elif page == "👁️ View Attendance":
        view_attendance(user['id'])
    elif page == "📚 Course Enrollment":
        course_enrollment(user['id'])
    elif page == "📊 My Grades & GPA":
        view_grades(user['id'])
    elif page == "🏠 Dashboard" and user['role'] == 'parent':
        parent_dashboard(user['id'])
    elif page == "📊 Child's Performance":
        parent_dashboard(user['id'])
    elif page == "📝 Assignments":
        assignment_tracking()
    elif page == "🔔 Notifications":
        notifications_center()
    else:
        st.error("❌ Page not found or access denied")

def main():
    """Main application"""

    st.set_page_config(
        page_title="APAS - Academic Performance Analytics",
        page_icon="🎓",
        layout="wide"
    )

    initialize_session()

    if not st.session_state.logged_in:
        login_page()
        return

    if not check_session_timeout():
        return

    user = st.session_state.user

    with st.sidebar:
        st.title("🎓 APAS")
        st.markdown("---")

        st.markdown(f"### Welcome!")
        st.write(f"**{user['name']}**")
        st.caption(f"Role: {user['role'].title()}")
        st.caption(f"ID: {user['user_uid']}")

        st.markdown("---")

        page = create_navigation(user['role'])

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

        st.markdown("---")
        st.caption("© 2025 APAS System")
        st.caption("v1.0 - All Features")

    route_page(page, user)

if __name__ == "__main__":
    main()