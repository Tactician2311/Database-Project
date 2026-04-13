# Course Management System — Database Project

A full-stack learning management system built with **Flask**, **MySQL**, and vanilla **HTML/CSS/JS**.

---

## Project Structure

```
Database-Project/
├── courseDB.sql          ← Schema: tables, indexes, views
├── generate_inserts.py   ← Script to produce inserts.sql
├── inserts.sql           ← Generated seed data (100k+ students)
├── API.py                ← Flask REST API (raw SQL, JWT auth)
├── index.html            ← Frontend SPA
├── styles.css            ← Frontend styles
├── app.js                ← Frontend JavaScript
├── postman_collection.json ← Postman API collection
└── README.md
```

---

## Setup Instructions

### 1. Install MySQL and create the database

```bash
mysql -u root -p < courseDB.sql
```

### 2. Load seed data

> ⚠️ `inserts.sql` is large (~165MB / 1.9M lines). Use `mysql` CLI for best performance:

```bash
mysql -u root -p school_db < inserts.sql
```

### 3. Install Python dependencies

```bash
pip install flask mysql-connector-python PyJWT bcrypt
```

### 4. Configure environment (optional)

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=yourpassword
export DB_NAME=school_db
export JWT_SECRET=your_secret_key_here
export PORT=5000
```

### 5. Run the API

```bash
python API.py
```

API runs at: `http://127.0.0.1:5000`

### 6. Open the Frontend

Open `index.html` in a browser. Make sure the API is running on port 5000.

---

## Default Seed Accounts

All seeded users have these default passwords:

| Role     | Email                    | Password      |
|----------|--------------------------|---------------|
| Admin    | admin1@university.edu    | admin123      |
| Admin    | admin2@university.edu    | admin123      |
| Lecturer | (auto-generated)         | lecturer123   |
| Student  | (auto-generated)         | student123    |

---

## API Endpoints

### Auth
| Method | Endpoint       | Description         | Auth Required |
|--------|---------------|---------------------|---------------|
| POST   | /register      | Register new user   | No            |
| POST   | /login         | Login, get JWT      | No            |
| GET    | /users/{id}    | Get user profile    | Yes           |

### Courses
| Method | Endpoint                    | Description                   | Auth    |
|--------|-----------------------------|-------------------------------|---------|
| GET    | /courses                    | All courses                   | No      |
| GET    | /courses/{id}               | Single course                 | No      |
| GET    | /courses/lecturer/{id}      | Courses by lecturer           | No      |
| GET    | /courses/student/{id}       | Courses for a student         | No      |
| POST   | /courses                    | Create course (admin only)    | Admin   |

### Enrollment
| Method | Endpoint           | Description                         | Auth    |
|--------|--------------------|-------------------------------------|---------|
| POST   | /enroll            | Enroll student in course            | Yes     |
| GET    | /members/{cid}     | Members of a course                 | Yes     |

### Calendar Events
| Method | Endpoint                       | Description                          | Auth              |
|--------|--------------------------------|--------------------------------------|-------------------|
| GET    | /events/course/{id}            | Events for a course                  | Yes               |
| GET    | /events/student?user_id=&date= | Events for a student on a date       | Yes               |
| POST   | /events                        | Create event (admin/lecturer)        | Admin/Lecturer    |

### Forums & Threads
| Method | Endpoint                   | Description                         | Auth              |
|--------|----------------------------|-------------------------------------|-------------------|
| GET    | /forums/{cid}              | Forums for a course                 | Yes               |
| POST   | /forums                    | Create forum (admin/lecturer)       | Admin/Lecturer    |
| GET    | /threads/{forum_id}        | Root threads for a forum            | Yes               |
| GET    | /threads/{post_id}/replies | Replies to a post (nested/reddit)   | Yes               |
| POST   | /threads                   | Add thread or reply                 | Yes               |

### Course Content
| Method | Endpoint              | Description                      | Auth              |
|--------|-----------------------|----------------------------------|-------------------|
| GET    | /sections/{cid}       | Sections + items for a course    | Yes               |
| POST   | /sections             | Create section                   | Admin/Lecturer    |
| GET    | /items/{section_id}   | Items for a section              | Yes               |
| POST   | /items                | Add item to section              | Admin/Lecturer    |

### Assignments
| Method | Endpoint                  | Description                     | Auth              |
|--------|---------------------------|---------------------------------|-------------------|
| GET    | /assignments/{cid}        | Assignments for a course        | Yes               |
| POST   | /assignments              | Create assignment                | Admin/Lecturer    |
| POST   | /submit                   | Student submits assignment      | Student           |
| POST   | /grade                    | Lecturer grades submission      | Admin/Lecturer    |
| GET    | /grades/student/{id}      | Student's grades + average      | Yes               |

### Reports (Views)
| Method | Endpoint                            | Description                        | Auth |
|--------|-------------------------------------|------------------------------------|------|
| GET    | /reports/courses_50_students        | Courses with ≥50 students          | Yes  |
| GET    | /reports/students_5_courses         | Students in ≥5 courses             | Yes  |
| GET    | /reports/lecturers_3_courses        | Lecturers teaching ≥3 courses      | Yes  |
| GET    | /reports/top_10_courses             | Top 10 most enrolled courses       | Yes  |
| GET    | /reports/top_10_students            | Top 10 students by grade average   | Yes  |

---

## Using the Postman Collection

1. Open Postman → Import → select `postman_collection.json`
2. Run the **Login** request first — the token is automatically saved to collection variables
3. All other authenticated requests use `{{token}}` automatically

---

## Data Constraints Satisfied

| Constraint                       | Value          |
|----------------------------------|----------------|
| Students                         | 100,500        |
| Courses                          | 210            |
| Min courses per student          | 3              |
| Max courses per student          | 6              |
| Min students per course          | 10             |
| Max courses per lecturer         | 5              |
| Lecturers                        | 300            |
| Total enrollments                | ~450,000       |
| Assignments per course           | 3              |
| Sections per course              | 3              |

---

## Bonus Features Implemented

- ✅ JWT Authentication (`Authorization: <token>` header)
- ✅ Role-based access control (admin / lecturer / student)
- ✅ Frontend SPA (HTML/CSS/JS, dark mode, responsive)
- ✅ Indexes on all high-traffic columns
- ✅ Thread-safe connection pooling
- ✅ Input validation + meaningful error messages

---

## Regenerating Seed Data

If you need to regenerate `inserts.sql`:

```bash
python generate_inserts.py
```

This takes ~2 minutes and produces a fresh `inserts.sql`.
