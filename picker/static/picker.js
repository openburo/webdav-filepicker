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

function sendMessage(message) {
  if (window.parent !== window && CLIENT_URL) {
    window.parent.postMessage(message, CLIENT_URL);
  }
}

async function fetchContent(path) {
  const resp = await fetch("/api/content" + path);
  const data = await resp.json();
  return data.content;
}

document.querySelectorAll(".file-entry[data-path]").forEach(el => {
  el.addEventListener("click", () => {
    const file = {
      name: el.dataset.name,
      path: el.dataset.path,
      size: parseInt(el.dataset.size),
      contentType: el.dataset.contentType,
    };

    if (MULTIPLE) {
      const idx = selectedFiles.findIndex(f => f.path === file.path);
      if (idx >= 0) {
        selectedFiles.splice(idx, 1);
        el.classList.remove("selected");
      } else {
        selectedFiles.push(file);
        el.classList.add("selected");
      }
    } else {
      document.querySelectorAll(".file-entry").forEach(e => e.classList.remove("selected"));
      selectedFiles.length = 0;
      selectedFiles.push(file);
      el.classList.add("selected");
    }

    updateButton();
  });
});

document.getElementById("btn-select")?.addEventListener("click", async () => {
  if (selectedFiles.length === 0) return;

  const wantSharingUrl = INTENT_TYPE.includes("sharingUrl");
  const wantDownloadUrl = INTENT_TYPE.includes("downloadUrl");
  const wantPayload = INTENT_TYPE.includes("payload");
  const fileUrl = (path) => WEBDAV_BASE + path;

  const results = await Promise.all(selectedFiles.map(async (f) => {
    const result = {
      name: f.name,
      mimeType: f.contentType,
      size: f.size,
    };
    if (wantSharingUrl) {
      result.sharingUrl = fileUrl(f.path);
    }
    if (wantDownloadUrl) {
      result.downloadUrl = fileUrl(f.path);
    }
    if (wantPayload) {
      result.payload = await fetchContent(f.path);
    }
    return result;
  }));

  sendMessage({
    status: "done",
    id: INTENT_ID,
    results,
  });
});

document.getElementById("btn-cancel")?.addEventListener("click", () => {
  sendMessage({
    status: "cancel",
    id: INTENT_ID,
  });
});
