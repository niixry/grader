function esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function fmtDate(iso) {
    return iso ? new Date(iso).toLocaleString('ru-RU') : '';
}
function showError(id, msg) {
    const el = document.getElementById(id);
    el.textContent = msg;
    el.classList.remove('hidden');
}
function hideError(id) {
    document.getElementById(id).classList.add('hidden');
}

function showApp(email) {
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    document.getElementById('user-email').textContent = email;
}
function showAuth() {
    document.getElementById('app-screen').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
}

async function init() {
    try {
        const r = await fetch('/api/me');
        if (r.ok) {
            const d = await r.json();
            showApp(d.email);
        } else {
            showAuth();
        }
    } catch {
        showAuth();
    }
}

document.querySelectorAll('.auth-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.auth-tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tab = btn.dataset.auth;
        document.getElementById('login-panel').classList.toggle('hidden', tab !== 'login');
        document.getElementById('register-panel').classList.toggle('hidden', tab !== 'register');
        hideError('login-error');
        hideError('register-error');
    });
});

document.getElementById('login-btn').addEventListener('click', async () => {
    hideError('login-error');
    const email    = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const btn      = document.getElementById('login-btn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Входим...';

    try {
        const r = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password}),
        });
        const d = await r.json();
        if (d.error) { showError('login-error', d.error); return; }
        showApp(d.email);
    } catch {
        showError('login-error', 'Ошибка соединения с сервером');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Войти';
    }
});

document.getElementById('login-password').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('login-btn').click();
});

document.getElementById('register-btn').addEventListener('click', async () => {
    hideError('register-error');
    const email    = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const btn      = document.getElementById('register-btn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Создаём аккаунт...';

    try {
        const r = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password}),
        });
        const d = await r.json();
        if (d.error) { showError('register-error', d.error); return; }
        showApp(d.email);
    } catch {
        showError('register-error', 'Ошибка соединения с сервером');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Создать аккаунт';
    }
});

document.getElementById('logout-btn').addEventListener('click', async () => {
    await fetch('/api/logout', {method: 'POST'});
    showAuth();
});

function setupPreview(inputId, previewId) {
    const input   = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    input.addEventListener('change', () => {
        const file = input.files[0];
        if (!file) { preview.innerHTML = ''; preview.classList.add('hidden'); return; }
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = e => {
                preview.innerHTML = `<img src="${e.target.result}" alt="Предпросмотр">`;
                preview.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        } else if (file.name.toLowerCase().endsWith('.zip')) {
            preview.innerHTML = `<div style="padding:.6rem;color:#555">📦 ${esc(file.name)} (${(file.size/1024/1024).toFixed(1)} МБ)</div>`;
            preview.classList.remove('hidden');
        } else {
            preview.innerHTML = '';
            preview.classList.add('hidden');
        }
    });
}
setupPreview('t-image', 't-preview');

function renderCheckResult(containerId, data) {
    const el = document.getElementById(containerId);
    if (data.error) {
        el.innerHTML = `<div style="margin-top:1.4rem;background:#fff0f0;border-left:5px solid #ff8a8a;
            border-radius:1.2rem;padding:.75rem 1rem;color:#a03030">⚠️ ${esc(data.error)}</div>`;
        return;
    }
    const errHtml = data.errors && data.errors.length
        ? data.errors.map(e => `• ${esc(e)}`).join('<br>')
        : '— нет явных ошибок —';
    el.innerHTML = `
        <div class="result-card">
            <h3>Результат проверки</h3>
            <div class="score-badge">⭐ ${esc(String(data.score))} / 10</div>
            <div class="errors-list"><strong>Замечания:</strong><br>${errHtml}</div>
            <div class="comment-block"><strong>Комментарий:</strong><br>${esc(data.comment)}</div>
            ${data.saved ? '<div class="saved-notice">✅ Результат сохранён</div>' : ''}
        </div>`;
}

async function submitTeacherCheck() {
    const btn = document.getElementById('t-submit');

    const formData = new FormData();
    formData.append('task',         document.getElementById('t-task').value.trim());
    formData.append('criteria',     document.getElementById('t-criteria').value.trim());
    formData.append('save',         'true');
    formData.append('student_name', document.getElementById('t-name').value.trim());
    const imageFile = document.getElementById('t-image').files[0];
    if (imageFile) formData.append('image', imageFile);

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Анализирую...';
    document.getElementById('teacher-result').innerHTML = '';

    try {
        const r    = await fetch('/check', {method: 'POST', body: formData});
        const data = await r.json();
        renderCheckResult('teacher-result', data);
    } catch {
        document.getElementById('teacher-result').innerHTML =
            `<div style="margin-top:1.4rem;background:#fff0f0;border-left:5px solid #ff8a8a;
                border-radius:1.2rem;padding:.75rem 1rem;color:#a03030">
                ⚠️ Ошибка соединения с сервером</div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '✨ Проверить и сохранить';
        document.getElementById('t-image').value = '';
        const prev = document.getElementById('t-preview');
        prev.innerHTML = '';
        prev.classList.add('hidden');
    }
}

document.getElementById('teacher-form').addEventListener('submit', e => { e.preventDefault(); submitTeacherCheck(); });

async function loadGroups() {
    try {
        const r = await fetch('/groups');
        if (!r.ok) return;
        const groups = await r.json();
        const options = groups.map(g => `<option value="${g.id}">${esc(g.name)}</option>`).join('');

        const sel = document.getElementById('g-group-select');
        if (sel) sel.innerHTML = '<option value="">— без группы —</option>' + options;

        const filter = document.getElementById('r-group-filter');
        if (filter) filter.innerHTML = '<option value="">Все группы</option>' + options;
    } catch { /* игнорим */ }
}

async function loadResults() {
    const list = document.getElementById('results-list');
    list.innerHTML = '<p class="loading"><span class="spinner"></span> Загрузка...</p>';

    try {
        const groupId = document.getElementById('r-group-filter').value;
        const url     = groupId ? `/results?group_id=${groupId}` : '/results';
        const r    = await fetch(url);
        const data = await r.json();

        if (data.error) {
            list.innerHTML = `<p class="loading">⚠️ ${esc(data.error)}</p>`;
            return;
        }
        if (!data.length) {
            list.innerHTML = '<p class="loading">Пока нет сохранённых работ</p>';
            return;
        }

        list.innerHTML = '';
        data.forEach(res => {
            const card = document.createElement('div');
            card.className = 'result-item';
            const taskShort = res.task.length > 80 ? esc(res.task.slice(0,80)) + '…' : esc(res.task);
            card.innerHTML = `
                <button class="delete-btn" title="Удалить">🗑️</button>
                <h4>${esc(res.student_name)}</h4>
                <div class="meta"><span class="meta-score">Оценка: ${res.score}/10</span> · ${fmtDate(res.created_at)}</div>
                ${res.group_name ? '<div><strong>Группа:</strong> ' + esc(res.group_name) + '</div>' : ''}
                <div><strong>Задание:</strong> ${taskShort}</div>
                <div><strong>Комментарий:</strong> ${esc(res.comment)}</div>`;
            card.querySelector('.delete-btn').addEventListener('click', () => {
                if (confirm('Удалить запись?')) deleteResult(res.id, card);
            });
            list.appendChild(card);
        });
    } catch {
        list.innerHTML = '<p class="loading">⚠️ Ошибка соединения с сервером</p>';
    }
}

async function deleteResult(id, cardEl) {
    try {
        await fetch(`/results/${id}`, {method: 'DELETE'});
        cardEl.remove();
        if (!document.querySelector('.result-item'))
            document.getElementById('results-list').innerHTML =
                '<p class="loading">Пока нет сохранённых работ</p>';
    } catch {
        alert('Не удалось удалить запись');
    }
}

document.getElementById('btn-refresh').addEventListener('click', loadResults);
document.getElementById('r-group-filter').addEventListener('change', loadResults);

document.getElementById('g-group-new').addEventListener('click', async () => {
    const name = prompt('Название группы (например: Контрольная №3, 9А)');
    if (!name || !name.trim()) return;
    try {
        const r = await fetch('/groups', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: name.trim()}),
        });
        const d = await r.json();
        if (d.error) { alert(d.error); return; }
        await loadGroups();
        document.getElementById('g-group-select').value = d.id;
    } catch {
        alert('Ошибка соединения с сервером');
    }
});

const tabBtns     = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const id = btn.dataset.tab;
        tabContents.forEach(c => c.classList.remove('active'));
        document.getElementById(`${id}-tab`).classList.add('active');
        if (id === 'results') { loadGroups(); loadResults(); }
        if (id === 'group') loadGroups();
    });
});

let gCount = 0;

function addStudentRow() {
    gCount++;
    const n   = gCount;
    const row = document.createElement('div');
    row.className  = 'student-row';
    row.dataset.sid = n;
    row.innerHTML = `
        <button type="button" class="btn-remove" title="Удалить">×</button>
        <div class="form-group">
            <label>ФИО ученика</label>
            <input type="text" id="g-name-${n}" placeholder="Фамилия Имя" required>
        </div>
        <div class="form-group">
            <label>Фото работы или ZIP-архив (JPG/PNG, до 5 МБ; ZIP до 10 фото)</label>
            <label class="file-label" for="g-image-${n}">📁 Загрузить файл</label>
            <input type="file" id="g-image-${n}" accept="image/jpeg,image/png,application/zip,.zip" required>
            <div id="g-preview-${n}" class="preview hidden"></div>
        </div>`;
    row.querySelector('.btn-remove').addEventListener('click', () => row.remove());
    document.getElementById('g-students').appendChild(row);
    setupPreview(`g-image-${n}`, `g-preview-${n}`);
}

addStudentRow();

document.getElementById('g-add').addEventListener('click', addStudentRow);

document.getElementById('group-form').addEventListener('submit', async e => {
    e.preventDefault();
    const rows = document.querySelectorAll('.student-row');
    if (!rows.length) return;

    const task     = document.getElementById('g-task').value.trim();
    const criteria = document.getElementById('g-criteria').value.trim();
    const btn      = document.getElementById('g-submit');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Проверяю...';

    const container = document.getElementById('group-results');
    container.innerHTML = '';

    rows.forEach(row => {
        const n    = row.dataset.sid;
        const name = document.getElementById(`g-name-${n}`).value.trim() || 'Ученик';
        const card = document.createElement('div');
        card.id        = `g-result-${n}`;
        card.className = 'result-card';
        card.innerHTML = `<h3>${esc(name)}</h3><p class="loading"><span class="spinner"></span> Анализирую...</p>`;
        container.appendChild(card);
    });

    const promises = Array.from(rows).map(async row => {
        const n    = row.dataset.sid;
        const name = document.getElementById(`g-name-${n}`).value.trim();
        const file = document.getElementById(`g-image-${n}`).files[0];

        const fd = new FormData();
        fd.append('task',         task);
        fd.append('criteria',     criteria);
        fd.append('save',         'true');
        fd.append('student_name', name);
        fd.append('group_id',     document.getElementById('g-group-select').value);
        if (file) fd.append('image', file);

        try {
            const r    = await fetch('/check', { method: 'POST', body: fd });
            const data = await r.json();
            renderGroupResult(`g-result-${n}`, name, data);
        } catch {
            const card = document.getElementById(`g-result-${n}`);
            card.innerHTML = `<h3>${esc(name)}</h3>
                <div style="color:#a03030">⚠️ Ошибка соединения с сервером</div>`;
        }
    });

    await Promise.allSettled(promises);

    btn.disabled    = false;
    btn.textContent = 'Проверить всех';
});

function renderGroupResult(cardId, name, data) {
    const card = document.getElementById(cardId);
    if (data.error) {
        card.innerHTML = `<h3>${esc(name)}</h3>
            <div style="color:#a03030">⚠️ ${esc(data.error)}</div>`;
        return;
    }
    const errHtml = data.errors && data.errors.length
        ? data.errors.map(e => `• ${esc(e)}`).join('<br>')
        : '— нет явных ошибок —';
    card.innerHTML = `
        <h3>${esc(name)}</h3>
        <div class="score-badge">⭐ ${esc(String(data.score))} / 10</div>
        <div class="errors-list"><strong>Замечания:</strong><br>${errHtml}</div>
        <div class="comment-block"><strong>Комментарий:</strong><br>${esc(data.comment)}</div>
        ${data.saved ? '<div class="saved-notice">✅ Результат сохранён</div>' : ''}`;
}

init();
