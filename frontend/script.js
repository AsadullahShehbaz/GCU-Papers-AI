// ============================================================
// script.js — Main App
// Fetches papers from backend API instead of data.json
// Depends on: config.js
// ============================================================

// ── State ─────────────────────────────────────────────────────
let allPapers = [];
let allFilteredPapers = [];
let currentPage = 1;
const PAPERS_PER_PAGE = 12;
// ── DOM Refs — queried once, reused everywhere ─────────────────
const dom = {
  grid:        document.getElementById("papersGrid"),
  search:      document.getElementById("searchInput"),
  semFilter:   document.getElementById("semesterFilter"),
  deptFilter:  document.getElementById("deptFilter"),
  resultCount: document.getElementById("resultCount"),
  statPapers:     document.getElementById("statPapers"),
  statSubjects:   document.getElementById("statSubjects"),
  statSemesters:  document.getElementById("statSemesters"),
  modal:       document.getElementById("pdfModal"),
  viewer:      document.getElementById("pdfViewer"),
  modalTitle:  document.getElementById("pdfTitle"),
  closeBtn:    document.getElementById("closeModal"),
  pagination: document.getElementById("pagination"),
};

// ── Load Papers from API ──────────────────────────────────────
async function loadPapers() {
  dom.grid.innerHTML = `<p class="state-msg">Loading papers…</p>`;

  try {
    const res = await fetch(`${CONFIG.API_URL}/api/papers/`);
    if (!res.ok) throw new Error("Failed to load papers");

    allPapers = await res.json();
    allFilteredPapers = [...allPapers];
    updateStats(allPapers);
    renderPapers(allPapers);

  } catch (err) {
    dom.grid.innerHTML = `<p class="state-msg">⚠️ Could not load papers.</p>`;
    console.error(err);
  }
}

function renderPapers(papers) {
  const totalPages = Math.ceil(papers.length / PAPERS_PER_PAGE);
  const start = (currentPage - 1) * PAPERS_PER_PAGE;
  const paginated = papers.slice(start, start + PAPERS_PER_PAGE);

  dom.resultCount.textContent = `${papers.length} paper${papers.length !== 1 ? "s" : ""}`;

  if (!papers.length) {
    dom.grid.innerHTML = `<p class="state-msg">No papers match your search.</p>`;
    dom.pagination.innerHTML = "";
    return;
  }

  dom.grid.innerHTML = paginated.map(buildCard).join("");

  // Pagination controls
  dom.pagination.innerHTML = `
    <button class="btn btn-view" onclick="changePage(-1)" ${currentPage === 1 ? "disabled" : ""}>← Prev</button>
    <span style="color:var(--muted); font-size:14px;">Page ${currentPage} of ${totalPages}</span>
    <button class="btn btn-view" onclick="changePage(1)" ${currentPage === totalPages ? "disabled" : ""}>Next →</button>
  `;
}

function changePage(dir) {
  currentPage += dir;
  renderPapers(allFilteredPapers);
  window.scrollTo({ top: 0, behavior: "smooth" });
}
// ── Card Template ─────────────────────────────────────────────
function buildCard(p) {
  return `
    <article class="paper-card" data-id="${p.id}">
      <div class="card-top">
        <span class="badge">Sem ${p.semester}</span>
        <span class="badge badge-year">${p.year}</span>
        <span class="badge badge-dept">${p.department}</span>
      </div>
      <h3 class="card-title">${p.subject}</h3>
      <p class="card-type">${p.type}</p>
      <div class="card-buttons">
        <button class="btn btn-view"     onclick="openPDF('${p.pdf}','${escAttr(p.subject)}')">View</button>
        <button class="btn btn-download" onclick="downloadPDF('${p.pdf}','${escAttr(p.subject)}')">Download</button>
      </div>
    </article>`;
}

function escAttr(str) {
  return str.replace(/'/g, "\\'");
}

// ── Stats ─────────────────────────────────────────────────────
function updateStats(papers) {
  dom.statPapers.textContent    = papers.length;
  dom.statSubjects.textContent  = new Set(papers.map(p => p.subject)).size;
  dom.statSemesters.textContent = new Set(papers.map(p => p.semester)).size;
}

// ── Filters ───────────────────────────────────────────────────
function applyFilters() {
  const query = dom.search.value.toLowerCase().trim();
  const sem   = dom.semFilter.value;
  const dept  = dom.deptFilter.value;
  
  const result = allPapers.filter(p => {
    const matchText = p.subject.toLowerCase().includes(query);
    const matchSem  = !sem  || p.semester.toString() === sem;
    const matchDept = !dept || p.department === dept;
    return matchText && matchSem && matchDept;
  });
  allFilteredPapers = result;
  currentPage = 1;        // reset to page 1 on every filter

  renderPapers(result);
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

// ── Event Listeners ───────────────────────────────────────────
function attachListeners() {
  dom.search   .addEventListener("input",  applyFilters);
  dom.semFilter.addEventListener("change", applyFilters);
  dom.deptFilter.addEventListener("change", applyFilters);
  dom.closeBtn .addEventListener("click",  closeModal);
  dom.modal    .addEventListener("click",  e => { if (e.target === dom.modal) closeModal(); });
  document     .addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  attachListeners();
  loadPapers();
});
