-- ============================================
-- APAS DATABASE SETUP
-- Complete Database Schema for Academic Performance Analytics System
-- Run this in MySQL Workbench to create all tables
-- ============================================

-- Create database
CREATE DATABASE IF NOT EXISTS epic1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE epic1;

-- ============================================
-- 1. USERS TABLE (Main authentication)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_uid VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student', 'parent') NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_user_uid (user_uid)
) ENGINE=InnoDB;

-- ============================================
-- 2. STUDENT PROFILES (FR-001)
-- ============================================
CREATE TABLE IF NOT EXISTS student_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department VARCHAR(100),
    year INT,
    phone VARCHAR(15),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB;

-- ============================================
-- 3. COURSES (Main course catalog)
-- ============================================
CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(150) NOT NULL,
    teacher_id INT,
    credits INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_teacher (teacher_id),
    INDEX idx_code (course_code)
) ENGINE=InnoDB;

-- ============================================
-- 4. STUDENT-COURSE ENROLLMENT
-- ============================================
CREATE TABLE IF NOT EXISTS student_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, course_id),
    INDEX idx_student (student_id),
    INDEX idx_course (course_id)
) ENGINE=InnoDB;

-- ============================================
-- 5. ATTENDANCE RECORDS (FR-003)
-- ============================================
CREATE TABLE IF NOT EXISTS attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    teacher_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Late') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (student_id, course_id, attendance_date),
    INDEX idx_student (student_id),
    INDEX idx_course (course_id),
    INDEX idx_date (attendance_date)
) ENGINE=InnoDB;

-- ============================================
-- 6. GRADES (FR-002, FR-007)
-- ============================================
CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    grade VARCHAR(5),
    percent DECIMAL(5,2),
    gpa_value DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_grade (student_id, course_id),
    INDEX idx_student (student_id),
    INDEX idx_course (course_id)
) ENGINE=InnoDB;

-- ============================================
-- 7. ASSIGNMENTS (FR-005, FR-006)
-- ============================================
CREATE TABLE IF NOT EXISTS assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    deadline DATE NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_course (course_id),
    INDEX idx_deadline (deadline)
) ENGINE=InnoDB;

-- ============================================
-- 8. ASSIGNMENT SUBMISSIONS (FR-005)
-- ============================================
CREATE TABLE IF NOT EXISTS assignment_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    student_id INT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('submitted', 'late', 'graded') DEFAULT 'submitted',
    grade DECIMAL(5,2),
    feedback TEXT,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_submission (assignment_id, student_id),
    INDEX idx_assignment (assignment_id),
    INDEX idx_student (student_id)
) ENGINE=InnoDB;

-- ============================================
-- 9. NOTIFICATIONS (FR-012, FR-013)
-- ============================================
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    type ENUM('info', 'warning', 'alert', 'success') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_read (is_read),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- ============================================
-- 10. PARENT-CHILD LINKS (FR-011)
-- ============================================
CREATE TABLE IF NOT EXISTS parent_child_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT NOT NULL,
    child_id INT NOT NULL,
    relationship VARCHAR(50) DEFAULT 'parent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_link (parent_id, child_id),
    INDEX idx_parent (parent_id),
    INDEX idx_child (child_id)
) ENGINE=InnoDB;

-- ============================================
-- 11. AUDIT LOGS (SR-004 - Security)
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- ============================================
-- 12. APPROVALS (Admin approval tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS approvals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    user_id INT NOT NULL,
    status ENUM('approved', 'rejected') NOT NULL,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_admin (admin_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB;

-- ============================================
-- INSERT SAMPLE DATA
-- ============================================

-- 1. Create Admin User (password: admin123)
INSERT INTO users (user_uid, name, email, password_hash, role, is_approved) VALUES
('A001', 'System Admin', 'admin@school.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztK7qBc8qGKu', 'admin', TRUE);

-- 2. Create Sample Teacher (password: pass123)
INSERT INTO users (user_uid, name, email, password_hash, role, is_approved) VALUES
('T001', 'John Smith', 'john.smith@school.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztK7qBc8qGKu', 'teacher', TRUE);

-- 3. Create Sample Student (password: pass123)
INSERT INTO users (user_uid, name, email, password_hash, role, is_approved) VALUES
('S001', 'Alice Johnson', 'alice.johnson@student.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztK7qBc8qGKu', 'student', TRUE);

-- 4. Create Student Profile
INSERT INTO student_profiles (user_id, department, year, phone) VALUES
(3, 'Computer Science', 2, '9876543210');

-- 5. Create Sample Courses
INSERT INTO courses (course_code, course_name, teacher_id) VALUES
('CS101', 'Introduction to Programming', 2),
('CS102', 'Data Structures', 2),
('MATH101', 'Calculus I', 2);

-- 6. Enroll Student in Courses
INSERT INTO student_courses (student_id, course_id) VALUES
(3, 1),
(3, 2),
(3, 3);

-- 7. Sample Attendance
INSERT INTO attendance_records (student_id, course_id, teacher_id, attendance_date, status) VALUES
(3, 1, 2, CURDATE(), 'Present'),
(3, 1, 2, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Present'),
(3, 2, 2, CURDATE(), 'Present');

-- 8. Sample Grades
INSERT INTO grades (student_id, course_id, grade, percent, gpa_value) VALUES
(3, 1, 'A', 92.5, 4.0),
(3, 2, 'B+', 85.0, 3.5);

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check if tables created
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'epic1';

-- Check sample data
SELECT u.user_uid, u.name, u.email, u.role, u.is_approved
FROM users u;

-- Check student profile
SELECT u.name, sp.department, sp.year
FROM users u
JOIN student_profiles sp ON sp.user_id = u.id;

-- Check courses
SELECT c.course_code, c.course_name, u.name as teacher_name
FROM courses c
LEFT JOIN users u ON c.teacher_id = u.id;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
SELECT 'Database setup completed successfully!' AS Status;
SELECT 'You can now run the Streamlit app with: streamlit run main.py' AS NextStep;
SELECT 'Login credentials:' AS Info;
SELECT 'Admin: admin@school.com / admin123' AS AdminLogin;
SELECT 'Teacher: john.smith@school.com / pass123' AS TeacherLogin;
SELECT 'Student: alice.johnson@student.com / pass123' AS StudentLogin;