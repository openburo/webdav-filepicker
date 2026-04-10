class PickerBridge {
  constructor(pickerUrl) {
    this.pickerUrl = pickerUrl;
    this.pickerOrigin = new URL(pickerUrl).origin;
    this.intentId = null;
    this.display = "iframe";
    this.pickerWindow = null;
    this.pendingFiles = null;
    this.resultTarget = document.getElementById("result");

    this._initOverlay();
    this._listenMessages();
  }

  _initOverlay() {
    const overlay = document.getElementById("picker-overlay");
    if (overlay) {
      overlay.addEventListener("click", (e) => {
        if (e.target === e.currentTarget) this.close();
      });
    }
  }

  _listenMessages() {
    window.addEventListener("message", (e) => {
      if (e.origin !== this.pickerOrigin) return;

      const data = e.data;
      if (!data || !data.status) return;
      if (data.id && data.id !== this.intentId) return;

      if (data.status === "ready" && this.pendingFiles) {
        this.pickerWindow.postMessage(
          { status: "save", id: this.intentId, results: this.pendingFiles },
          this.pickerOrigin
        );
      } else if (["done", "cancel", "error"].includes(data.status)) {
        fetch("/result", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        })
          .then(r => r.text())
          .then(html => { this.resultTarget.innerHTML = html; });
        this.close();
      }
    });
  }

  open(params) {
    this.intentId = generateId();
    params.set("clientUrl", window.location.origin);
    params.set("id", this.intentId);

    const url = this.pickerUrl + "?" + params.toString();

    if (this.display === "popup") {
      this.pickerWindow = window.open(url, "picker", "width=800,height=600");
    } else {
      const iframe = document.getElementById("picker-iframe");
      iframe.src = url;
      this.pickerWindow = iframe.contentWindow;
      document.getElementById("picker-overlay").classList.add("active");
    }
  }

  close() {
    this.pendingFiles = null;
    if (this.display === "popup") {
      if (this.pickerWindow && !this.pickerWindow.closed) {
        this.pickerWindow.close();
      }
      this.pickerWindow = null;
    } else {
      const overlay = document.getElementById("picker-overlay");
      const iframe = document.getElementById("picker-iframe");
      if (overlay) overlay.classList.remove("active");
      if (iframe) iframe.src = "";
    }
  }
}
