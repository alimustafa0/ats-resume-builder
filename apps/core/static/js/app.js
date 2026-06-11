(function () {
  function bytesToSize(bytes) {
    if (!bytes) return "";
    const mb = bytes / (1024 * 1024);
    return mb >= 1 ? mb.toFixed(1) + " MB" : Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function setupDropzone(zone) {
    if (zone.dataset.dzReady) return;
    zone.dataset.dzReady = "1";
    const input = zone.querySelector(".dropzone-input");
    const fileOut = zone.querySelector(".dropzone-file");
    if (!input) return;

    function showFile() {
      const f = input.files && input.files[0];
      if (f) {
        zone.classList.add("has-file");
        if (fileOut) fileOut.textContent = f.name + "  \u00b7  " + bytesToSize(f.size);
      } else {
        zone.classList.remove("has-file");
        if (fileOut) fileOut.textContent = "";
      }
    }

    input.addEventListener("change", showFile);

    ["dragenter", "dragover"].forEach(function (evt) {
      zone.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add("is-dragover");
      });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      zone.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove("is-dragover");
      });
    });
    zone.addEventListener("drop", function (e) {
      const files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) {
        input.files = files;
        showFile();
      }
    });
  }

  function initDropzones() {
    document.querySelectorAll(".dropzone").forEach(setupDropzone);
  }

  initDropzones();
  document.body.addEventListener("htmx:load", initDropzones);
})();