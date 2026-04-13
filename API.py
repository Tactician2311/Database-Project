"""
API.py  –  Course Management System REST API
Flask + MySQL (raw SQL, no ORM) + JWT Auth
"""

import os
import datetime
from functools import wraps

import bcrypt
import jwt
import mysql.connector
from mysql.connector import pooling
from flask import Flask, request, jsonify, g

# ── App & Config ─────────────────────────────────────────────────────────────
app = Flask(__name__)

SECRET = os.environ.get("JWT_SECRET", "change_this_in_production")

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "user":     os.environ.get("DB_USER",     "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME",     "school_db"),
}

# Connection pool — thread-safe, one connection per request
pool = pooling.MySQLConnectionPool(
    pool_name="school_pool",
    pool_size=10,
    **DB_CONFIG
)

# ── CORS ─────────────────────────────────────────────────────────────────────
from flask_cors import CORS
CORS(app)

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

@app.route("/", methods=["OPTIONS", "GET"])
def root():
    return jsonify({"status": "ok"}), 200

@app.route("/<path:p>", methods=["OPTIONS"])
def options_handler(p):
    from flask import Response
    r = Response()
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return r, 200

# ── DB Helpers ───────────────────────────────────────────────────────────────
def get_db():
    """Return (connection, cursor) for this request; auto-close on teardown."""
    if "db" not in g:
        g.db     = pool.get_connection()
        g.cursor = g.db.cursor(dictionary=True)
    return g.db, g.cursor

@app.teardown_appcontext
def close_db(exc):
    cursor = g.pop("cursor", None)
    db     = g.pop("db", None)
    if cursor: cursor.close()
    if db:     db.close()

def query(sql, params=None, commit=False):
    db, cursor = get_db()
    cursor.execute(sql, params or ())
    if commit:
        db.commit()
        return cursor.lastrowid
    return cursor.fetchall()

def query_one(sql, params=None):
    db, cursor = get_db()
    cursor.execute(sql, params or ())
    return cursor.fetchone()

# ── Auth Helpers ─────────────────────────────────────────────────────────────
def make_token(user):
    payload = {
        "id":   user["user_id"],
        "role": user["role"],
        "exp":  datetime.datetime.utcnow() + datetime.timedelta(hours=8),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").strip()
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            data = jwt.decode(token, SECRET, algorithms=["HS256"])
            request.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.user["role"] not in roles:
                return jsonify({"error": "Forbidden — insufficient role"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ── Register ─────────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    d = request.json or {}
    required = ["name", "email", "password", "role"]
    if not all(k in d for k in required):
        return jsonify({"error": f"Required fields: {required}"}), 400
    if d["role"] not in ("admin", "lecturer", "student"):
        return jsonify({"error": "role must be admin, lecturer, or student"}), 400
    if query_one("SELECT user_id FROM users WHERE email=%s", (d["email"],)):
        return jsonify({"error": "Email already registered"}), 409
    hashed = bcrypt.hashpw(d["password"].encode(), bcrypt.gensalt()).decode()
    uid = query(
        "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
        (d["name"], d["email"], hashed, d["role"]), commit=True
    )
    return jsonify({"msg": "User created", "user_id": uid}), 201

# ── Login ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    d = request.json or {}
    u = query_one("SELECT * FROM users WHERE email=%s", (d.get("email"),))
    if not u:
        return jsonify({"error": "Invalid credentials"}), 401
    try:
        match = bcrypt.checkpw(d.get("password", "").encode(), u["password"].encode())
    except ValueError:
        # Fallback for plaintext-stored dev passwords
        match = d.get("password") == u["password"]
    if not match:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({
        "token":   make_token(u),
        "user_id": u["user_id"],
        "role":    u["role"],
        "name":    u["name"],
    })

# ── Users ─────────────────────────────────────────────────────────────────────
@app.route("/users/<int:uid>", methods=["GET"])
@token_required
def get_user(uid):
    u = query_one("SELECT user_id,name,email,role,created_at FROM users WHERE user_id=%s", (uid,))
    if not u:
        return jsonify({"error": "Not found"}), 404
    return jsonify(u)

# ── Courses ───────────────────────────────────────────────────────────────────
@app.route("/courses", methods=["GET"])
def all_courses():
    rows = query("""
        SELECT c.course_id, c.title, c.description,
               u.user_id AS lecturer_id, u.name AS lecturer_name
        FROM courses c
        JOIN users u ON c.lecturer_id = u.user_id
        ORDER BY c.course_id
    """)
    return jsonify(rows)

@app.route("/courses/<int:cid>", methods=["GET"])
def get_course(cid):
    row = query_one("""
        SELECT c.course_id, c.title, c.description,
               u.user_id AS lecturer_id, u.name AS lecturer_name
        FROM courses c
        JOIN users u ON c.lecturer_id = u.user_id
        WHERE c.course_id=%s
    """, (cid,))
    if not row:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(row)

@app.route("/courses/lecturer/<int:lid>", methods=["GET"])
def lecturer_courses(lid):
    rows = query("SELECT * FROM courses WHERE lecturer_id=%s", (lid,))
    return jsonify(rows)

@app.route("/courses/student/<int:sid>", methods=["GET"])
def student_courses(sid):
    rows = query("""
        SELECT c.* FROM courses c
        JOIN enrollments e ON c.course_id = e.course_id
        WHERE e.user_id=%s
    """, (sid,))
    return jsonify(rows)

@app.route("/courses", methods=["POST"])
@require_role("admin")
def create_course():
    d = request.json or {}
    if not d.get("title") or not d.get("lecturer_id"):
        return jsonify({"error": "title and lecturer_id required"}), 400
    # Verify lecturer exists and has ≤4 courses (max 5)
    lec = query_one("SELECT role FROM users WHERE user_id=%s", (d["lecturer_id"],))
    if not lec or lec["role"] != "lecturer":
        return jsonify({"error": "lecturer_id must refer to a lecturer user"}), 400
    count = query_one("SELECT COUNT(*) AS c FROM courses WHERE lecturer_id=%s", (d["lecturer_id"],))
    if count["c"] >= 5:
        return jsonify({"error": "Lecturer already teaches 5 courses (max)"}), 400
    cid = query(
        "INSERT INTO courses (title,description,lecturer_id) VALUES (%s,%s,%s)",
        (d["title"], d.get("description", ""), d["lecturer_id"]), commit=True
    )
    return jsonify({"msg": "Course created", "course_id": cid}), 201

# ── Enroll ────────────────────────────────────────────────────────────────────
@app.route("/enroll", methods=["POST"])
@token_required
def enroll():
    d = request.json or {}
    uid = d.get("user_id")
    cid = d.get("course_id")
    if not uid or not cid:
        return jsonify({"error": "user_id and course_id required"}), 400
    # Only students enroll
    u = query_one("SELECT role FROM users WHERE user_id=%s", (uid,))
    if not u or u["role"] != "student":
        return jsonify({"error": "Only students can enroll"}), 400
    # Max 6 courses
    cnt = query_one("SELECT COUNT(*) AS c FROM enrollments WHERE user_id=%s", (uid,))
    if cnt["c"] >= 6:
        return jsonify({"error": "Student already enrolled in 6 courses (max)"}), 400
    # Check course exists
    if not query_one("SELECT course_id FROM courses WHERE course_id=%s", (cid,)):
        return jsonify({"error": "Course not found"}), 404
    # Check already enrolled
    if query_one("SELECT enrollment_id FROM enrollments WHERE user_id=%s AND course_id=%s", (uid, cid)):
        return jsonify({"error": "Already enrolled"}), 409
    eid = query("INSERT INTO enrollments (user_id,course_id) VALUES (%s,%s)", (uid, cid), commit=True)
    return jsonify({"msg": "Enrolled", "enrollment_id": eid}), 201

# ── Members ───────────────────────────────────────────────────────────────────
@app.route("/members/<int:cid>", methods=["GET"])
@token_required
def members(cid):
    rows = query("""
        SELECT u.user_id, u.name, u.email, u.role, e.enrolled_at
        FROM users u
        JOIN enrollments e ON u.user_id = e.user_id
        WHERE e.course_id=%s
    """, (cid,))
    return jsonify(rows)

# ── Calendar Events ───────────────────────────────────────────────────────────
@app.route("/events/course/<int:cid>", methods=["GET"])
@token_required
def events_for_course(cid):
    rows = query("SELECT * FROM calendar_events WHERE course_id=%s ORDER BY event_date", (cid,))
    return jsonify(rows)

@app.route("/events/student", methods=["GET"])
@token_required
def events_for_student():
    uid  = request.args.get("user_id")
    date = request.args.get("date")
    if not uid or not date:
        return jsonify({"error": "user_id and date query params required"}), 400
    rows = query("""
        SELECT ce.* FROM calendar_events ce
        JOIN enrollments e ON ce.course_id = e.course_id
        WHERE e.user_id=%s AND ce.event_date=%s
        ORDER BY ce.event_date
    """, (uid, date))
    return jsonify(rows)

@app.route("/events", methods=["POST"])
@require_role("admin", "lecturer")
def create_event():
    d = request.json or {}
    if not all(k in d for k in ["course_id", "title", "event_date"]):
        return jsonify({"error": "course_id, title, event_date required"}), 400
    eid = query(
        "INSERT INTO calendar_events (course_id,title,type,event_date) VALUES (%s,%s,%s,%s)",
        (d["course_id"], d["title"], d.get("type", "event"), d["event_date"]), commit=True
    )
    return jsonify({"msg": "Event created", "event_id": eid}), 201

# ── Forums ────────────────────────────────────────────────────────────────────
@app.route("/forums/<int:cid>", methods=["GET"])
@token_required
def get_forums(cid):
    rows = query("SELECT * FROM forums WHERE course_id=%s", (cid,))
    return jsonify(rows)

@app.route("/forums", methods=["POST"])
@require_role("admin", "lecturer")
def create_forum():
    d = request.json or {}
    if not d.get("course_id") or not d.get("title"):
        return jsonify({"error": "course_id and title required"}), 400
    fid = query(
        "INSERT INTO forums (course_id,title) VALUES (%s,%s)",
        (d["course_id"], d["title"]), commit=True
    )
    return jsonify({"msg": "Forum created", "forum_id": fid}), 201

# ── Threads ───────────────────────────────────────────────────────────────────
@app.route("/threads/<int:fid>", methods=["GET"])
@token_required
def get_threads(fid):
    """Return all root threads for a forum."""
    rows = query("""
        SELECT t.*, u.name AS author_name
        FROM threads t
        JOIN users u ON t.author_id = u.user_id
        WHERE t.forum_id=%s AND t.parent_post_id IS NULL
        ORDER BY t.created_at DESC
    """, (fid,))
    return jsonify(rows)

@app.route("/threads/<int:post_id>/replies", methods=["GET"])
@token_required
def get_replies(post_id):
    """Return direct replies to a post (supports recursive nesting client-side)."""
    rows = query("""
        SELECT t.*, u.name AS author_name
        FROM threads t
        JOIN users u ON t.author_id = u.user_id
        WHERE t.parent_post_id=%s
        ORDER BY t.created_at
    """, (post_id,))
    return jsonify(rows)

@app.route("/threads", methods=["POST"])
@token_required
def add_thread():
    d = request.json or {}
    if not d.get("forum_id") or not d.get("author_id") or not d.get("content"):
        return jsonify({"error": "forum_id, author_id, content required"}), 400
    pid = query("""
        INSERT INTO threads (forum_id,author_id,parent_post_id,title,content)
        VALUES (%s,%s,%s,%s,%s)
    """, (
        d["forum_id"],
        d["author_id"],
        d.get("parent_post_id"),        # NULL for root, ID for reply
        d.get("title"),                 # title only on root posts
        d["content"],
    ), commit=True)
    return jsonify({"msg": "Thread post added", "post_id": pid}), 201

# ── Course Content ────────────────────────────────────────────────────────────
@app.route("/sections/<int:cid>", methods=["GET"])
@token_required
def get_sections(cid):
    rows = query("""
        SELECT s.*, 
               JSON_ARRAYAGG(JSON_OBJECT(
                   'item_id',  i.item_id,
                   'title',    i.title,
                   'item_type',i.item_type,
                   'content',  i.content
               )) AS items
        FROM sections s
        LEFT JOIN section_items i ON s.section_id = i.section_id
        WHERE s.course_id=%s
        GROUP BY s.section_id
        ORDER BY s.sequence_order
    """, (cid,))
    return jsonify(rows)

@app.route("/sections", methods=["POST"])
@require_role("admin", "lecturer")
def add_section():
    d = request.json or {}
    if not d.get("course_id") or not d.get("title"):
        return jsonify({"error": "course_id and title required"}), 400
    sid = query(
        "INSERT INTO sections (course_id,title,sequence_order) VALUES (%s,%s,%s)",
        (d["course_id"], d["title"], d.get("order", 0)), commit=True
    )
    return jsonify({"msg": "Section created", "section_id": sid}), 201

@app.route("/items", methods=["POST"])
@require_role("admin", "lecturer")
def add_item():
    d = request.json or {}
    if not all(k in d for k in ["section_id", "title", "item_type"]):
        return jsonify({"error": "section_id, title, item_type required"}), 400
    if d["item_type"] not in ("link", "file", "slide", "text"):
        return jsonify({"error": "item_type must be link, file, slide, or text"}), 400
    iid = query(
        "INSERT INTO section_items (section_id,title,item_type,content) VALUES (%s,%s,%s,%s)",
        (d["section_id"], d["title"], d["item_type"], d.get("content", "")), commit=True
    )
    return jsonify({"msg": "Item added", "item_id": iid}), 201

@app.route("/items/<int:sid>", methods=["GET"])
@token_required
def get_items(sid):
    rows = query("SELECT * FROM section_items WHERE section_id=%s", (sid,))
    return jsonify(rows)

# ── Assignments ───────────────────────────────────────────────────────────────
@app.route("/assignments/<int:cid>", methods=["GET"])
@token_required
def get_assignments(cid):
    rows = query("SELECT * FROM assignments WHERE course_id=%s", (cid,))
    return jsonify(rows)

@app.route("/assignments", methods=["POST"])
@require_role("admin", "lecturer")
def create_assignment():
    d = request.json or {}
    if not d.get("course_id") or not d.get("title"):
        return jsonify({"error": "course_id and title required"}), 400
    aid = query(
        "INSERT INTO assignments (course_id,title,due_date) VALUES (%s,%s,%s)",
        (d["course_id"], d["title"], d.get("due_date")), commit=True
    )
    return jsonify({"msg": "Assignment created", "assignment_id": aid}), 201

@app.route("/submit", methods=["POST"])
@require_role("student")
def submit():
    d = request.json or {}
    if not d.get("assignment_id") or not d.get("student_id"):
        return jsonify({"error": "assignment_id and student_id required"}), 400
    # Check student is enrolled in the course this assignment belongs to
    enrolled = query_one("""
        SELECT e.enrollment_id FROM enrollments e
        JOIN assignments a ON e.course_id = a.course_id
        WHERE a.assignment_id=%s AND e.user_id=%s
    """, (d["assignment_id"], d["student_id"]))
    if not enrolled:
        return jsonify({"error": "Student not enrolled in this course"}), 403
    if query_one("SELECT submission_id FROM submissions WHERE assignment_id=%s AND student_id=%s",
                 (d["assignment_id"], d["student_id"])):
        return jsonify({"error": "Already submitted"}), 409
    subid = query(
        "INSERT INTO submissions (assignment_id,student_id,grade) VALUES (%s,%s,NULL)",
        (d["assignment_id"], d["student_id"]), commit=True
    )
    return jsonify({"msg": "Submitted", "submission_id": subid}), 201

@app.route("/grade", methods=["POST"])
@require_role("admin", "lecturer")
def grade():
    d = request.json or {}
    if not all(k in d for k in ["assignment_id", "student_id", "grade"]):
        return jsonify({"error": "assignment_id, student_id, grade required"}), 400
    try:
        g_val = float(d["grade"])
        if not (0 <= g_val <= 100):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "grade must be a number 0–100"}), 400
    query(
        "UPDATE submissions SET grade=%s WHERE assignment_id=%s AND student_id=%s",
        (g_val, d["assignment_id"], d["student_id"]), commit=True
    )
    return jsonify({"msg": "Grade recorded"})

@app.route("/grades/student/<int:sid>", methods=["GET"])
@token_required
def student_grades(sid):
    """All grades for a student with overall average."""
    rows = query("""
        SELECT a.course_id, a.title AS assignment_title, s.grade, s.submitted_at
        FROM submissions s
        JOIN assignments a ON s.assignment_id = a.assignment_id
        WHERE s.student_id=%s
        ORDER BY s.submitted_at
    """, (sid,))
    avg = query_one("""
        SELECT ROUND(AVG(grade),2) AS overall_average
        FROM submissions WHERE student_id=%s AND grade IS NOT NULL
    """, (sid,))
    return jsonify({"grades": rows, "overall_average": avg["overall_average"]})

# ── Reports ───────────────────────────────────────────────────────────────────
ALLOWED_VIEWS = {
    "courses_50_students",
    "students_5_courses",
    "lecturers_3_courses",
    "top_10_courses",
    "top_10_students",
}

@app.route("/reports/<name>", methods=["GET"])
@token_required
def reports(name):
    if name not in ALLOWED_VIEWS:
        return jsonify({"error": f"Unknown report. Available: {sorted(ALLOWED_VIEWS)}"}), 400
    rows = query(f"SELECT * FROM {name}")
    return jsonify(rows)

# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Course Management API"})

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
