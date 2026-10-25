/**
 * Electricity Waste Monitor — shared frontend helpers
 */

document.addEventListener("DOMContentLoaded", function () {
  // Sidebar toggle (mobile)
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  // Auto-dismiss alerts after 6s (optional UX)
  document.querySelectorAll(".alert-dismissible").forEach(function (el) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      try {
        bsAlert.close();
      } catch (e) {
        /* ignore */
      }
    }, 6000);
  });
});
