// ============================================================
// config.js — Frontend configuration
// Only file you touch when moving between dev and production
// ============================================================

// 1. Detect if the browser is currently running locally
const isLocalhost = Boolean(
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname.search(/\[::1\]/)?.[0]
);

// 2. Define environment-specific configurations
const CONFIG = {
  // Dynamic API URL assignment
  API_URL: isLocalhost 
    ? "http://127.0.0.1:8000" 
    : "https://gculpapersai.vercel.app/",
  

  // Your Google OAuth Client ID
  GOOGLE_CLIENT_ID: "636727255190-jebjospo4suh9d1v9i0bppbocelnsm49.apps.googleusercontent.com",

  // PDF viewer — using PDF.js
  pdfViewer: (url) =>
    `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(url)}`,
};
