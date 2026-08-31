'use strict';

document.addEventListener('DOMContentLoaded', function () {

  // Auto-dismiss flash alerts after 5 seconds
  document.querySelectorAll('.alert.alert-dismissible').forEach(function (el) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) {
        try { bsAlert.close(); } catch (_) {}
      }
    }, 5000);
  });

  // Confirm dialogs for destructive actions
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      const msg = this.dataset.confirm || 'Are you sure?';
      if (!confirm(msg)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });

  // Clickable table rows (navigate to data-href on row click,
  // but ignore clicks on interactive child elements)
  document.querySelectorAll('.incident-row[data-href]').forEach(function (row) {
    row.addEventListener('click', function (e) {
      if (e.target.closest('a, button, form, input, select, textarea')) return;
      window.location.href = this.dataset.href;
    });
  });

});
