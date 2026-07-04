const form = document.getElementById("convert-form");
const fileInput = document.getElementById("pdf_file");
const dropzone = document.getElementById("dropzone");
const dropzoneLabel = document.getElementById("dropzone-label");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");

function setStatus(message, kind) {
  statusEl.textContent = message;
  statusEl.className = "status" + (kind ? ` ${kind}` : "");
}

function updateLabel() {
  if (fileInput.files.length > 0) {
    dropzoneLabel.textContent = fileInput.files[0].name;
  } else {
    dropzoneLabel.textContent = "ここにPDFをドラッグ&ドロップ、またはクリックして選択";
  }
}

fileInput.addEventListener("change", updateLabel);

["dragenter", "dragover"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  });
});

dropzone.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    fileInput.files = files;
    updateLabel();
  }
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!fileInput.files.length) {
    setStatus("PDFファイルを選択してください。", "error");
    return;
  }

  const formData = new FormData(form);
  submitBtn.disabled = true;
  setStatus("変換中です。しばらくお待ちください...", "");

  try {
    const response = await fetch("/convert", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let message = "変換に失敗しました。";
      try {
        const data = await response.json();
        if (data.error) message = data.error;
      } catch (_) {
        /* ignore parse errors */
      }
      setStatus(message, "error");
      return;
    }

    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : "presentation.pptx";

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    setStatus("変換が完了しました。ダウンロードを開始します。", "success");
  } catch (err) {
    setStatus(`エラーが発生しました: ${err.message}`, "error");
  } finally {
    submitBtn.disabled = false;
  }
});
