// ============================================================
// auth.js — Google Login
// Handles sign in, sign out, and current user state
// Import order in HTML: config.js → auth.js → script.js
// ============================================================

// ── State ─────────────────────────────────────────────────────
let currentUser = null;   // { email, name, picture } or null


// ── Init Google Sign-In button ────────────────────────────────
function initGoogleAuth() {
  google.accounts.id.initialize({
    client_id: CONFIG.GOOGLE_CLIENT_ID,
    callback:  handleGoogleLogin,
  });

  // Render the sign-in button inside #googleBtn div
  google.accounts.id.renderButton(
    document.getElementById("googleBtn"),
    { theme: "filled_black", size: "large", shape: "pill" }
  );
}


// ── Called by Google after user clicks Sign In ────────────────
async function handleGoogleLogin(response) {
  try {
    // Send token to our backend for verification
    const res = await fetch(`${CONFIG.API_URL}/api/auth/google`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ token: response.credential }),
    });

    if (!res.ok) throw new Error("Login failed");

    currentUser = await res.json();   // { email, name, picture }

    onLoginSuccess(currentUser);

  } catch (err) {
    console.error("Login error:", err);
    showAuthError("Login failed. Please try again.");
  }
}


// ── Sign Out ──────────────────────────────────────────────────
function signOut() {
  google.accounts.id.disableAutoSelect();
  currentUser = null;
  onLogout();
}


// ── UI updates after login / logout ──────────────────────────
function onLoginSuccess(user) {
  // Hide login button, show user info + upload button
  document.getElementById("authSection").innerHTML = `
    <div class="user-info">
      <img src="${user.picture}" alt="${user.name}" class="user-avatar">
      <span class="user-name">${user.name}</span>
      <button class="btn btn-outline" onclick="signOut()">Sign Out</button>
      <button class="btn btn-upload" onclick="openUploadModal()">+ Upload Paper</button>
    </div>
  `;
}

function onLogout() {
  // Show login button again
  document.getElementById("authSection").innerHTML = `
    <div id="googleBtn"></div>
  `;
  initGoogleAuth();
}

function showAuthError(msg) {
  document.getElementById("authSection").innerHTML += `
    <p class="auth-error">${msg}</p>
  `;
}


// ── Getter — used by upload.js ────────────────────────────────
function getCurrentUser() {
  return currentUser;
}


// ── Auto-init when DOM is ready ───────────────────────────────
document.addEventListener("DOMContentLoaded", initGoogleAuth);
