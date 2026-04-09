const selectedFiles = [];

function updateButton() {
  const btn = document.getElementById("btn-select");
  if (selectedFiles.length === 0) {
    btn.disabled = true;
    btn.textContent = "Sélectionner";
  } else if (selectedFiles.length === 1) {
    btn.disabled = false;
    btn.textContent = "Sélectionner (1)";
  } else {
    btn.disabled = false;
    btn.textContent = `Sélectionner (${selectedFiles.length})`;
  }
}

document.querySelectorAll(".file-entry[data-path]").forEach(el => {
  el.addEventListener("click", (e) => {
    const file = {
      name: el.dataset.name,
      path: el.dataset.path,
      size: parseInt(el.dataset.size),
      contentType: el.dataset.contentType,
    };

    const idx = selectedFiles.findIndex(f => f.path === file.path);
    if (idx >= 0) {
      selectedFiles.splice(idx, 1);
      el.classList.remove("selected");
    } else {
      selectedFiles.push(file);
      el.classList.add("selected");
    }

    updateButton();
  });
});

document.getElementById("btn-select").addEventListener("click", () => {
  if (selectedFiles.length > 0) {
    console.log("Selected:", selectedFiles);
    alert("Fichiers sélectionnés:\n" + selectedFiles.map(f => f.name).join("\n"));
  }
});

document.getElementById("btn-cancel").addEventListener("click", () => {
  console.log("Cancelled");
  alert("Annulé");
});
