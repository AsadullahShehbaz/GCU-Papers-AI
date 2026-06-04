// ============================================================
// config.js — Frontend configuration
// Only file you touch when moving between dev and production
// ============================================================

const CONFIG = {
  // Your Render backend URL (change this after deploying)
  API_URL: "https://gculpapersai.vercel.app/",

  // Your Google OAuth Client ID
  GOOGLE_CLIENT_ID: "your-client-id.apps.googleusercontent.com",

  // PDF viewer — using PDF.js
  pdfViewer: (url) =>
    `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(url)}`,
};