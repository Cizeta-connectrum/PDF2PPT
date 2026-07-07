const form = document.getElementById("add-app-form");
const nameInput = document.getElementById("app-name");
const urlInput = document.getElementById("app-url");
const addBtn = document.getElementById("add-app-btn");
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
      <span class="app-item-actions">
        <a href="${encodeURI(app.url)}" target="_blank" rel="noopener noreferrer" class="launch-btn">起動</a>
        <button type="button" class="delete-btn" data-id="${app.id}">削除</button>
      </span>
    `;
    listEl.appendChild(li);
  }
}

async function loadApps() {
  try {
    const response = await fetch("/api/apps");
    if (!response.ok) throw new Error("一覧の取得に失敗しました。");
    const apps = await response.json();
    renderApps(apps);
  } catch (err) {
    setStatus(`エラーが発生しました: ${err.message}`, "error");
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = nameInput.value.trim();
  const url = urlInput.value.trim();
  if (!name || !url) {
    setStatus("アプリ名とURLを入力してください。", "error");
    return;
  }

  addBtn.disabled = true;
  setStatus("追加中です...", "");

  try {
    const response = await fetch("/api/apps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, url }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      setStatus(data.error || "追加に失敗しました。", "error");
      return;
    }

    form.reset();
    setStatus("アプリを追加しました。", "success");
    await loadApps();
  } catch (err) {
    setStatus(`エラーが発生しました: ${err.message}`, "error");
  } finally {
    addBtn.disabled = false;
  }
});

listEl.addEventListener("click", async (e) => {
  const target = e.target;
  if (!(target instanceof HTMLElement) || !target.classList.contains("delete-btn")) return;

  const id = target.dataset.id;
  target.disabled = true;

  try {
    const response = await fetch(`/api/apps/${id}`, { method: "DELETE" });
    if (!response.ok && response.status !== 204) {
      throw new Error("削除に失敗しました。");
    }
    setStatus("アプリを削除しました。", "success");
    await loadApps();
  } catch (err) {
    setStatus(`エラーが発生しました: ${err.message}`, "error");
    target.disabled = false;
  }
});

loadApps();
