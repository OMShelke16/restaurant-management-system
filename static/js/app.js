// Minimal UI helpers for The Pass — no frameworks needed.

function toggleDrawer(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('open');
}

// Auto-dismiss flash messages after a few seconds.
document.addEventListener('DOMContentLoaded', function () {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 4000);
  });
});
