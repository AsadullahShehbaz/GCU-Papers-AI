// ============================================================
// upload.js — Paper Upload Form
// Handles modal open/close and form submission
// Depends on: config.js, auth.js
// ============================================================


// ── Open / Close Modal ────────────────────────────────────────
function openUploadModal() {
  // Block if not logged in (safety check)
  if (!getCurrentUser()) {
    alert("Please sign in first.");
    return;
  }
  document.getElementById("uploadModal").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeUploadModal() {
  document.getElementById("uploadModal").classList.remove("active");
  document.body.style.overflow = "";
  resetUploadForm();
}


// ── Form Reset ────────────────────────────────────────────────
function resetUploadForm() {
  document.getElementById("uploadForm").reset();
  setUploadStatus("", "");
}


// ── Status message helper ─────────────────────────────────────
// type: "success" | "error" | "loading" | ""
function setUploadStatus(message, type) {
  const el = document.getElementById("uploadStatus");
  el.textContent  = message;
  el.className    = `upload-status ${type}`;
}


// ── Submit ────────────────────────────────────────────────────
async function submitUpload(e) {
  e.preventDefault();

  const user = getCurrentUser();
  if (!user) {
    setUploadStatus("Please sign in first.", "error");
    return;
  }

  // Collect form values
  const form       = e.target;
  const subject    = form.subject.value.trim();
  const semester   = form.semester.value;
  const year       = form.year.value;
  const type       = form.type.value;
  const department = form.department.value;
  const file       = form.pdfFile.files[0];

  // Basic validation
  if (!file) {
    setUploadStatus("Please select a PDF file.", "error");
    return;
  }

  setUploadStatus("Uploading... please wait.", "loading");

  // Build FormData — matches FastAPI Form() fields exactly
  const formData = new FormData();
  formData.append("subject",     subject);
  formData.append("semester",    semester);
  formData.append("year",        year);
  formData.append("type",        type);
  formData.append("department",  department);
  formData.append("uploaded_by", user.email);
  formData.append("file",        file);

  try {
    const res = await fetch(`${CONFIG.API_URL}/api/papers/upload`, {
      method: "POST",
      body:   formData,
      // Don't set Content-Type — browser sets it with boundary automatically
    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Upload failed");

    setUploadStatus(`✅ "${subject}" uploaded successfully!`, "success");

    // Refresh paper list so new paper appears immediately
    setTimeout(() => {
      closeUploadModal();
      loadPapers();   // from script.js
    }, 1500);

  } catch (err) {
    setUploadStatus(`❌ ${err.message}`, "error");
    console.error("Upload error:", err);
  }
}


// ── Attach submit listener ────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("uploadForm").addEventListener("submit", submitUpload);

  // Close modal on backdrop click
  document.getElementById("uploadModal").addEventListener("click", (e) => {
    if (e.target === document.getElementById("uploadModal")) {
      closeUploadModal();
    }
  });
});
