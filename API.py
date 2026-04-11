
# =============================
# FLASK API (JWT + RAW SQL)
# =============================

from flask import Flask, request, jsonify
import mysql.connector
import jwt, datetime
from functools import wraps
import bcrypt

SECRET = "secretkey"

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

db = mysql.connector.connect(host="localhost",user="root",password="Boxer789",database="school_db")
cursor = db.cursor(dictionary=True)

# -------- AUTH HELPERS --------

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error":"Missing token"})
        try:
            data = jwt.decode(token, SECRET, algorithms=["HS256"])
            request.user = data
        except:
            return jsonify({"error":"Invalid token"})
        return f(*args, **kwargs)
    return decorated

# -------- REGISTER --------
@app.route('/register', methods=['POST'])
def register():
    d = request.json
    hashed = bcrypt.hashpw(d['password'].encode(), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                   (d['name'], d['email'], hashed, d['role']))
    db.commit()
    return jsonify({"msg":"created"})

# -------- LOGIN --------
@app.route('/login', methods=['POST'])
def login():
    d = request.json
    app.logger.warning(f"LOGIN ATTEMPT: Received email: '{d.get('email')}' password: '{d.get('password')}'")
    cursor.execute("SELECT * FROM users WHERE email=%s", (d.get('email'),))
    u = cursor.fetchone()
    if u:
        app.logger.warning(f"USER FOUND IN DB: {u['email']} with stored password: '{u['password']}'")
        valid_password = False
        try:
            if bcrypt.checkpw(d['password'].encode(), u['password'].encode()):
                valid_password = True
                app.logger.warning("Bcrypt match: SUCCEEDED")
            else:
                app.logger.warning("Bcrypt match: FAILED")
        except ValueError as e:
            app.logger.warning(f"Bcrypt hit ValueError: {e}. Falling back to plaintext compare...")
            if d['password'] == u['password']:
                valid_password = True
                app.logger.warning("Plaintext match: SUCCEEDED")
            else:
                app.logger.warning("Plaintext match: FAILED")
                
        if valid_password:
            token = jwt.encode({"id":u['user_id'],"role":u['role'],"exp":datetime.datetime.utcnow()+datetime.timedelta(hours=5)}, SECRET)
            return jsonify({"token":token})
    else:
        app.logger.warning("USER NOT FOUND in database.")
        
    return jsonify({"error":"invalid"})

# -------- COURSES --------
@app.route('/courses', methods=['GET'])
def all_courses():
    cursor.execute("SELECT * FROM courses")
    return jsonify(cursor.fetchall())

@app.route('/courses/lecturer/<int:id>')
def lecturer_courses(id):
    cursor.execute("SELECT * FROM courses WHERE lecturer_id=%s", (id,))
    return jsonify(cursor.fetchall())

@app.route('/courses/student/<int:id>')
def student_courses(id):
    cursor.execute("SELECT c.* FROM courses c JOIN enrollments e ON c.course_id=e.course_id WHERE e.user_id=%s", (id,))
    return jsonify(cursor.fetchall())

@app.route('/courses', methods=['POST'])
@token_required
def create_course():
    if request.user['role']!='admin': return jsonify({"error":"unauthorized"})
    d=request.json
    cursor.execute("INSERT INTO courses (title,description,lecturer_id) VALUES (%s,%s,%s)",(d['title'],d['description'],d['lecturer_id']))
    db.commit()
    return jsonify({"msg":"created"})

# -------- ENROLL --------
@app.route('/enroll', methods=['POST'])
def enroll():
    d=request.json
    cursor.execute("INSERT IGNORE INTO enrollments (user_id,course_id) VALUES (%s,%s)",(d['user_id'],d['course_id']))
    db.commit()
    return jsonify({"msg":"enrolled"})

@app.route('/members/<int:course_id>')
def members(course_id):
    cursor.execute("SELECT u.* FROM users u JOIN enrollments e ON u.user_id=e.user_id WHERE e.course_id=%s",(course_id,))
    return jsonify(cursor.fetchall())

# -------- EVENTS --------
@app.route('/events/course/<int:id>')
def events_course(id):
    cursor.execute("SELECT * FROM calendar_events WHERE course_id=%s",(id,))
    return jsonify(cursor.fetchall())

@app.route('/events/student')
def events_student():
    uid=request.args.get('user_id')
    date=request.args.get('date')
    cursor.execute("""
        SELECT ce.* FROM calendar_events ce
        JOIN enrollments e ON ce.course_id=e.course_id
        WHERE e.user_id=%s AND ce.event_date=%s
    """,(uid,date))
    return jsonify(cursor.fetchall())

@app.route('/events', methods=['POST'])
def create_event():
    d=request.json
    cursor.execute("INSERT INTO calendar_events (course_id,title,type,event_date) VALUES (%s,%s,%s,%s)",(d['course_id'],d['title'],d['type'],d['event_date']))
    db.commit()
    return jsonify({"msg":"created"})

# -------- FORUMS --------
@app.route('/forums/<int:course_id>')
def forums(course_id):
    cursor.execute("SELECT * FROM forums WHERE course_id=%s",(course_id,))
    return jsonify(cursor.fetchall())

@app.route('/forums', methods=['POST'])
def create_forum():
    d=request.json
    cursor.execute("INSERT INTO forums (course_id,title) VALUES (%s,%s)",(d['course_id'],d['title']))
    db.commit()
    return jsonify({"msg":"created"})

# -------- THREADS --------
@app.route('/threads/<int:forum_id>')
def threads(forum_id):
    cursor.execute("SELECT * FROM threads WHERE forum_id=%s",(forum_id,))
    return jsonify(cursor.fetchall())

@app.route('/threads', methods=['POST'])
def add_thread():
    d=request.json
    cursor.execute("INSERT INTO threads (forum_id,author_id,parent_post_id,content) VALUES (%s,%s,%s,%s)",(d['forum_id'],d['author_id'],d.get('parent_post_id'),d['content']))
    db.commit()
    return jsonify({"msg":"added"})

# -------- CONTENT --------
@app.route('/sections/<int:course_id>')
def get_sections(course_id):
    cursor.execute("SELECT * FROM sections WHERE course_id=%s",(course_id,))
    return jsonify(cursor.fetchall())

@app.route('/sections', methods=['POST'])
def add_section():
    d=request.json
    cursor.execute("INSERT INTO sections (course_id,title,sequence_order) VALUES (%s,%s,%s)",(d['course_id'],d['title'],d['order']))
    db.commit()
    return jsonify({"msg":"created"})

@app.route('/items/<int:section_id>')
def get_items(section_id):
    cursor.execute("SELECT * FROM section_items WHERE section_id=%s",(section_id,))
    return jsonify(cursor.fetchall())

@app.route('/items', methods=['POST'])
def add_item():
    d=request.json
    cursor.execute("INSERT INTO section_items (section_id,title,content) VALUES (%s,%s,%s)",(d['section_id'],d['title'],d['content']))
    db.commit()
    return jsonify({"msg":"added"})

# -------- ASSIGNMENTS --------
@app.route('/assignments', methods=['POST'])
def create_assignment():
    d=request.json
    cursor.execute("INSERT INTO assignments (course_id,title) VALUES (%s,%s)",(d['course_id'],d['title']))
    db.commit()
    return jsonify({"msg":"created"})

@app.route('/submit', methods=['POST'])
def submit():
    d=request.json
    cursor.execute("INSERT INTO submissions (assignment_id,student_id,grade) VALUES (%s,%s,NULL)",(d['assignment_id'],d['student_id']))
    db.commit()
    return jsonify({"msg":"submitted"})

@app.route('/grade', methods=['POST'])
def grade():
    d=request.json
    cursor.execute("UPDATE submissions SET grade=%s WHERE assignment_id=%s AND student_id=%s",(d['grade'],d['assignment_id'],d['student_id']))
    db.commit()
    return jsonify({"msg":"graded"})

# -------- REPORTS --------
@app.route('/reports/<name>')
def reports(name):
    cursor.execute(f"SELECT * FROM {name}")
    return jsonify(cursor.fetchall())

# -------- RUN --------
if __name__ == '__main__':
    app.run(debug=True)
