// ============================================================
// auth.js — Google Login + Profile Navbar
// Shows profile name in navbar with hover dropdown for sign out
// Depends on: config.js
// ============================================================

// ── State ─────────────────────────────────────────────────────
let currentUser = null;

// ── Init Google Sign-In ───────────────────────────────────────
function initGoogleAuth() {
  if (typeof google === "undefined") return;

  google.accounts.id.initialize({
    client_id: CONFIG.GOOGLE_CLIENT_ID,
    callback:  handleGoogleLogin,
  });

  // Render button only if element exists on this page
  const btn = document.getElementById("googleBtn");
  if (btn) {
    google.accounts.id.renderButton(btn, {
      theme: "filled_black",
      size:  "large",
      shape: "pill",
    });
  }
}

// ── Handle login response from Google ─────────────────────────
async function handleGoogleLogin(response) {
  try {
    const res = await fetch(`${CONFIG.API_URL}/api/auth/google`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ token: response.credential }),
    });

    if (!res.ok) throw new Error("Login failed");

    currentUser = await res.json();
    localStorage.setItem("gcul_user", JSON.stringify(currentUser));

    updateNavProfile(currentUser);
    if (typeof onLoginSuccess === "function") onLoginSuccess(currentUser);

  } catch (err) {
    console.error("Login error:", err);
  }
}

// ── Sign Out ──────────────────────────────────────────────────
function signOut() {
  if (typeof google !== "undefined") {
    google.accounts.id.disableAutoSelect();
  }
  currentUser = null;
  localStorage.removeItem("gcul_user");

  updateNavProfile(null);
  if (typeof onLogout === "function") onLogout();
}

// ── Update Navbar Profile UI ──────────────────────────────────
function updateNavProfile(user) {
  const authSection = document.getElementById("authSection");
  if (!authSection) return;

  if (user) {
    // First name only — keeps navbar clean
    const firstName = user.name.split(" ")[0];

    authSection.innerHTML = `
      <div class="profile-wrap" id="profileWrap">
        <button class="profile-btn" id="profileBtn">
          <img
            src="${user.picture}"
            alt="${user.name}"
            class="profile-avatar"
            onerror="this.style.display='none'"
          >
          <span class="profile-name">${firstName}</span>
          <span class="profile-chevron">▾</span>
        </button>

        <div class="profile-dropdown" id="profileDropdown">
          <div class="profile-dropdown-header">
            <img src="${user.picture}" alt="${user.name}" class="dropdown-avatar"
              onerror="this.style.display='none'">
            <div>
              <div class="dropdown-name">${user.name}</div>
              <div class="dropdown-email">${user.email}</div>
            </div>
          </div>
          <div class="profile-dropdown-divider"></div>
          <a href="upload.html" class="dropdown-item">⬆️ Upload Paper</a>
          <a href="papers.html" class="dropdown-item">📚 Browse Papers</a>
          <div class="profile-dropdown-divider"></div>
          <button class="dropdown-item dropdown-signout" onclick="signOut()">
            🚪 Sign Out
          </button>
        </div>
      </div>
    `;

    // Toggle dropdown on click (mobile-friendly)
    document.getElementById("profileBtn").addEventListener("click", (e) => {
      e.stopPropagation();
      document.getElementById("profileDropdown").classList.toggle("open");
    });

    // Close on outside click
    document.addEventListener("click", () => {
      document.getElementById("profileDropdown")?.classList.remove("open");
    });

  } else {
    // Not logged in — show Google button
    authSection.innerHTML = `<div id="googleBtn"></div>`;
    initGoogleAuth();
  }
}

// ── Getter — used by upload.js and other modules ──────────────
function getCurrentUser() {
  return currentUser;
}

// ── Restore session from localStorage ────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const saved = localStorage.getItem("gcul_user");
  if (saved) {
    try {
      currentUser = JSON.parse(saved);
      updateNavProfile(currentUser);
      if (typeof onLoginSuccess === "function") onLoginSuccess(currentUser);
    } catch {
      localStorage.removeItem("gcul_user");
    }
  }
  initGoogleAuth();
});