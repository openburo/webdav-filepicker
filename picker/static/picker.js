const selectedFiles = [];
let saveData = null;


function updateButton() {
  const btn = document.getElementById("btn-select");
  if (!btn) return;
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
  const parentWindow = window.opener || window.parent;
  if (CLIENT_URL) {
    parentWindow.postMessage(message, CLIENT_URL);
  }
}

async function fetchContent(path) {
  const resp = await fetch("/api/content" + path);
  const data = await resp.json();
  return data.content;
}

// PICK mode: file selection
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

// PICK mode: send selection
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
      result.sharingUrl = window.location.origin + "/preview" + f.path;
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

// SAVE mode: receive payload from client and handle save
if (ACTION === "SAVE") {
  // Notify client we're ready to receive payload
  sendMessage({ status: "ready", id: INTENT_ID });

  // Listen for payload from client
  window.addEventListener("message", (e) => {
    console.debug("filePicker received message", e.data)
    if (!e.data || e.data.status !== "save") {
        console.warn("Bad status");
        return
    }
    if (e.data.id !== INTENT_ID) {
        console.warn("Bad intent ID");
        return
    };
    saveData = e.data;

    const filenameInput = document.getElementById("save-filename");
    const fileList = document.getElementById("save-file-list");
    if (saveData.results.length === 1 && filenameInput) {
      filenameInput.value = saveData.results[0].name;
      filenameInput.classList.remove("hidden");
    } else if (fileList) {
      fileList.innerHTML = "<p>" + saveData.results.map(f => f.name).join(", ") + "</p>";
    }
  });

  document.getElementById("btn-save")?.addEventListener("click", async () => {
    if (!saveData || !saveData.results || saveData.results.length === 0) {
      console.warn("save data")
      sendMessage({ status: "error", id: INTENT_ID, message: "No file data received" });
      return;
    }

    // In single mode, use the filename input if available
    const filenameInput = document.getElementById("save-filename");
    const files = saveData.results.map((f, i) => {
      const name = (i === 0 && filenameInput && filenameInput.value.trim())
        ? filenameInput.value.trim()
        : f.name;
      return { ...f, name };
    });

    const results = [];
    for (const f of files) {
      const body = { name: f.name };
      if (f.payload) {
        body.payload = f.payload;
      } else if (f.downloadUrl) {
        body.downloadUrl = f.downloadUrl;
      } else {
        sendMessage({ status: "error", id: INTENT_ID, message: `No data for ${f.name}` });
        return;
      }

      const resp = await fetch("/api/save" + CURRENT_PATH, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        sendMessage({ status: "error", id: INTENT_ID, message: err.error || `Upload failed for ${f.name}` });
        return;
      }
      results.push(await resp.json());
    }

    console.log("save done", results)
    sendMessage({ status: "done", id: INTENT_ID, results });
  });
}

// Cancel
document.getElementById("btn-cancel")?.addEventListener("click", () => {
  sendMessage({
    status: "cancel",
    id: INTENT_ID,
  });
});
