// app.js
lucide.createIcons();

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
fileInput.addEventListener('change', function() {
  if (this.files && this.files.length > 0) handleFiles(this.files);
});

function handleFiles(files) {
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
    const res = await fetch('/api/extract', { method: 'POST', body: formData });
    clearInterval(msgInterval);
    const data = await res.json();
    
    if (!res.ok) throw new Error(data.error || "Extraction failed");
    
    extractedTables = data.tables || [];
    currentReportPath = data.report_path || "";
    
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

document.getElementById('pdfBtn').addEventListener('click', () => {
  if (!currentReportPath) return;
  window.location.href = `/api/download-report?path=${encodeURIComponent(currentReportPath)}`;
});

document.getElementById('csvBtn').addEventListener('click', async () => {
  const table = extractedTables[currentTableIndex];
  if (!table) return;
  try {
    const res = await fetch('/api/download-csv', {
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
