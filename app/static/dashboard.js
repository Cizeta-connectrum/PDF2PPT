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

function faviconUrl(url) {
  try {
    const host = new URL(url).hostname;
    return `https://www.google.com/s2/favicons?sz=64&domain=${encodeURIComponent(host)}`;
  } catch (_) {
    return "";
  }
}

function renderApps(apps) {
  listEl.innerHTML = "";
  emptyEl.hidden = apps.length > 0;

  for (const app of apps) {
    const card = document.createElement("a");
    card.className = "app-card";
    card.href = encodeURI(app.url);
    card.target = "_blank";
    card.rel = "noopener noreferrer";
    card.innerHTML = `
      <img class="app-card-icon" src="${faviconUrl(app.url)}" alt="" width="40" height="40" loading="lazy">
      <span class="app-card-name">${escapeHtml(app.name)}</span>
      <span class="app-card-url">${escapeHtml(app.url)}</span>
    `;
    listEl.appendChild(card);
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
