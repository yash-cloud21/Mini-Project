/**
 * Student Career Platform — Core JavaScript
 * Handles: sidebar toggle, alert auto-dismiss, utility helpers.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ----------------------------------------------------------------
    // Sidebar toggle (mobile)
    // ----------------------------------------------------------------
    const toggle  = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (toggle && sidebar) {
        toggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function (e) {
            if (
                window.innerWidth <= 768 &&
                sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !toggle.contains(e.target)
            ) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ----------------------------------------------------------------
    // Auto-dismiss flash messages after 5 seconds
    // ----------------------------------------------------------------
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity .3s ease, transform .3s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';
            setTimeout(function () { alert.remove(); }, 300);
        }, 5000);
    });
});
