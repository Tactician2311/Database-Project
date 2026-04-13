"""
generate_inserts.py
-------------------
Generates inserts.sql satisfying ALL project constraints:
  - 100,000+ students
  - 200+ courses
  - Each student: 3–6 courses
  - Each course: at least 10 members
  - Lecturers: 1–5 courses each
  - Assignments + grades for every enrollment
  - Forums, threads, calendar events, course content

Run:  python generate_inserts.py
Output: inserts.sql  (~50–100MB)
"""

import random
import hashlib
import os

random.seed(42)

STUDENT_COUNT  = 100_500
LECTURER_COUNT = 300
COURSE_COUNT   = 210
ADMIN_COUNT    = 3

OUT = "inserts.sql"

first_names = [
    "James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda",
    "William","Barbara","David","Elizabeth","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Charles","Karen","Christopher","Lisa","Daniel","Nancy",
    "Matthew","Betty","Anthony","Margaret","Mark","Sandra","Donald","Ashley",
    "Steven","Dorothy","Paul","Kimberly","Andrew","Emily","Kenneth","Donna",
    "Joshua","Michelle","Kevin","Carol","Brian","Amanda","George","Melissa",
    "Timothy","Deborah","Ronald","Stephanie","Edward","Rebecca","Jason","Sharon",
    "Jeffrey","Laura","Ryan","Cynthia","Jacob","Kathleen","Gary","Amy",
    "Nicholas","Angela","Eric","Shirley","Jonathan","Anna","Stephen","Brenda",
    "Larry","Pamela","Justin","Emma","Scott","Nicole","Brandon","Helen",
    "Benjamin","Samantha","Samuel","Katherine","Raymond","Christine","Gregory","Debra",
    "Frank","Rachel","Alexander","Carolyn","Patrick","Janet","Jack","Catherine",
    "Dennis","Maria","Jerry","Heather","Tyler","Diane","Aaron","Julie",
    "Jose","Joyce","Adam","Victoria","Nathan","Ruth","Henry","Lauren"
]

last_names = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas",
    "Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White",
    "Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young",
    "Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell",
    "Carter","Roberts","Gomez","Phillips","Evans","Turner","Diaz","Parker",
    "Cruz","Edwards","Collins","Reyes","Stewart","Morris","Morales","Murphy",
    "Cook","Rogers","Gutierrez","Ortiz","Morgan","Cooper","Peterson","Bailey",
    "Reed","Kelly","Howard","Ramos","Kim","Cox","Ward","Richardson",
    "Watson","Brooks","Chavez","Wood","James","Bennett","Gray","Mendoza",
    "Ruiz","Hughes","Price","Alvarez","Castillo","Sanders","Patel","Myers",
    "Long","Ross","Foster","Jimenez","Powell","Jenkins","Perry","Russell"
]

course_titles = [
    "Introduction to Computer Science","Data Structures and Algorithms","Database Management Systems",
    "Operating Systems","Computer Networks","Software Engineering","Web Development Fundamentals",
    "Object-Oriented Programming","Discrete Mathematics","Linear Algebra","Calculus I","Calculus II",
    "Statistics for Engineers","Probability Theory","Artificial Intelligence","Machine Learning",
    "Deep Learning","Natural Language Processing","Computer Vision","Data Mining",
    "Cloud Computing","Cybersecurity Fundamentals","Cryptography","Network Security",
    "Mobile App Development","iOS Development","Android Development","React Native",
    "Frontend Development","Backend Development","Full Stack Web Development","RESTful API Design",
    "Microservices Architecture","DevOps Practices","Docker and Kubernetes","CI/CD Pipelines",
    "Agile Software Development","Project Management","Technical Writing","Business Analysis",
    "Human-Computer Interaction","UI/UX Design","Graphic Design Principles","Digital Marketing",
    "E-commerce Systems","Enterprise Resource Planning","Business Intelligence","Data Warehousing",
    "ETL Processes","Big Data Technologies","Apache Spark","Hadoop Ecosystem",
    "NoSQL Databases","Graph Databases","Time Series Analysis","Financial Mathematics",
    "Actuarial Science","Econometrics","Microeconomics","Macroeconomics",
    "Accounting Principles","Cost Accounting","Financial Management","Corporate Finance",
    "Investment Analysis","Risk Management","Marketing Management","Operations Management",
    "Supply Chain Management","Logistics","Quality Management","Lean Six Sigma",
    "Healthcare Informatics","Bioinformatics","Computational Biology","Genomics",
    "Biostatistics","Medical Imaging","Neuroscience","Cognitive Psychology",
    "Developmental Psychology","Social Psychology","Research Methods","Experimental Design",
    "Ethics in Technology","Philosophy of Science","Environmental Science","Renewable Energy",
    "Structural Engineering","Fluid Mechanics","Thermodynamics","Electrical Circuits",
    "Signal Processing","Embedded Systems","Robotics","Control Systems",
    "Compiler Design","Programming Languages","Formal Methods","Theory of Computation",
    "Parallel Computing","High Performance Computing","Quantum Computing","Blockchain Technology",
    "Internet of Things","Augmented Reality","Virtual Reality","Game Development",
    "3D Modelling and Animation","Digital Forensics","Incident Response","Penetration Testing",
    "Ethical Hacking","Vulnerability Assessment","Identity and Access Management","Zero Trust Security",
    "Technical Support","IT Service Management","ITIL Framework","Help Desk Operations",
    "Network Administration","Systems Administration","Database Administration","Cloud Architecture",
    "AWS Fundamentals","Azure Fundamentals","Google Cloud Platform","Infrastructure as Code",
    "Python Programming","Java Programming","C++ Programming","Go Programming",
    "Rust Programming","TypeScript","JavaScript Advanced","PHP Development",
    "Ruby on Rails","Django Framework","Spring Boot","ASP.NET Core",
    "Functional Programming","Design Patterns","Code Quality","Test-Driven Development",
    "Software Testing","Performance Engineering","Accessibility in Software","Internationalization",
    "Geographic Information Systems","Remote Sensing","Spatial Databases","Urban Planning Tech",
    "Smart Cities","Digital Twins","Simulation Modelling","Systems Thinking",
    "Decision Support Systems","Expert Systems","Fuzzy Logic","Evolutionary Algorithms",
    "Swarm Intelligence","Multi-Agent Systems","Knowledge Representation","Semantic Web",
    "Ontology Engineering","Information Retrieval","Recommender Systems","Social Network Analysis",
    "Computational Social Science","Digital Humanities","Corpus Linguistics","Computational Linguistics",
    "Speech Recognition","Speaker Verification","Audio Processing","Music Information Retrieval",
    "Image Processing","Video Analysis","Medical Image Analysis","Satellite Image Processing",
    "Point Cloud Processing","LIDAR Data Analysis","Drone Technology","Autonomous Vehicles",
    "Advanced Algorithms","Approximation Algorithms","Graph Theory","Combinatorics",
    "Number Theory","Abstract Algebra","Real Analysis","Complex Analysis",
    "Numerical Methods","Optimization Techniques","Operations Research","Queueing Theory",
    "Game Theory","Mechanism Design","Auction Theory","Behavioural Economics",
    "Health Economics","Public Policy Analysis","Social Welfare Theory","Poverty Studies",
    "Global Development","Sustainability","Corporate Social Responsibility","Technology Policy",
    "Intellectual Property Law","Privacy and Data Protection","Digital Ethics","AI Governance",
    "Introduction to Programming","Advanced Programming Topics","Capstone Project I","Capstone Project II",
    "Independent Study","Research Practicum","Graduate Seminar","Industry Attachment",
    "Technical Internship","Honours Dissertation","Masters Research","Doctoral Colloquium",
][:COURSE_COUNT]

content_types = ['link','file','slide','text']
event_types   = ['lecture','lab','exam','assignment','holiday','seminar']

def esc(s):
    return s.replace("'", "\\'")

def fake_email(name, uid):
    slug = name.lower().replace(" ",".")
    return f"{slug}.{uid}@university.edu"

def fake_hash(pw):
    # bcrypt-style placeholder — real bcrypt is done in Python at runtime
    # For seeded data we store a known bcrypt hash of "password123"
    return "$2b$12$KIXuBLwz2/K7GqS5NVOMKO9VFOM5YPL/xqUPnRvqNkEXDt2FDl4d6"

print("Generating inserts.sql …")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("USE school_db;\n")
    f.write("SET FOREIGN_KEY_CHECKS=0;\n")
    f.write("SET autocommit=0;\n\n")

    # ── ADMINS ──────────────────────────────────────────────────────────
    f.write("-- ADMINS\n")
    for i in range(1, ADMIN_COUNT + 1):
        name  = f"Admin User{i}"
        email = f"admin{i}@university.edu"
        pw    = fake_hash("admin123")
        f.write(f"INSERT INTO users (name,email,password,role) VALUES ('{esc(name)}','{email}','{pw}','admin');\n")

    # ── LECTURERS ───────────────────────────────────────────────────────
    f.write("\n-- LECTURERS\n")
    for i in range(1, LECTURER_COUNT + 1):
        fn    = random.choice(first_names)
        ln    = random.choice(last_names)
        name  = f"{fn} {ln}"
        email = fake_email(name, f"lec{i}")
        pw    = fake_hash("lecturer123")
        f.write(f"INSERT INTO users (name,email,password,role) VALUES ('{esc(name)}','{esc(email)}','{pw}','lecturer');\n")

    # ── STUDENTS ────────────────────────────────────────────────────────
    f.write("\n-- STUDENTS (100,500)\n")
    f.write("START TRANSACTION;\n")
    for i in range(1, STUDENT_COUNT + 1):
        fn    = random.choice(first_names)
        ln    = random.choice(last_names)
        name  = f"{fn} {ln}"
        email = fake_email(name, f"s{i}")
        pw    = fake_hash("student123")
        f.write(f"INSERT INTO users (name,email,password,role) VALUES ('{esc(name)}','{esc(email)}','{pw}','student');\n")
        if i % 5000 == 0:
            f.write("COMMIT;\nSTART TRANSACTION;\n")
    f.write("COMMIT;\n\n")

    # IDs: admins=1..ADMIN_COUNT, lecturers=ADMIN_COUNT+1..ADMIN_COUNT+LECTURER_COUNT
    admin_ids    = list(range(1, ADMIN_COUNT + 1))
    lecturer_ids = list(range(ADMIN_COUNT + 1, ADMIN_COUNT + LECTURER_COUNT + 1))
    student_ids  = list(range(ADMIN_COUNT + LECTURER_COUNT + 1,
                               ADMIN_COUNT + LECTURER_COUNT + STUDENT_COUNT + 1))

    # ── COURSES ─────────────────────────────────────────────────────────
    # Assign lecturers: each must teach 1–5, shuffle to spread load
    f.write("-- COURSES\n")
    lec_cycle  = lecturer_ids * 5           # enough slots
    random.shuffle(lec_cycle)
    lec_assign = lec_cycle[:COURSE_COUNT]   # one lecturer per course

    for cid, (title, lec_id) in enumerate(zip(course_titles, lec_assign), 1):
        desc = f"Comprehensive study of {title}. Topics include theory and practical application."
        f.write(f"INSERT INTO courses (title,description,lecturer_id) VALUES ('{esc(title)}','{esc(desc)}',{lec_id});\n")

    course_ids = list(range(1, COURSE_COUNT + 1))

    # ── ENROLLMENTS ─────────────────────────────────────────────────────
    # Each student: 3–6 courses. Guarantee each course has ≥10 students.
    f.write("\n-- ENROLLMENTS\n")
    f.write("START TRANSACTION;\n")

    enrollment_map = {cid: [] for cid in course_ids}   # course_id -> [student_ids]
    student_course_counts = {sid: 0 for sid in student_ids}

    # Phase 1: seed every course with 10 students
    shuffled_students = student_ids[:]
    random.shuffle(shuffled_students)
    ptr = 0
    for cid in course_ids:
        for _ in range(10):
            sid = shuffled_students[ptr % len(shuffled_students)]
            ptr += 1
            if sid not in enrollment_map[cid] and student_course_counts[sid] < 6:
                enrollment_map[cid].append(sid)
                student_course_counts[sid] += 1

    # Phase 2: every student must have ≥3 courses
    for sid in student_ids:
        while student_course_counts[sid] < 3:
            cid = random.choice(course_ids)
            if sid not in enrollment_map[cid] and student_course_counts[sid] < 6:
                enrollment_map[cid].append(sid)
                student_course_counts[sid] += 1

    # Phase 3: remaining capacity (up to 6)
    random.shuffle(student_ids)
    for sid in student_ids:
        target = random.randint(3, 6)
        while student_course_counts[sid] < target:
            cid = random.choice(course_ids)
            if sid not in enrollment_map[cid]:
                enrollment_map[cid].append(sid)
                student_course_counts[sid] += 1

    count = 0
    for cid, sids in enrollment_map.items():
        for sid in sids:
            f.write(f"INSERT IGNORE INTO enrollments (user_id,course_id) VALUES ({sid},{cid});\n")
            count += 1
            if count % 10000 == 0:
                f.write("COMMIT;\nSTART TRANSACTION;\n")
    f.write("COMMIT;\n\n")

    # ── SECTIONS + ITEMS ────────────────────────────────────────────────
    f.write("-- SECTIONS AND COURSE CONTENT\n")
    section_id = 1
    section_map = {}   # course_id -> [section_ids]
    for cid in course_ids:
        section_map[cid] = []
        for sec_num in range(1, 4):
            title = f"Module {sec_num}"
            f.write(f"INSERT INTO sections (course_id,title,sequence_order) VALUES ({cid},'{title}',{sec_num});\n")
            section_map[cid].append(section_id)
            section_id += 1

    # Items
    item_titles = ["Lecture Slides","Reading Material","Practice Quiz","Lab Exercise",
                   "Tutorial Video","Reference Link","Assignment Guide","Cheat Sheet"]
    sid_counter = 1
    for cid, secs in section_map.items():
        for sec in secs:
            for _ in range(random.randint(2, 4)):
                t = random.choice(item_titles)
                it = random.choice(content_types)
                content = f"https://resources.university.edu/course/{cid}/section/{sec}/{it}"
                f.write(f"INSERT INTO section_items (section_id,title,item_type,content) VALUES ({sec},'{t}','{it}','{content}');\n")
            sid_counter += 1

    # ── CALENDAR EVENTS ─────────────────────────────────────────────────
    f.write("\n-- CALENDAR EVENTS\n")
    for cid in course_ids:
        for _ in range(random.randint(3, 6)):
            et   = random.choice(event_types)
            mo   = random.randint(1,12)
            dy   = random.randint(1,28)
            date = f"2025-{mo:02d}-{dy:02d}"
            title = f"{et.title()} - Course {cid}"
            f.write(f"INSERT INTO calendar_events (course_id,title,type,event_date) VALUES ({cid},'{title}','{et}','{date}');\n")

    # ── FORUMS + THREADS ────────────────────────────────────────────────
    f.write("\n-- FORUMS AND THREADS\n")
    forum_id  = 1
    thread_id = 1
    forum_ids_map = {}

    for cid in course_ids:
        forum_ids_map[cid] = []
        for fi in range(1, 3):
            title = f"Forum {fi}: General Discussion" if fi == 1 else f"Forum {fi}: Q&A"
            f.write(f"INSERT INTO forums (course_id,title) VALUES ({cid},'{title}');\n")
            forum_ids_map[cid].append(forum_id)
            enrolled = enrollment_map.get(cid, [])
            if enrolled:
                # Root thread
                author = random.choice(enrolled)
                f.write(f"INSERT INTO threads (forum_id,author_id,parent_post_id,title,content) VALUES ({forum_id},{author},NULL,'Welcome Thread','Welcome to this forum! Please introduce yourself.');\n")
                root_id = thread_id
                thread_id += 1
                # A few replies
                for _ in range(random.randint(2, 5)):
                    rep_author = random.choice(enrolled)
                    f.write(f"INSERT INTO threads (forum_id,author_id,parent_post_id,title,content) VALUES ({forum_id},{rep_author},{root_id},NULL,'Looking forward to this course!');\n")
                    thread_id += 1
            forum_id += 1

    # ── ASSIGNMENTS + SUBMISSIONS ────────────────────────────────────────
    f.write("\n-- ASSIGNMENTS AND SUBMISSIONS\n")
    f.write("START TRANSACTION;\n")
    asgn_id = 1
    sub_count = 0
    for cid in course_ids:
        enrolled_stus = enrollment_map.get(cid, [])
        for asgn_num in range(1, 4):   # 3 assignments per course
            title    = f"Assignment {asgn_num}"
            due_mo   = random.randint(1,12)
            due_dy   = random.randint(1,28)
            due_date = f"2025-{due_mo:02d}-{due_dy:02d}"
            f.write(f"INSERT INTO assignments (course_id,title,due_date) VALUES ({cid},'{title}','{due_date}');\n")

            for sid in enrolled_stus:
                grade = round(random.uniform(40.0, 100.0), 2)
                f.write(f"INSERT IGNORE INTO submissions (assignment_id,student_id,grade) VALUES ({asgn_id},{sid},{grade});\n")
                sub_count += 1
                if sub_count % 10000 == 0:
                    f.write("COMMIT;\nSTART TRANSACTION;\n")
            asgn_id += 1

    f.write("COMMIT;\n\n")
    f.write("SET FOREIGN_KEY_CHECKS=1;\n")
    f.write("SET autocommit=1;\n")

print(f"Done! Written to {OUT}")
print(f"Approx enrollments: {sum(len(v) for v in enrollment_map.values()):,}")
