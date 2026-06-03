// app.js
lucide.createIcons();

const authState = {
  token: localStorage.getItem('rowrocket_token') || '',
  user: null
};
const ANON_TRIAL_KEY = 'rowrocket_anonymous_trial_used';
const THEME_KEY = 'rowrocket_theme';
const emailPattern = /^[A-Za-z][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

function authHeaders(extra = {}) {
  return authState.token ? { ...extra, Authorization: `Bearer ${authState.token}` } : extra;
}

async function authFetch(url, options = {}) {
  const headers = authHeaders(options.headers || {});
  return fetch(url, { ...options, headers });
}

function openAuth(tab = 'signin') {
  document.getElementById('authGate').classList.add('open');
  switchAuthTab(tab);
}

function hasUsedAnonymousTrial() {
  return localStorage.getItem(ANON_TRIAL_KEY) === '1';
}

function markAnonymousTrialUsed() {
  localStorage.setItem(ANON_TRIAL_KEY, '1');
}

function showValidationAlert(message) {
  alert(message);
  showToast(message, 'error');
}

function isValidEmail(email) {
  return emailPattern.test((email || '').trim());
}

function isStrongPassword(password) {
  return passwordPattern.test(password || '');
}

function closeAuth() {
  document.getElementById('authGate').classList.remove('open');
}

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab').forEach(btn => btn.classList.toggle('active', btn.dataset.authTab === tab));
  document.getElementById('signinForm').classList.toggle('active', tab === 'signin');
  document.getElementById('signupForm').classList.toggle('active', tab === 'signup');
  document.getElementById('forgotForm').classList.toggle('active', tab === 'forgot');
}

function setAuth(token, user) {
  authState.token = token;
  authState.user = user;
  localStorage.setItem('rowrocket_token', token);
  if (user.theme_preference) applyTheme(user.theme_preference, { persistRemote: false });
  renderAuthUi();
}

function clearAuth() {
  authState.token = '';
  authState.user = null;
  localStorage.removeItem('rowrocket_token');
  renderAuthUi();
}

function renderAuthUi() {
  const signedIn = Boolean(authState.user);
  document.getElementById('signinOpenBtn').style.display = signedIn ? 'none' : 'inline-flex';
  document.getElementById('signupOpenBtn').style.display = signedIn ? 'none' : 'inline-flex';
  document.getElementById('profileOpenBtn').style.display = signedIn ? 'inline-flex' : 'none';
  document.getElementById('mobileSigninBtn').style.display = signedIn ? 'none' : 'inline-flex';
  document.getElementById('mobileSignupBtn').style.display = signedIn ? 'none' : 'inline-flex';
  document.getElementById('mobileProfileBtn').style.display = signedIn ? 'inline-flex' : 'none';
  if (!signedIn) return;

  document.getElementById('profileChipName').textContent = authState.user.name;
  document.getElementById('profileName').textContent = authState.user.name;
  document.getElementById('profileEmail').textContent = authState.user.email;
  const remaining = Math.max(0, authState.user.free_unverified_uses - authState.user.unverified_uses);
  document.getElementById('verifyStatus').textContent = authState.user.email_verified
    ? 'Email verified. Your account is fully active.'
    : `Email not verified. ${remaining} unverified extraction${remaining === 1 ? '' : 's'} remaining.`;
  document.getElementById('settingsThemeLabel').textContent = `Current theme: ${getCurrentTheme() === 'light' ? 'Light' : 'Dark'}`;
  lucide.createIcons();
}

function getCurrentTheme() {
  return document.documentElement.dataset.theme || localStorage.getItem(THEME_KEY) || 'dark';
}

async function saveThemePreference(theme) {
  if (!authState.token || !authState.user) return;
  try {
    const res = await authFetch('/api/auth/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme_preference: theme })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    authState.user = data.user;
    renderAuthUi();
  } catch (err) {
    showToast(err.message || 'Could not save theme preference.', 'error');
  }
}

function applyTheme(theme, options = {}) {
  const persistRemote = options.persistRemote !== false;
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
  document.querySelectorAll('#themeToggle i, #mobileThemeToggle i, #settingsThemeToggle i').forEach(icon => {
    icon.setAttribute('data-lucide', theme === 'light' ? 'moon' : 'sun');
  });
  const label = document.getElementById('settingsThemeLabel');
  if (label) label.textContent = `Current theme: ${theme === 'light' ? 'Light' : 'Dark'}`;
  lucide.createIcons();
  if (persistRemote) saveThemePreference(theme);
}

function toggleTheme() {
  const nextTheme = getCurrentTheme() === 'light' ? 'dark' : 'light';
  applyTheme(nextTheme);
}

async function refreshMe() {
  if (!authState.token) {
    renderAuthUi();
    return;
  }
  try {
    const res = await authFetch('/api/auth/me');
    if (!res.ok) throw new Error('Session expired');
    const data = await res.json();
    authState.user = data.user;
    if (data.user.theme_preference) applyTheme(data.user.theme_preference, { persistRemote: false });
    renderAuthUi();
  } catch {
    clearAuth();
  }
}

async function loadAuthHistory() {
  if (!authState.token) return;
  const res = await authFetch('/api/auth/history');
  const data = await res.json();
  const history = data.history || [];
  document.getElementById('authHistory').innerHTML = history.length ? history.map(item => `
    <div class="history-item">
      <strong>${item.action.replaceAll('_', ' ')}</strong>
      <span>${new Date(item.at).toLocaleString()} · ${item.ip}</span>
    </div>
  `).join('') : '<p class="profile-email">No history yet.</p>';
}

document.querySelectorAll('.auth-tab').forEach(btn => btn.addEventListener('click', () => switchAuthTab(btn.dataset.authTab)));
document.getElementById('signinOpenBtn').addEventListener('click', () => openAuth('signin'));
document.getElementById('signupOpenBtn').addEventListener('click', () => openAuth('signup'));
document.getElementById('mobileSigninBtn').addEventListener('click', () => openAuth('signin'));
document.getElementById('mobileSignupBtn').addEventListener('click', () => openAuth('signup'));
document.getElementById('authClose').addEventListener('click', closeAuth);
document.getElementById('forgotPasswordBtn').addEventListener('click', () => switchAuthTab('forgot'));
document.getElementById('createAccountFirstBtn').addEventListener('click', () => switchAuthTab('signup'));
document.getElementById('alreadyHaveAccountBtn').addEventListener('click', () => switchAuthTab('signin'));
document.getElementById('backToSigninBtn').addEventListener('click', () => switchAuthTab('signin'));
document.getElementById('themeToggle').addEventListener('click', toggleTheme);
document.getElementById('mobileThemeToggle').addEventListener('click', toggleTheme);
document.getElementById('settingsThemeToggle').addEventListener('click', toggleTheme);
document.getElementById('profileOpenBtn').addEventListener('click', async () => {
  document.getElementById('profilePanel').classList.add('open');
  await loadAuthHistory();
});
document.getElementById('mobileProfileBtn').addEventListener('click', async () => {
  document.getElementById('profilePanel').classList.add('open');
  await loadAuthHistory();
});
document.getElementById('profileClose').addEventListener('click', () => document.getElementById('profilePanel').classList.remove('open'));

document.getElementById('signinForm').addEventListener('submit', async e => {
  e.preventDefault();
  try {
    const res = await fetch('/api/auth/signin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: signinEmail.value, password: signinPassword.value })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    setAuth(data.token, data.user);
    closeAuth();
    showToast('Signed in successfully.');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

document.getElementById('signupForm').addEventListener('submit', async e => {
  e.preventDefault();
  const email = signupEmail.value.trim();
  const password = signupPassword.value;
  if (!isValidEmail(email)) {
    showValidationAlert('Enter a valid email. Email must not start with a number.');
    return;
  }
  if (!isStrongPassword(password)) {
    showValidationAlert('Password must be at least 8 characters and include uppercase, lowercase, number, and special character.');
    return;
  }
  try {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: signupName.value, email, password, theme_preference: getCurrentTheme() })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    setAuth(data.token, data.user);
    document.getElementById('devOtp').textContent = `Dev OTP: ${data.otp_dev}`;
    closeAuth();
    showToast('Account created. Verify your email to unlock unlimited use.');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

document.getElementById('sendResetOtpBtn').addEventListener('click', async () => {
  const email = forgotEmail.value.trim();
  if (!isValidEmail(email)) {
    showValidationAlert('Enter a valid email. Email must not start with a number.');
    return;
  }
  try {
    const res = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    document.getElementById('resetDevOtp').textContent = `Reset OTP: ${data.otp_dev}`;
    showToast('Password reset code generated.');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

document.getElementById('forgotForm').addEventListener('submit', async e => {
  e.preventDefault();
  const email = forgotEmail.value.trim();
  const password = resetPassword.value;
  if (!isValidEmail(email)) {
    showValidationAlert('Enter a valid email. Email must not start with a number.');
    return;
  }
  if (!isStrongPassword(password)) {
    showValidationAlert('Password must be at least 8 characters and include uppercase, lowercase, number, and special character.');
    return;
  }
  try {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp: resetOtp.value, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    showToast('Password updated. Please sign in.');
    switchAuthTab('signin');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

document.getElementById('sendOtpBtn').addEventListener('click', async () => {
  const res = await authFetch('/api/auth/send-otp', { method: 'POST' });
  const data = await res.json();
  if (!res.ok) return showToast(data.error, 'error');
  document.getElementById('devOtp').textContent = `Dev OTP: ${data.otp_dev}`;
  showToast('OTP generated.');
});

document.getElementById('verifyOtpBtn').addEventListener('click', async () => {
  const res = await authFetch('/api/auth/verify-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ otp: otpInput.value })
  });
  const data = await res.json();
  if (!res.ok) return showToast(data.error, 'error');
  authState.user = data.user;
  renderAuthUi();
  showToast('Email verified.');
});

document.getElementById('changeEmailBtn').addEventListener('click', async () => {
  if (!isValidEmail(newEmailInput.value)) {
    showValidationAlert('Enter a valid email. Email must not start with a number.');
    return;
  }
  const res = await authFetch('/api/auth/change-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: newEmailInput.value })
  });
  const data = await res.json();
  if (!res.ok) return showToast(data.error, 'error');
  document.getElementById('devOtp').textContent = `Email change OTP: ${data.otp_dev}`;
  showToast('Email change OTP generated.');
});

document.getElementById('confirmEmailBtn').addEventListener('click', async () => {
  const res = await authFetch('/api/auth/confirm-email-change', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ otp: emailChangeOtpInput.value })
  });
  const data = await res.json();
  if (!res.ok) return showToast(data.error, 'error');
  authState.user = data.user;
  renderAuthUi();
  showToast('Email changed.');
});

document.getElementById('logoutBtn').addEventListener('click', async () => {
  if (authState.token) await authFetch('/api/auth/logout', { method: 'POST' });
  clearAuth();
  document.getElementById('profilePanel').classList.remove('open');
  showToast('Signed out.');
});

document.getElementById('deleteAccountBtn').addEventListener('click', async () => {
  if (!confirm('Delete this account permanently?')) return;
  const res = await authFetch('/api/auth/delete-account', { method: 'DELETE' });
  const data = await res.json();
  if (!res.ok) return showToast(data.error, 'error');
  clearAuth();
  document.getElementById('profilePanel').classList.remove('open');
  showToast('Account deleted.');
});

applyTheme(localStorage.getItem(THEME_KEY) || 'dark');
refreshMe();

// Custom Cursor
const cursor = document.getElementById('cursor');
const cursorFollower = document.getElementById('cursorFollower');
let mouseX = 0, mouseY = 0, followerX = 0, followerY = 0;

document.addEventListener('mousemove', (e) => {
  mouseX = e.clientX; mouseY = e.clientY;
  cursor.style.transform = `translate(${mouseX}px, ${mouseY}px)`;
});
function animateFollower() {
  followerX += (mouseX - followerX) * 0.15;
  followerY += (mouseY - followerY) * 0.15;
  cursorFollower.style.transform = `translate(${followerX}px, ${followerY}px)`;
  requestAnimationFrame(animateFollower);
}
animateFollower();
document.querySelectorAll('a, button, input, .dropzone').forEach(el => {
  el.addEventListener('mouseenter', () => cursorFollower.classList.add('hover'));
  el.addEventListener('mouseleave', () => cursorFollower.classList.remove('hover'));
});

// Navbar Scroll
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 80) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
});

// Mobile Menu
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
const mobileClose = document.getElementById('mobileClose');
hamburger.addEventListener('click', () => mobileMenu.classList.add('open'));
mobileClose.addEventListener('click', () => mobileMenu.classList.remove('open'));
function closeMobileMenu() { mobileMenu.classList.remove('open'); }

// Word Swap
const words = ["Instantly.", "Accurately.", "Effortlessly."];
let currentWordIndex = 0;
const wordSwap = document.getElementById('wordSwap');
setInterval(() => {
  wordSwap.style.opacity = 0;
  setTimeout(() => {
    currentWordIndex = (currentWordIndex + 1) % words.length;
    wordSwap.textContent = words[currentWordIndex];
    wordSwap.style.opacity = 1;
  }, 300);
}, 3000);

// Scroll Reveal
const revealElements = document.querySelectorAll('.reveal');
const revealOptions = { threshold: 0.1, rootMargin: "0px 0px -50px 0px" };
const revealObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('active');
      observer.unobserve(entry.target);
    }
  });
}, revealOptions);
revealElements.forEach(el => revealObserver.observe(el));

// Toast
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? 'check-circle-2' : 'alert-circle';
  toast.innerHTML = `<i data-lucide="${icon}" class="toast-icon"></i> <span>${message}</span>`;
  container.appendChild(toast);
  lucide.createIcons();
  setTimeout(() => {
    toast.style.animation = 'fadeOut 0.3s forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Upload Logic
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const filePreviewCard = document.getElementById('filePreviewCard');
const fpFiles = document.getElementById('fpFiles');
const fpRemove = document.getElementById('fpRemove');
const extractBtn = document.getElementById('extractBtn');
const progressWrap = document.getElementById('progressWrap');
const loadingMsg = document.getElementById('loadingMsg');
const progressBar = document.getElementById('progressBar');
const dzContent = document.getElementById('dzContent');
const browseLabel = document.querySelector('label[for="fileInput"]');

let selectedFiles = [];

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
  dropzone.addEventListener(evt, e => { e.preventDefault(); e.stopPropagation(); });
});
['dragenter', 'dragover'].forEach(evt => {
  dropzone.addEventListener(evt, () => dropzone.classList.add('dragover'));
});
['dragleave', 'drop'].forEach(evt => {
  dropzone.addEventListener(evt, () => dropzone.classList.remove('dragover'));
});
dropzone.addEventListener('drop', e => {
  const dt = e.dataTransfer;
  if (dt.files && dt.files.length > 0) handleFiles(dt.files);
});
browseLabel.addEventListener('click', e => {
  if (!authState.user && hasUsedAnonymousTrial()) {
    e.preventDefault();
    openAuth('signup');
    showToast('Please sign up and sign in to continue extracting.', 'error');
  }
});
fileInput.addEventListener('click', e => {
  if (!authState.user && hasUsedAnonymousTrial()) {
    e.preventDefault();
    openAuth('signup');
    showToast('Please sign up and sign in to continue extracting.', 'error');
  }
});
fileInput.addEventListener('change', function() {
  if (this.files && this.files.length > 0) handleFiles(this.files);
});

function handleFiles(files) {
  if (!authState.user && hasUsedAnonymousTrial()) {
    openAuth('signup');
    showToast('Please sign up and sign in to continue extracting.', 'error');
    fileInput.value = "";
    return;
  }
  selectedFiles = Array.from(files).filter(f => 
    f.name.toLowerCase().endsWith('.pdf') || 
    f.name.toLowerCase().endsWith('.docx') || 
    f.name.toLowerCase().endsWith('.doc')
  );
  if (selectedFiles.length === 0) {
    dropzone.classList.add('error');
    showToast("Unsupported file type. Please upload PDF or DOCX.", "error");
    setTimeout(() => dropzone.classList.remove('error'), 500);
    return;
  }
  dzContent.style.display = 'none';
  filePreviewCard.style.display = 'block';
  fpFiles.innerHTML = selectedFiles.map(f => `
    <div class="file-item">
      <i data-lucide="file-text" class="file-item-icon"></i>
      <div class="file-item-info">
        <div class="file-item-name">${f.name}</div>
        <div class="file-item-size">${(f.size / 1024 / 1024).toFixed(2)} MB</div>
      </div>
      <i data-lucide="check" class="toast-icon success"></i>
    </div>
  `).join('');
  lucide.createIcons();
}

fpRemove.addEventListener('click', () => resetUpload());
window.resetUpload = function() {
  selectedFiles = [];
  fileInput.value = "";
  filePreviewCard.style.display = 'none';
  dzContent.style.display = 'block';
  document.getElementById('results').style.display = 'none';
  document.getElementById('emptyState').style.display = 'none';
};

// Extraction
let currentReportPath = "";
let extractedTables = [];
let currentTableIndex = 0;

const loadingMessages = [
  "Detecting table boundaries...",
  "Parsing cell structure...",
  "Cleaning extracted data...",
  "Formatting results...",
  "Almost done..."
];

extractBtn.addEventListener('click', async () => {
  if (!authState.user && hasUsedAnonymousTrial()) {
    openAuth('signup');
    showToast('Your free extraction is used. Please sign up and then sign in to continue.', 'error');
    return;
  }
  if (selectedFiles.length === 0) return;
  extractBtn.disabled = true;
  document.getElementById('extractBtnText').textContent = "Extracting...";
  progressWrap.style.display = 'block';
  progressBar.classList.add('indeterminate');
  document.getElementById('results').style.display = 'none';
  document.getElementById('emptyState').style.display = 'none';
  
  let msgIdx = 0;
  const msgInterval = setInterval(() => {
    msgIdx = (msgIdx + 1) % loadingMessages.length;
    loadingMsg.textContent = loadingMessages[msgIdx];
  }, 2000);

  const formData = new FormData();
  selectedFiles.forEach(f => formData.append('files', f));

  try {
    const res = await fetch('/api/extract', {
      method: 'POST',
      headers: authState.user ? authHeaders() : { 'X-Anonymous-Trial': '1' },
      body: formData
    });
    clearInterval(msgInterval);
    const data = await res.json();
    
    if (!res.ok) throw new Error(data.error || "Extraction failed");
    
    extractedTables = data.tables || [];
    currentReportPath = data.report_path || "";
    if (data.anonymous_trial_used) {
      markAnonymousTrialUsed();
      showToast('Free extraction used. Sign up to continue using RowRocket.');
    }
    if (typeof data.unverified_uses_remaining === 'number') {
      authState.user.unverified_uses = authState.user.free_unverified_uses - data.unverified_uses_remaining;
      renderAuthUi();
      if (data.unverified_uses_remaining > 0) showToast(`${data.unverified_uses_remaining} unverified uses remaining.`);
    }
    
    if (extractedTables.length === 0) {
      document.getElementById('emptyState').style.display = 'block';
    } else {
      document.getElementById('results').style.display = 'block';
      showToast("Extraction Complete!");
      renderResults();
      document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
    }
  } catch (err) {
    clearInterval(msgInterval);
    showToast(err.message, "error");
    console.error(err);
  } finally {
    extractBtn.disabled = false;
    document.getElementById('extractBtnText').textContent = "Extract Tables →";
    progressWrap.style.display = 'none';
    progressBar.classList.remove('indeterminate');
  }
});

function renderResults() {
  const stats = document.getElementById('resultsStats');
  let totalRows = extractedTables.reduce((sum, t) => sum + (t.rows ? t.rows.length : 0), 0);
  stats.textContent = `${extractedTables.length} tables found • ${totalRows} rows total`;

  const tabsContainer = document.getElementById('tableTabs');
  const tabList = document.getElementById('tabList');
  if (extractedTables.length > 1) {
    tabsContainer.style.display = 'block';
    tabList.innerHTML = extractedTables.map((t, i) => 
      `<button class="tab-btn ${i === 0 ? 'active' : ''}" data-idx="${i}">Table ${i+1}</button>`
    ).join('');
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        currentTableIndex = parseInt(this.dataset.idx);
        renderTableData();
      });
    });
  } else {
    tabsContainer.style.display = 'none';
  }
  currentTableIndex = 0;
  renderTableData();
}

function renderTableData() {
  const tableHead = document.getElementById('tableHead');
  const tableBody = document.getElementById('tableBody');
  const table = extractedTables[currentTableIndex];
  if (!table) return;

  const headers = table.headers || [];
  const rows = table.rows || [];

  if (headers.length > 0) {
    tableHead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
  } else if (rows.length > 0) {
    tableHead.innerHTML = `<tr>${rows[0].map((_, i) => `<th>Column ${i+1}</th>`).join('')}</tr>`;
  } else {
    tableHead.innerHTML = '';
  }

  window.currentTableRows = rows;
  displayRows(rows);
}

function displayRows(rowsToDisplay) {
  const tableBody = document.getElementById('tableBody');
  document.getElementById('rowCount').textContent = `Showing ${rowsToDisplay.length} rows`;
  tableBody.innerHTML = rowsToDisplay.map((row, rIdx) => 
    `<tr style="animation-delay: ${rIdx * 0.05}s">${row.map(cell => `<td>${cell !== null ? cell : ''}</td>`).join('')}</tr>`
  ).join('');
}

// Search
document.getElementById('tableSearch').addEventListener('input', function(e) {
  const query = e.target.value.toLowerCase();
  if (!window.currentTableRows) return;
  if (!query) {
    displayRows(window.currentTableRows);
    return;
  }
  const filtered = window.currentTableRows.filter(row => 
    row.some(cell => String(cell).toLowerCase().includes(query))
  );
  displayRows(filtered);
});

// Actions
document.getElementById('copyAllBtn').addEventListener('click', () => {
  const table = extractedTables[currentTableIndex];
  if (!table) return;
  const headers = table.headers || [];
  let text = headers.join('\t') + '\n';
  table.rows.forEach(r => text += r.join('\t') + '\n');
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied to clipboard!");
  });
});

document.getElementById('pdfBtn').addEventListener('click', async () => {
  if (!currentReportPath) return;
  try {
    const res = await authFetch(`/api/download-report?path=${encodeURIComponent(currentReportPath)}`);
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || 'Failed to download PDF');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentReportPath.split(/[\\/]/).pop() || 'report.pdf';
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    showToast(err.message, 'error');
  }
});

document.getElementById('csvBtn').addEventListener('click', async () => {
  const table = extractedTables[currentTableIndex];
  if (!table) return;
  try {
    const res = await authFetch('/api/download-csv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(table)
    });
    if (!res.ok) throw new Error("Failed to generate CSV");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `table_${currentTableIndex + 1}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    showToast(err.message, "error");
  }
});
