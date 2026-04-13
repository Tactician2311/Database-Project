-- =============================================
-- COURSE MANAGEMENT SYSTEM - DATABASE SCHEMA
-- MySQL | Normalized | Indexed | Views
-- =============================================

CREATE DATABASE IF NOT EXISTS school_db;
USE school_db;

-- ── USERS ─────────────────────────────────────
CREATE TABLE users (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(120) UNIQUE NOT NULL,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('admin','lecturer','student') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── COURSES ───────────────────────────────────
-- One lecturer per course (lecturer_id FK)
CREATE TABLE courses (
    course_id   INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    lecturer_id INT NOT NULL,
    FOREIGN KEY (lecturer_id) REFERENCES users(user_id)
);

-- ── ENROLLMENTS ───────────────────────────────
-- Students <-> Courses (many-to-many)
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    course_id     INT NOT NULL,
    enrolled_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, course_id),
    FOREIGN KEY (user_id)   REFERENCES users(user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- ── SECTIONS ──────────────────────────────────
-- Course content is separated by sections
CREATE TABLE sections (
    section_id     INT AUTO_INCREMENT PRIMARY KEY,
    course_id      INT NOT NULL,
    title          VARCHAR(255) NOT NULL,
    sequence_order INT DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- ── SECTION ITEMS (Course Content) ────────────
-- Links, files, slides, text
CREATE TABLE section_items (
    item_id    INT AUTO_INCREMENT PRIMARY KEY,
    section_id INT NOT NULL,
    title      VARCHAR(255) NOT NULL,
    item_type  ENUM('link','file','slide','text') NOT NULL DEFAULT 'text',
    content    TEXT,
    FOREIGN KEY (section_id) REFERENCES sections(section_id)
);

-- ── CALENDAR EVENTS ───────────────────────────
CREATE TABLE calendar_events (
    event_id   INT AUTO_INCREMENT PRIMARY KEY,
    course_id  INT NOT NULL,
    title      VARCHAR(255) NOT NULL,
    type       VARCHAR(50),
    event_date DATE NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- ── FORUMS ────────────────────────────────────
CREATE TABLE forums (
    forum_id  INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title     VARCHAR(255) NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- ── THREADS (Reddit-style nested) ─────────────
-- parent_post_id NULL = root thread post
-- parent_post_id SET  = reply to a post
CREATE TABLE threads (
    post_id        INT AUTO_INCREMENT PRIMARY KEY,
    forum_id       INT NOT NULL,
    author_id      INT NOT NULL,
    parent_post_id INT NULL,
    title          VARCHAR(255),          -- only on root posts
    content        TEXT NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (forum_id)       REFERENCES forums(forum_id),
    FOREIGN KEY (author_id)      REFERENCES users(user_id),
    FOREIGN KEY (parent_post_id) REFERENCES threads(post_id)
);

-- ── ASSIGNMENTS ───────────────────────────────
CREATE TABLE assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id     INT NOT NULL,
    title         VARCHAR(255) NOT NULL,
    due_date      DATE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- ── SUBMISSIONS ───────────────────────────────
CREATE TABLE submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    student_id    INT NOT NULL,
    grade         DECIMAL(5,2) DEFAULT NULL,
    submitted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id),
    FOREIGN KEY (student_id)    REFERENCES users(user_id)
);

-- =============================================
-- INDEXES (Performance)
-- =============================================
CREATE INDEX idx_users_role         ON users(role);
CREATE INDEX idx_enroll_user        ON enrollments(user_id);
CREATE INDEX idx_enroll_course      ON enrollments(course_id);
CREATE INDEX idx_courses_lecturer   ON courses(lecturer_id);
CREATE INDEX idx_threads_forum      ON threads(forum_id);
CREATE INDEX idx_threads_parent     ON threads(parent_post_id);
CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_events_course      ON calendar_events(course_id);
CREATE INDEX idx_events_date        ON calendar_events(event_date);
CREATE INDEX idx_sections_course    ON sections(course_id);
CREATE INDEX idx_items_section      ON section_items(section_id);

-- =============================================
-- REPORT VIEWS
-- =============================================

-- All courses that have 50 or more students
CREATE VIEW courses_50_students AS
    SELECT c.course_id, c.title, COUNT(e.user_id) AS student_count
    FROM courses c
    JOIN enrollments e ON c.course_id = e.course_id
    GROUP BY c.course_id, c.title
    HAVING student_count >= 50;

-- All students enrolled in 5 or more courses
CREATE VIEW students_5_courses AS
    SELECT u.user_id, u.name, u.email, COUNT(e.course_id) AS course_count
    FROM users u
    JOIN enrollments e ON u.user_id = e.user_id
    WHERE u.role = 'student'
    GROUP BY u.user_id, u.name, u.email
    HAVING course_count >= 5;

-- All lecturers teaching 3 or more courses
CREATE VIEW lecturers_3_courses AS
    SELECT u.user_id, u.name, u.email, COUNT(c.course_id) AS course_count
    FROM users u
    JOIN courses c ON u.user_id = c.lecturer_id
    WHERE u.role = 'lecturer'
    GROUP BY u.user_id, u.name, u.email
    HAVING course_count >= 3;

-- Top 10 most enrolled courses
CREATE VIEW top_10_courses AS
    SELECT c.course_id, c.title, COUNT(e.user_id) AS enrollment_count
    FROM courses c
    JOIN enrollments e ON c.course_id = e.course_id
    GROUP BY c.course_id, c.title
    ORDER BY enrollment_count DESC
    LIMIT 10;

-- Top 10 students by overall grade average
CREATE VIEW top_10_students AS
    SELECT u.user_id, u.name, u.email, ROUND(AVG(s.grade), 2) AS overall_average
    FROM users u
    JOIN submissions s ON u.user_id = s.student_id
    WHERE s.grade IS NOT NULL
      AND u.role = 'student'
    GROUP BY u.user_id, u.name, u.email
    ORDER BY overall_average DESC
    LIMIT 10;
