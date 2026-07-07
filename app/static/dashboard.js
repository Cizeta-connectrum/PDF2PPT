const PDF_CONVERTER_APP = {
  name: "PDF変換",
  url: "/convert-tool",
  builtin: true,
  emoji: "📄",
};

const AVATAR_GRADIENTS = [
  ["#7c3aed", "#ec4899"],
  ["#2563eb", "#06b6d4"],
  ["#16a34a", "#84cc16"],
  ["#f97316", "#ef4444"],
  ["#0ea5e9", "#6366f1"],
  ["#db2777", "#f97316"],
];

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

function hostnameOf(url) {
  try {
    return new URL(url).hostname;
  } catch (_) {
    return url;
  }
}

function gradientFor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  }
  const [a, b] = AVATAR_GRADIENTS[hash % AVATAR_GRADIENTS.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

function buildIcon(app) {
  const wrap = document.createElement("div");
  wrap.className = "app-card-icon-wrap";
  wrap.style.background = gradientFor(app.name);

  const glyph = document.createElement("div");
  glyph.className = "app-card-icon-fallback";
  glyph.textContent = app.builtin ? app.emoji || "★" : (app.name.trim().charAt(0) || "?").toUpperCase();
  wrap.appendChild(glyph);

  return wrap;
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

    link.appendChild(buildIcon(app));

    const nameEl = document.createElement("span");
    nameEl.className = "app-card-name";
    nameEl.textContent = app.name;
    link.appendChild(nameEl);

    if (!app.builtin) {
      const urlEl = document.createElement("span");
      urlEl.className = "app-card-url";
      urlEl.textContent = hostnameOf(app.url);
      urlEl.title = app.url;
      link.appendChild(urlEl);
    }

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
