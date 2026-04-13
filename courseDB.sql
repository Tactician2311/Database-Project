# =============================
# COURSE MANAGEMENT SYSTEM (COMPLETE BACKEND)
# - MySQL Schema (normalized)
# - Indexes
# - Views (reports)
# - Data generator (Python -> SQL output with constraints)
# - Flask API (RAW SQL, JWT auth, role guards)
# =============================

# =============================
# DATABASE SCHEMA (MySQL)
# =============================

CREATE DATABASE IF NOT EXISTS school_db;
USE school_db;

-- USERS
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','lecturer','student') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- COURSES (1 lecturer per course)
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    lecturer_id INT NOT NULL,
    FOREIGN KEY (lecturer_id) REFERENCES users(user_id)
);

-- ENROLLMENTS (student-course)
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    UNIQUE(user_id, course_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- SECTIONS
CREATE TABLE sections (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(255),
    sequence_order INT,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- SECTION ITEMS (content)
CREATE TABLE section_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    section_id INT NOT NULL,
    title VARCHAR(255),
    content TEXT,
    FOREIGN KEY (section_id) REFERENCES sections(section_id)
);

-- CALENDAR EVENTS
CREATE TABLE calendar_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    title VARCHAR(255),
    type VARCHAR(50),
    event_date DATE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- FORUMS
CREATE TABLE forums (
    forum_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    title VARCHAR(255),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- THREADS (nested)
CREATE TABLE threads (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    forum_id INT,
    author_id INT,
    parent_post_id INT NULL,
    content TEXT,
    FOREIGN KEY (forum_id) REFERENCES forums(forum_id),
    FOREIGN KEY (author_id) REFERENCES users(user_id)
);

-- ASSIGNMENTS
CREATE TABLE assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    title VARCHAR(255),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- SUBMISSIONS
CREATE TABLE submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT,
    student_id INT,
    grade DECIMAL(5,2),
    FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id),
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- INDEXES (performance)
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_enroll_user ON enrollments(user_id);
CREATE INDEX idx_enroll_course ON enrollments(course_id);

# =============================
# REPORT VIEWS
# =============================

CREATE VIEW courses_50_students AS
SELECT course_id, COUNT(user_id) total
FROM enrollments GROUP BY course_id HAVING total >= 50;

CREATE VIEW students_5_courses AS
SELECT user_id, COUNT(course_id) total
FROM enrollments GROUP BY user_id HAVING total >= 5;

CREATE VIEW lecturers_3_courses AS
SELECT lecturer_id, COUNT(course_id) total
FROM courses GROUP BY lecturer_id HAVING total >= 3;

CREATE VIEW top_courses AS
SELECT course_id, COUNT(user_id) total
FROM enrollments GROUP BY course_id ORDER BY total DESC LIMIT 10;

CREATE VIEW top_students AS
SELECT student_id, AVG(grade) avg_grade
FROM submissions GROUP BY student_id ORDER BY avg_grade DESC LIMIT 10;

