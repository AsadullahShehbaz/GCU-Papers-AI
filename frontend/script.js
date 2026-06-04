// ============================================================
// script.js — Main App
// Fetches papers from backend API
// Depends on: config.js, ai-solver.js
// ============================================================

// ── State ─────────────────────────────────────────────────────
let allPapers        = [];
let allFilteredPapers = [];
let currentPage      = 1;
const PAPERS_PER_PAGE = 12;

// ── DOM Refs ──────────────────────────────────────────────────
const dom = {
  grid:         document.getElementById("papersGrid"),
  search:       document.getElementById("searchInput"),
  semFilter:    document.getElementById("semesterFilter"),
  deptFilter:   document.getElementById("deptFilter"),
  resultCount:  document.getElementById("resultCount"),
  statPapers:   document.getElementById("statPapers"),
  statSubjects: document.getElementById("statSubjects"),
  statSemesters:document.getElementById("statSemesters"),
  statDepts:    document.getElementById("statDepts"),
  modal:        document.getElementById("pdfModal"),
  viewer:       document.getElementById("pdfViewer"),
  modalTitle:   document.getElementById("pdfTitle"),
  closeBtn:     document.getElementById("closeModal"),
  pagination:   document.getElementById("pagination"),
};

// ── Load Papers ───────────────────────────────────────────────
async function loadPapers() {
  dom.grid.innerHTML = `<p class="state-msg">Loading papers…</p>`;

  try {
    const res = await fetch(`${CONFIG.API_URL}/api/papers/`);
    if (!res.ok) throw new Error("Failed to load papers");

    allPapers         = await res.json();
    allFilteredPapers = [...allPapers];

    updateStats(allPapers);
    renderPapers(allPapers);

  } catch (err) {
    dom.grid.innerHTML = `<p class="state-msg">⚠️ Could not load papers.</p>`;
    console.error(err);
  }
}

// ── Render ────────────────────────────────────────────────────
function renderPapers(papers) {
  const totalPages = Math.ceil(papers.length / PAPERS_PER_PAGE);
  const start      = (currentPage - 1) * PAPERS_PER_PAGE;
  const paginated  = papers.slice(start, start + PAPERS_PER_PAGE);

  dom.resultCount.textContent =
    `${papers.length} paper${papers.length !== 1 ? "s" : ""}`;

  if (!papers.length) {
    dom.grid.innerHTML     = `<p class="state-msg">No papers match your search.</p>`;
    dom.pagination.innerHTML = "";
    return;
  }

  dom.grid.innerHTML = paginated.map(buildCard).join("");

  // Pagination
  dom.pagination.innerHTML = totalPages <= 1 ? "" : `
    <button class="btn-page" onclick="changePage(-1)" ${currentPage === 1 ? "disabled" : ""}>← Prev</button>
    <span class="page-info">Page ${currentPage} of ${totalPages}</span>
    <button class="btn-page" onclick="changePage(1)"  ${currentPage === totalPages ? "disabled" : ""}>Next →</button>
  `;
}

// ── Card Template ─────────────────────────────────────────────
function buildCard(p) {
  // Safely escape for onclick attributes
  const safeSubject = escAttr(p.subject);
  const safeDept    = escAttr(p.department || "");

  return `
    <article class="paper-card" data-id="${p.id}">

      <div class="card-top">
        <span class="badge badge-sem">Sem ${p.semester}</span>
        <span class="badge badge-year">${p.year}</span>
        <span class="badge badge-dept">${p.department || "—"}</span>
      </div>

      <h3 class="card-title">${p.subject}</h3>
      <p class="card-type">${p.type}</p>

      <div class="card-buttons">
        <button class="btn-card btn-view"
          onclick="openPDF('${p.pdf}','${safeSubject}')">
          View
        </button>
        <button class="btn-card btn-download"
          onclick="downloadPDF('${p.pdf}','${safeSubject}')">
          Download
        </button>
        <button class="btn-card btn-solve"
          onclick="openSolver('${safeSubject}','${p.semester}','${safeDept}')">
          🤖 Solve
        </button>
      </div>

    </article>`;
}

function escAttr(str) {
  return String(str).replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

// ── Pagination ────────────────────────────────────────────────
function changePage(dir) {
  currentPage += dir;
  renderPapers(allFilteredPapers);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── Stats ─────────────────────────────────────────────────────
function updateStats(papers) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  set("statPapers",    papers.length);
  set("statSubjects",  new Set(papers.map(p => p.subject)).size);
  set("statSemesters", new Set(papers.map(p => p.semester)).size);
  set("statDepts",     new Set(papers.map(p => p.department)).size);
}

// ── Filters ───────────────────────────────────────────────────
function applyFilters() {
  const query = dom.search?.value.toLowerCase().trim() || "";
  const sem   = dom.semFilter?.value  || "";
  const dept  = dom.deptFilter?.value || "";

  allFilteredPapers = allPapers.filter(p => {
    const matchText = p.subject.toLowerCase().includes(query);
    const matchSem  = !sem  || p.semester.toString() === sem;
    const matchDept = !dept || p.department === dept;
    return matchText && matchSem && matchDept;
  });

  currentPage = 1;
  renderPapers(allFilteredPapers);
}

// ── PDF Modal ─────────────────────────────────────────────────
function openPDF(url, title) {
  dom.modalTitle.textContent = title;
  dom.viewer.src = CONFIG.pdfViewer(url);
  dom.modal.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  dom.modal.classList.remove("active");
  dom.viewer.src = "";
  document.body.style.overflow = "";
}

function downloadPDF(url, title) {
  Object.assign(document.createElement("a"), {
    href: url, download: title || "paper", target: "_blank",
  }).click();
}

// ── Listeners ─────────────────────────────────────────────────
function attachListeners() {
  dom.search?.   addEventListener("input",  applyFilters);
  dom.semFilter?.addEventListener("change", applyFilters);
  dom.deptFilter?.addEventListener("change", applyFilters);
  dom.closeBtn?. addEventListener("click",  closeModal);
  dom.modal?.    addEventListener("click",  e => { if (e.target === dom.modal) closeModal(); });
  document.      addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
}

// ── Theme ─────────────────────────────────────────────────────
function toggleTheme() {
  const isLight = document.body.classList.toggle("light");
  localStorage.setItem("theme", isLight ? "light" : "dark");
  const btn = document.getElementById("themeBtn");
  if (btn) btn.textContent = isLight ? "🌙" : "☀️";
}

const savedTheme = localStorage.getItem("theme");
if (savedTheme === "light") {
  document.body.classList.add("light");
  const btn = document.getElementById("themeBtn");
  if (btn) btn.textContent = "🌙";
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Only run papers logic when grid exists (papers.html)
  if (document.getElementById("papersGrid")) {
    attachListeners();
    loadPapers();
  }
});