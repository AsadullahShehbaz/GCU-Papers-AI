// ============================================================
// CONFIG — tweak global behaviour here
// ============================================================
const CONFIG = {
  dataUrl: "data.json",
  pdfViewer: (url) => `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(url)}`,
};

// ============================================================
// STATE
// ============================================================
let allPapers = [];

// ============================================================
// DOM REFS — grab once, reuse everywhere
// ============================================================
const dom = {
  grid:           () => document.getElementById("papersGrid"),
  search:         () => document.getElementById("searchInput"),
  semFilter:      () => document.getElementById("semesterFilter"),
  modal:          () => document.getElementById("pdfModal"),
  viewer:         () => document.getElementById("pdfViewer"),
  modalTitle:     () => document.getElementById("pdfTitle"),
  closeBtn:       () => document.getElementById("closeModal"),
  statPapers:     () => document.getElementById("statPapers"),
  statSubjects:   () => document.getElementById("statSubjects"),
  statSemesters:  () => document.getElementById("statSemesters"),
  resultCount:    () => document.getElementById("resultCount"),
  deptFilter: () => document.getElementById("deptFilter"),
};

// ============================================================
// DATA
// ============================================================
async function loadPapers() {
  try {
    const res = await fetch(CONFIG.dataUrl);
    if (!res.ok) throw new Error("Network error");
    allPapers = await res.json();
    updateStats(allPapers);
    renderPapers(allPapers);
  } catch (err) {
    dom.grid().innerHTML = `<p class="state-msg">⚠️ Could not load papers. Check your data.json file.</p>`;
    console.error(err);
  }
}

// ============================================================
// RENDER
// ============================================================
function renderPapers(papers) {
  dom.resultCount().textContent = `${papers.length} paper${papers.length !== 1 ? "s" : ""}`;

  if (!papers.length) {
    dom.grid().innerHTML = `<p class="state-msg">No papers match your search.</p>`;
    return;
  }

  // Build all cards in one go — single DOM write
  dom.grid().innerHTML = papers.map(buildCard).join("");
}

// ── Single card template ──────────────────────────────────────
function buildCard(p) {
  return `
    <article class="paper-card" data-id="${p.id}">
      <div class="card-top">
        <span class="badge">Sem ${p.semester}</span>
        <span class="badge badge-year">${p.year}</span>
      </div>
      <h3 class="card-title">${p.subject}</h3>
      <p class="card-type">${p.type}</p>
      <div class="card-buttons">
        <button class="btn btn-view"     onclick="openPDF('${p.pdf}','${escAttr(p.subject)}')">View</button>
        <button class="btn btn-download" onclick="downloadPDF('${p.pdf}','${escAttr(p.subject)}')">Download</button>
      </div>
    </article>`;
}

// Escape single quotes so onclick strings don't break
function escAttr(str) {
  return str.replace(/'/g, "\\'");
}

// ============================================================
// STATS
// ============================================================
function updateStats(papers) {
  dom.statPapers().textContent    = papers.length;
  dom.statSubjects().textContent  = new Set(papers.map(p => p.subject)).size;
  dom.statSemesters().textContent = new Set(papers.map(p => p.semester)).size;
}

// ============================================================
// FILTERS — one function, called by both listeners
// ============================================================
function applyFilters() {
  const query = dom.search().value.toLowerCase().trim();
  const sem   = dom.semFilter().value;
  const dept  = document.getElementById("deptFilter").value;

  const result = allPapers.filter(p => {
    const matchText = p.subject.toLowerCase().includes(query);
    const matchSem  = !sem  || p.semester.toString() === sem;
    const matchDept = !dept || p.department === dept;
    return matchText && matchSem && matchDept;
  });

  renderPapers(result);
}

dom.search    = memoize(dom.search);   // keep reference stable
dom.semFilter = memoize(dom.semFilter);

// tiny helper so we don't query DOM on every keystroke
function memoize(fn) {
  let cache;
  return () => cache ?? (cache = fn());
}

// Attach listeners after DOM ready (called at bottom)
function attachFilters() {
  document.getElementById("searchInput")   .addEventListener("input",  applyFilters);
  document.getElementById("semesterFilter").addEventListener("change", applyFilters);
  document.getElementById("deptFilter").addEventListener("change", applyFilters);
}

// ============================================================
// PDF MODAL
// ============================================================
function openPDF(url, title) {
  dom.modalTitle().textContent = title;
  dom.viewer().src = CONFIG.pdfViewer(url);
  dom.modal().classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  dom.modal().classList.remove("active");
  dom.viewer().src = "";
  document.body.style.overflow = "";
}

function downloadPDF(url, title) {
  const a = Object.assign(document.createElement("a"), {
    href: url, download: title || "paper", target: "_blank",
  });
  a.click();
}

// ============================================================
// MODAL EVENT LISTENERS
// ============================================================
function attachModal() {
  dom.closeBtn().addEventListener("click", closeModal);
  dom.modal().addEventListener("click", e => { if (e.target === dom.modal()) closeModal(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });
  
}

// ============================================================
// INIT
// ============================================================
function init() {
  attachFilters();
  attachModal();
  loadPapers();
}

init();