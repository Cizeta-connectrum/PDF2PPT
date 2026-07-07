const PDF_CONVERTER_APP = {
  name: "PDF変換",
  url: "/convert-tool",
  builtin: true,
};

const form = document.getElementById("add-app-form");
const nameInput = document.getElementById("app-name");
const urlInput = document.getElementById("app-url");
const addBtn = document.getElementById("add-app-btn");
const statusEl = document.getElementById("apps-status");
const listEl = document.getElementById("apps-list");

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
    const host = new URL(url, window.location.origin).hostname;
    return `https://www.google.com/s2/favicons?sz=64&domain=${encodeURIComponent(host)}`;
  } catch (_) {
    return "";
  }
}

function renderApps(apps) {
  listEl.innerHTML = "";

  for (const app of [PDF_CONVERTER_APP, ...apps]) {
    const wrapper = document.createElement("div");
    wrapper.className = "app-card-wrapper";

    const link = document.createElement("a");
    link.className = "app-card";
    link.href = app.builtin ? app.url : encodeURI(app.url);
    if (!app.builtin) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
    link.innerHTML = `
      <img class="app-card-icon" src="${faviconUrl(app.url)}" alt="" width="40" height="40" loading="lazy">
      <span class="app-card-name">${escapeHtml(app.name)}</span>
      ${app.builtin ? "" : `<span class="app-card-url">${escapeHtml(app.url)}</span>`}
    `;
    wrapper.appendChild(link);

    if (!app.builtin) {
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = "delete-btn";
      deleteBtn.dataset.id = app.id;
      deleteBtn.textContent = "削除";
      wrapper.appendChild(deleteBtn);
    }

    listEl.appendChild(wrapper);
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
