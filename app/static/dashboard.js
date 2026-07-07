const refreshBtn = document.getElementById("refresh-btn");
const statusEl = document.getElementById("apps-status");
const listEl = document.getElementById("apps-list");
const emptyEl = document.getElementById("apps-empty");

function setStatus(message, kind) {
  statusEl.textContent = message;
  statusEl.className = "status" + (kind ? ` ${kind}` : "");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderApps(apps) {
  listEl.innerHTML = "";
  emptyEl.hidden = apps.length > 0;

  for (const app of apps) {
    const li = document.createElement("li");
    li.className = "app-item";
    li.innerHTML = `
      <span class="app-item-name">${escapeHtml(app.name)}</span>
      <span class="app-item-url">${escapeHtml(app.url)}</span>
      <a href="${encodeURI(app.url)}" target="_blank" rel="noopener noreferrer" class="launch-btn">起動</a>
    `;
    listEl.appendChild(li);
  }
}

async function loadApps() {
  refreshBtn.disabled = true;
  setStatus("読み込み中...", "");

  try {
    const response = await fetch("/api/apps");
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      setStatus(data.error || "一覧の取得に失敗しました。", "error");
      return;
    }

    renderApps(data);
    setStatus("");
  } catch (err) {
    setStatus(`エラーが発生しました: ${err.message}`, "error");
  } finally {
    refreshBtn.disabled = false;
  }
}

refreshBtn.addEventListener("click", loadApps);

loadApps();
