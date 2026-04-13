const API_BASE = 'http://127.0.0.1:5000';

// ── State ──────────────────────────────────────
let token = localStorage.getItem('nexus_token');
let user = null;
let currentCourseId = null;

// ── DOM refs ────────────────────────────────────
const views = {
    auth: document.getElementById('auth-view'),
    dashboard: document.getElementById('dashboard-view')
};
const panels = {
    home: document.getElementById('home-panel'),
    courses: document.getElementById('courses-panel'),
    calendar: document.getElementById('calendar-panel'),
    courseDetail: document.getElementById('course-detail-panel')
};

// ── Toast ───────────────────────────────────────
function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    const icon = type === 'error' ? 'ri-error-warning-line'
        : type === 'warning' ? 'ri-alert-line'
            : 'ri-checkbox-circle-line';
    toast.innerHTML = `<i class="${icon}"></i> ${msg}`;
    toast.className = `toast show ${type}`;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { toast.className = 'toast hidden'; }, 3200);
}

// ── JWT helper ──────────────────────────────────
function parseJwt(token) {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(decodeURIComponent(atob(base64).split('').map(c =>
        '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    ).join('')));
}

// ── API helper ──────────────────────────────────
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = token;
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        showToast('Error: ' + err.message, 'error');
        return null;
    }
}

// ── Dark mode ───────────────────────────────────
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('monavle_theme', theme);
    const isDark = theme === 'dark';
    ['auth-theme-icon', 'dash-theme-icon'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = isDark ? 'ri-sun-line' : 'ri-moon-line';
    });
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
}

// Apply saved theme immediately
applyTheme(localStorage.getItem('monavle_theme') || 'light');

document.getElementById('auth-theme-toggle').addEventListener('click', toggleTheme);
document.getElementById('dash-theme-toggle').addEventListener('click', toggleTheme);

// ── Mobile sidebar ──────────────────────────────
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebar-overlay');

document.getElementById('mobile-menu-btn').addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sidebarOverlay.classList.toggle('show');
});
sidebarOverlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('show');
});

// ── Auth: toggle login / register ───────────────
let isLoginMode = true;

function switchAuthMode() {
    isLoginMode = !isLoginMode;
    document.getElementById('register-fields').classList.toggle('hidden', isLoginMode);
    document.getElementById('auth-title').innerText = isLoginMode ? 'Welcome Back' : 'Create Account';
    document.getElementById('auth-subtitle').innerText = isLoginMode ? 'Sign in to your MONAvle account' : 'Join your institution today';
    document.getElementById('auth-submit-btn').innerHTML = isLoginMode
        ? '<i class="ri-login-box-line"></i> Sign In'
        : '<i class="ri-user-add-line"></i> Sign Up';
    document.getElementById('toggle-auth-text').innerText = isLoginMode
        ? "Don't have an account? "
        : 'Already have an account? ';
    const link = document.createElement('a');
    link.href = '#';
    link.id = 'toggle-auth';
    link.innerText = isLoginMode ? 'Sign Up' : 'Sign In';
    link.addEventListener('click', (e) => { e.preventDefault(); switchAuthMode(); });
    document.getElementById('toggle-auth-text').appendChild(link);
}

// Attach initial listener
document.getElementById('toggle-auth').addEventListener('click', (e) => {
    e.preventDefault();
    switchAuthMode();
});

document.getElementById('auth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('auth-submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="ri-loader-4-line"></i> Please wait…';

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();

    if (isLoginMode) {
        const res = await apiCall('/login', 'POST', { email, password });
        if (res && res.token) {
            token = res.token;
            localStorage.setItem('nexus_token', token);
            initApp();
        } else if (res) {
            showToast('Invalid credentials', 'error');
        }
    } else {
        const name = document.getElementById('name').value;
        const role = document.getElementById('role').value;
        const res = await apiCall('/register', 'POST', { name, email, password, role });
        if (res && res.msg) {
            showToast('Registration successful! Please sign in.');
            if (!isLoginMode) switchAuthMode();
        }
    }

    btn.disabled = false;
    btn.innerHTML = isLoginMode
        ? '<i class="ri-login-box-line"></i> Sign In'
        : '<i class="ri-user-add-line"></i> Sign Up';
});

document.getElementById('logout-btn').addEventListener('click', () => {
    token = null; user = null;
    localStorage.removeItem('nexus_token');
    switchView('auth');
});

// ── Navigation ──────────────────────────────────
function switchView(viewName) {
    Object.values(views).forEach(el => el.classList.remove('active-view'));
    views[viewName].classList.add('active-view');
}

function switchPanel(panelId) {
    Object.values(panels).forEach(el => el.classList.remove('active-panel'));
    // Map panel key → element ID
    const map = {
        'home-panel': panels.home,
        'courses-panel': panels.courses,
        'calendar-panel': panels.calendar,
        'course-detail-panel': panels.courseDetail
    };
    const target = map[panelId] || document.getElementById(panelId);
    if (target) target.classList.add('active-panel');

    document.querySelectorAll('.nav-link').forEach(nav => {
        nav.classList.toggle('active', nav.dataset.target === panelId);
    });

    // Close mobile sidebar
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('show');
}

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = e.currentTarget.dataset.target;
        switchPanel(target);
        const label = e.currentTarget.querySelector('i').nextSibling.textContent.trim();
        document.getElementById('current-page-title').innerHTML = `<strong>${label}</strong>`;
        if (target === 'courses-panel') loadCourses();
        if (target === 'calendar-panel') loadEvents();
    });
});

document.querySelector('.back-to-courses').addEventListener('click', () => {
    switchPanel('courses-panel');
    document.getElementById('current-page-title').innerHTML = '<strong>Courses</strong>';
});

// Course tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const tab = e.currentTarget.dataset.tab;
        document.getElementById(`tab-${tab}`).classList.add('active');
        loadCourseDetailData(tab);
    });
});

// ── Initialisation ──────────────────────────────
function initApp() {
    if (token) {
        user = parseJwt(token);

        // Update display
        document.getElementById('display-name').innerText = `User #${user.id}`;
        document.getElementById('display-role').innerText = user.role;
        document.getElementById('display-role').className = `badge ${user.role}`;

        // Avatar initial
        const avatarEl = document.getElementById('avatar-initials');
        avatarEl.innerHTML = `<span style="font-weight:700;font-family:'Roboto Mono',monospace">${String(user.id).slice(0, 2)}</span>`;

        // Topbar welcome day
        const dayEl = document.getElementById('welcome-day');
        if (dayEl) dayEl.textContent = new Date().toLocaleDateString('en-US', { weekday: 'long' });

        // Role-based button visibility
        document.getElementById('btn-create-course').classList.toggle('hidden', user.role !== 'admin');
        document.getElementById('btn-enroll-course').classList.toggle('hidden', user.role !== 'student');
        document.getElementById('btn-add-section').classList.toggle('hidden', user.role !== 'admin' && user.role !== 'lecturer');
        document.getElementById('btn-add-forum').classList.toggle('hidden', user.role === 'student');
        document.getElementById('btn-add-assignment').classList.toggle('hidden', user.role !== 'admin' && user.role !== 'lecturer');
        document.getElementById('btn-add-event').classList.toggle('hidden', user.role !== 'admin' && user.role !== 'lecturer');

        switchView('dashboard');
        switchPanel('home-panel');
        loadDashboardStats();
    } else {
        switchView('auth');
    }
}

// ── Dashboard stats ─────────────────────────────
async function loadDashboardStats() {
    const statsDiv = document.getElementById('dashboard-stats');
    statsDiv.innerHTML = `<div class="stat-card glass-card"><div class="stat-icon"><i class="ri-loader-4-line"></i></div><div class="stat-info"><p>Loading…</p></div></div>`;

    const courses = await fetchCoursesList();
    const count = courses ? courses.length : 0;

    statsDiv.innerHTML = `
    <div class="stat-card glass-card">
      <div class="stat-icon"><i class="ri-book-read-line"></i></div>
      <div class="stat-info"><h3>${count}</h3><p>Active Courses</p></div>
    </div>
    <div class="stat-card glass-card">
      <div class="stat-icon" style="background:var(--success-bg);color:var(--success)"><i class="ri-user-star-line"></i></div>
      <div class="stat-info"><h3>${user.role.charAt(0).toUpperCase() + user.role.slice(1)}</h3><p>Your Role</p></div>
    </div>
    <div class="stat-card glass-card">
      <div class="stat-icon" style="background:var(--gold-subtle);color:var(--gold)"><i class="ri-calendar-check-line"></i></div>
      <div class="stat-info">
        <h3>${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</h3>
        <p>Today's Date</p>
      </div>
    </div>
  `;
}

// ── Courses ─────────────────────────────────────
async function fetchCoursesList() {
    let endpoint = '/courses';
    if (user.role === 'student') endpoint = `/courses/student/${user.id}`;
    if (user.role === 'lecturer') endpoint = `/courses/lecturer/${user.id}`;
    return await apiCall(endpoint);
}

async function loadCourses() {
    const container = document.getElementById('courses-list');
    container.innerHTML = `<p class="text-muted">Loading courses…</p>`;
    const courses = await fetchCoursesList();

    if (!courses || courses.length === 0) {
        container.innerHTML = `
      <div class="empty-state">
        <i class="ri-book-open-line"></i>
        <p>No courses found.</p>
      </div>`;
        return;
    }

    const gradients = [
        'linear-gradient(135deg,#fca5a5,#ef4444)',
        'linear-gradient(135deg,#a78bfa,#8b5cf6)',
        'linear-gradient(135deg,#86efac,#10b981)',
        'linear-gradient(135deg,#fcd34d,#f59e0b)',
        'linear-gradient(135deg,#93c5fd,#3b82f6)',
        'linear-gradient(135deg,#fbcfe8,#ec4899)',
        'linear-gradient(135deg,#c4b5fd,#7c3aed)',
        'linear-gradient(135deg,#6ee7b7,#059669)',
    ];
    const icons = ['ri-quill-pen-line', 'ri-macbook-line', 'ri-microscope-line', 'ri-pie-chart-line', 'ri-palette-line', 'ri-global-line', 'ri-book-3-line', 'ri-flask-line'];

    container.innerHTML = courses.map(c => {
        const bg = gradients[c.course_id % gradients.length];
        const icon = icons[c.course_id % icons.length];
        const safeTitle = c.title.replace(/'/g, "\\'").replace(/"/g, '&quot;');
        return `
      <div class="course-card glass-card" onclick="openCourse(${c.course_id},'${safeTitle}')">
        <div class="course-card-banner" style="background:${bg}">
          <i class="${icon}"></i>
        </div>
        <div class="course-card-body">
          <span class="course-tag">ID ${c.course_id}</span>
          <h3 style="margin-top:0.6rem">${c.title}</h3>
          <p>${c.description || 'No description provided.'}</p>
          <div class="course-card-footer">
            <span><i class="ri-user-star-line"></i> Instructor ${c.lecturer_id}</span>
            <span><i class="ri-arrow-right-s-line"></i> Open</span>
          </div>
        </div>
      </div>`;
    }).join('');
}

function openCourse(id, title) {
    currentCourseId = id;
    document.getElementById('detail-course-title').innerText = title;
    document.getElementById('current-page-title').innerHTML = `<strong>${title}</strong>`;
    switchPanel('course-detail-panel');
    document.querySelector('.tab-btn[data-tab="content"]').click();
}

// ── Course detail data ──────────────────────────
async function loadCourseDetailData(tab) {
    if (tab === 'content') {
        const sections = await apiCall(`/sections/${currentCourseId}`);
        const container = document.getElementById('course-sections');

        if (!sections || sections.length === 0) {
            container.innerHTML = `<div class="empty-state"><i class="ri-layout-line"></i><p>No sections added yet.</p></div>`;
            return;
        }

        container.innerHTML = '';
        for (const s of sections) {
            const items = await apiCall(`/items/${s.section_id}`);
            const itemsHtml = items && items.length
                ? items.map(i => `
            <div class="list-item">
              <h4>${i.title}</h4>
              <p class="text-secondary text-sm mt-2">${i.content}</p>
            </div>`).join('')
                : `<p class="text-muted text-sm">No items in this section.</p>`;

            const addBtn = (user.role === 'admin' || user.role === 'lecturer')
                ? `<button class="btn btn-ghost btn-sm" onclick="showAddItemModal(${s.section_id})"><i class="ri-add-line"></i> Add Item</button>`
                : '';

            container.innerHTML += `
        <div class="section-item">
          <div class="section-header">
            <h4><i class="ri-folder-3-line" style="color:var(--accent);margin-right:0.5rem"></i>${s.title}</h4>
            ${addBtn}
          </div>
          <div class="section-body">${itemsHtml}</div>
        </div>`;
        }

    } else if (tab === 'forums') {
        const forums = await apiCall(`/forums/${currentCourseId}`);
        const container = document.getElementById('course-forums');
        if (!forums || forums.length === 0) {
            container.innerHTML = `<div class="empty-state"><i class="ri-discuss-line"></i><p>No forums yet.</p></div>`;
            return;
        }
        container.innerHTML = forums.map(f => `
      <div class="list-item">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h4><i class="ri-discuss-line" style="color:var(--accent);margin-right:0.5rem"></i>${f.title}</h4>
          <button class="btn btn-outline btn-sm" onclick="viewThreads(${f.forum_id})">
            <i class="ri-chat-3-line"></i> Threads
          </button>
        </div>
        <div id="threads-container-${f.forum_id}" class="mt-3 pl-3" style="border-left:2px solid var(--bg-glass-border);display:none;"></div>
      </div>`).join('');

    } else if (tab === 'assignments') {
        const assignments = await apiCall(`/reports/assignments`);
        const container = document.getElementById('course-assignments');
        if (!assignments || assignments.length === 0) {
            container.innerHTML = `<div class="empty-state"><i class="ri-task-line"></i><p>No assignments yet.</p></div>`;
            return;
        }
        const courseAssignments = assignments.filter(a => a.course_id == currentCourseId);
        if (!courseAssignments.length) {
            container.innerHTML = `<div class="empty-state"><i class="ri-task-line"></i><p>No assignments for this course.</p></div>`;
            return;
        }
        container.innerHTML = courseAssignments.map(a => {
            const action = user.role === 'student'
                ? `<button class="btn btn-primary btn-sm mt-2" onclick="showSubmitModal(${a.assignment_id})"><i class="ri-send-plane-line"></i> Submit</button>`
                : `<button class="btn btn-secondary btn-sm mt-2" onclick="showGradeModal(${a.assignment_id})"><i class="ri-pencil-line"></i> Grade</button>`;
            return `
        <div class="list-item">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem">
            <div>
              <h4>${a.title}</h4>
              <p class="text-muted text-sm">Assignment #${a.assignment_id}</p>
            </div>
            ${action}
          </div>
        </div>`;
        }).join('');

    } else if (tab === 'members') {
        const members = await apiCall(`/members/${currentCourseId}`);
        const container = document.getElementById('course-members');
        if (!members || members.length === 0) {
            container.innerHTML = `<div class="empty-state"><i class="ri-group-line"></i><p>No members found.</p></div>`;
            return;
        }
        container.innerHTML = members.map(m => `
      <div class="list-item" style="display:flex;align-items:center;gap:1rem">
        <div class="avatar" style="width:38px;height:38px;font-size:0.85rem;font-family:'Roboto Mono',monospace">
          ${m.name.charAt(0).toUpperCase()}
        </div>
        <div style="flex:1;min-width:0">
          <strong>${m.name}</strong>
          <span class="badge ${m.role}" style="margin-left:0.5rem">${m.role}</span>
          <div class="text-muted text-sm">${m.email}</div>
        </div>
      </div>`).join('');
    }
}

// ── Forum threads ───────────────────────────────
async function viewThreads(forum_id) {
    const container = document.getElementById(`threads-container-${forum_id}`);
    if (container.style.display === 'block') { container.style.display = 'none'; return; }
    container.style.display = 'block';
    container.innerHTML = `<p class="text-muted text-sm">Loading…</p>`;

    const threads = await apiCall(`/threads/${forum_id}`);
    let html = threads && threads.length
        ? threads.map(t => `
        <div style="background:var(--bg-surface-2);border:1px solid var(--bg-glass-border);border-radius:var(--r-sm);padding:0.75rem;margin-bottom:0.5rem;font-size:0.87rem">
          <span style="color:var(--text-muted);font-size:0.75rem;margin-bottom:0.3rem;display:block">Author #${t.author_id}</span>
          ${t.content}
        </div>`).join('')
        : `<p class="text-muted text-sm">No threads yet.</p>`;

    html += `
    <div class="mt-3" style="display:flex;gap:0.5rem">
      <input type="text" id="new-thread-${forum_id}" class="form-input" style="padding:0.45rem 0.75rem;font-size:0.85rem" placeholder="Write a reply…">
      <button class="btn btn-primary btn-sm" onclick="postThread(${forum_id})"><i class="ri-send-plane-line"></i></button>
    </div>`;

    container.innerHTML = html;
}

async function postThread(forum_id) {
    const content = document.getElementById(`new-thread-${forum_id}`).value.trim();
    if (!content) return;
    await apiCall('/threads', 'POST', { forum_id, author_id: user.id, content });
    viewThreads(forum_id);
    showToast('Thread posted');
}

// ── Events ──────────────────────────────────────
async function loadEvents() {
    const dateInput = document.getElementById('event-date-filter').value;
    const container = document.getElementById('events-list');
    container.innerHTML = `<p class="text-muted">Loading events…</p>`;

    let endpoint = `/events/student?user_id=${user.id}`;
    if (dateInput) endpoint += `&date=${dateInput}`;

    const events = await apiCall(endpoint);
    if (!events || events.length === 0) {
        container.innerHTML = `<div class="empty-state"><i class="ri-calendar-line"></i><p>No events found.</p></div>`;
        return;
    }

    container.innerHTML = events.map(e => {
        const d = new Date(e.event_date);
        const day = d.getDate();
        const month = d.toLocaleDateString('en-US', { month: 'short' });
        return `
      <div class="event-item">
        <div class="event-date-badge">
          <div class="day">${day}</div>
          <div class="month">${month}</div>
        </div>
        <div class="event-info">
          <h4>${e.title}</h4>
          <p>${d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <span class="event-type-badge ${e.type}">${e.type}</span>
      </div>`;
    }).join('');
}

// ── Submission / Grade ──────────────────────────
function showSubmitModal(assignment_id) {
    openModal('Submit Assignment', `
    <input type="hidden" id="sub-aid" value="${assignment_id}">
    <div style="text-align:center;padding:1rem 0">
      <i class="ri-send-plane-2-line" style="font-size:2.5rem;color:var(--accent);display:block;margin-bottom:1rem"></i>
      <p>Confirm submission for assignment <strong>#${assignment_id}</strong>?</p>
    </div>
    <button class="btn btn-primary btn-block mt-3" onclick="submitAssignmentWork()">
      <i class="ri-check-line"></i> Confirm Submission
    </button>
  `);
}

async function submitAssignmentWork() {
    const assignment_id = document.getElementById('sub-aid').value;
    await apiCall('/submit', 'POST', { assignment_id, student_id: user.id });
    showToast('Assignment submitted successfully');
    modal.classList.add('hidden');
}

function showGradeModal(assignment_id) {
    openModal('Grade Submission', `
    <input type="hidden" id="gr-aid" value="${assignment_id}">
    <div class="input-group"><label>Student ID</label><input type="number" id="gr-sid" placeholder="e.g. 42"></div>
    <div class="input-group"><label>Grade (0–100)</label><input type="number" id="gr-grade" min="0" max="100" placeholder="85"></div>
    <button class="btn btn-primary btn-block" onclick="submitGrade()"><i class="ri-check-line"></i> Submit Grade</button>
  `);
}

async function submitGrade() {
    const assignment_id = document.getElementById('gr-aid').value;
    const student_id = document.getElementById('gr-sid').value;
    const grade = document.getElementById('gr-grade').value;
    await apiCall('/grade', 'POST', { assignment_id, student_id, grade });
    showToast('Grade submitted');
    modal.classList.add('hidden');
}

// ── Modal ───────────────────────────────────────
const modal = document.getElementById('modal-container');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');

document.getElementById('close-modal').addEventListener('click', () => {
    modal.classList.add('hidden');
});
modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.add('hidden');
});

function openModal(title, html) {
    modalTitle.innerText = title;
    modalBody.innerHTML = html;
    modal.classList.remove('hidden');
}

// ── Course actions ──────────────────────────────
document.getElementById('btn-create-course').addEventListener('click', () => {
    openModal('Create New Course', `
    <div class="input-group"><label>Course Title</label><input type="text" id="c-title" placeholder="e.g. Introduction to Biology"></div>
    <div class="input-group"><label>Description</label><input type="text" id="c-desc" placeholder="Short course description"></div>
    <div class="input-group"><label>Lecturer ID</label><input type="number" id="c-lect" placeholder="e.g. 12"></div>
    <button class="btn btn-primary btn-block" onclick="submitCourse()"><i class="ri-add-line"></i> Create Course</button>
  `);
});

async function submitCourse() {
    const title = document.getElementById('c-title').value;
    const description = document.getElementById('c-desc').value;
    const lecturer_id = document.getElementById('c-lect').value;
    const res = await apiCall('/courses', 'POST', { title, description, lecturer_id });
    if (res) { showToast('Course created'); modal.classList.add('hidden'); loadCourses(); }
}

document.getElementById('btn-enroll-course').addEventListener('click', () => {
    openModal('Enroll in Course', `
    <div class="input-group"><label>Course ID</label><input type="number" id="e-cid" placeholder="e.g. 5"></div>
    <button class="btn btn-primary btn-block" onclick="submitEnroll()"><i class="ri-user-add-line"></i> Enroll</button>
  `);
});

async function submitEnroll() {
    const course_id = document.getElementById('e-cid').value;
    const res = await apiCall('/enroll', 'POST', { user_id: user.id, course_id });
    if (res) { showToast('Enrolled successfully'); modal.classList.add('hidden'); loadCourses(); }
}

document.getElementById('btn-add-section').addEventListener('click', () => {
    openModal('Add Section', `
    <div class="input-group"><label>Section Title</label><input type="text" id="s-title" placeholder="e.g. Week 1 — Introduction"></div>
    <div class="input-group"><label>Order</label><input type="number" id="s-order" value="1"></div>
    <button class="btn btn-primary btn-block" onclick="submitSection()"><i class="ri-add-line"></i> Add Section</button>
  `);
});

async function submitSection() {
    const title = document.getElementById('s-title').value;
    const order = document.getElementById('s-order').value;
    await apiCall('/sections', 'POST', { course_id: currentCourseId, title, order });
    showToast('Section added'); modal.classList.add('hidden');
    loadCourseDetailData('content');
}

function showAddItemModal(section_id) {
    openModal('Add Item to Section', `
    <input type="hidden" id="i-sid" value="${section_id}">
    <div class="input-group"><label>Title</label><input type="text" id="i-title" placeholder="e.g. Lecture Slides"></div>
    <div class="input-group"><label>Content / URL</label><input type="text" id="i-content" placeholder="e.g. https://…"></div>
    <button class="btn btn-primary btn-block" onclick="submitItem()"><i class="ri-save-line"></i> Save Item</button>
  `);
}

async function submitItem() {
    const section_id = document.getElementById('i-sid').value;
    const title = document.getElementById('i-title').value;
    const content = document.getElementById('i-content').value;
    await apiCall('/items', 'POST', { section_id, title, content });
    showToast('Item added'); modal.classList.add('hidden');
    loadCourseDetailData('content');
}

document.getElementById('btn-add-forum').addEventListener('click', () => {
    openModal('Create Forum', `
    <div class="input-group"><label>Forum Title</label><input type="text" id="f-title" placeholder="e.g. General Discussion"></div>
    <button class="btn btn-primary btn-block" onclick="submitForum()"><i class="ri-add-line"></i> Create Forum</button>
  `);
});

async function submitForum() {
    const title = document.getElementById('f-title').value;
    await apiCall('/forums', 'POST', { course_id: currentCourseId, title });
    showToast('Forum created'); modal.classList.add('hidden');
    loadCourseDetailData('forums');
}

document.getElementById('btn-add-assignment').addEventListener('click', () => {
    openModal('Add Assignment', `
    <div class="input-group"><label>Assignment Title</label><input type="text" id="a-title" placeholder="e.g. Essay — Week 3"></div>
    <button class="btn btn-primary btn-block" onclick="submitAssignment()"><i class="ri-add-line"></i> Create Assignment</button>
  `);
});

async function submitAssignment() {
    const title = document.getElementById('a-title').value;
    await apiCall('/assignments', 'POST', { course_id: currentCourseId, title });
    showToast('Assignment posted'); modal.classList.add('hidden');
    loadCourseDetailData('assignments');
}

document.getElementById('btn-add-event').addEventListener('click', () => {
    openModal('Add Event', `
    <div class="input-group"><label>Course ID</label><input type="number" id="ev-cid" value="${currentCourseId || ''}"></div>
    <div class="input-group"><label>Title</label><input type="text" id="ev-title" placeholder="e.g. Midterm Exam"></div>
    <div class="input-group">
      <label>Type</label>
      <select id="ev-type">
        <option value="lecture">Lecture</option>
        <option value="exam">Exam</option>
        <option value="deadline">Deadline</option>
      </select>
    </div>
    <div class="input-group"><label>Date</label><input type="date" id="ev-date"></div>
    <button class="btn btn-primary btn-block" onclick="submitEvent()"><i class="ri-calendar-check-line"></i> Add Event</button>
  `);
});

async function submitEvent() {
    const course_id = document.getElementById('ev-cid').value;
    const title = document.getElementById('ev-title').value;
    const type = document.getElementById('ev-type').value;
    const event_date = document.getElementById('ev-date').value;
    await apiCall('/events', 'POST', { course_id, title, type, event_date });
    showToast('Event added'); modal.classList.add('hidden');
    if (document.getElementById('calendar-panel').classList.contains('active-panel')) loadEvents();
}

document.getElementById('btn-load-events').addEventListener('click', loadEvents);

// ── Boot ────────────────────────────────────────
initApp();