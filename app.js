async function fetchJSON(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

function $(id) { return document.getElementById(id); }

let allRows = [];
let currentFile = "";

function renderTable(rows) {
  const tbody = $("tbody");
  tbody.innerHTML = "";

  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.rank ?? ""}</td>
      <td>${row.server ?? ""}</td>
      <td>${row.guild ?? ""}</td>
      <td>${row.hunt_score ?? ""}</td>
      <td>${row.level_score ?? ""}</td>
      <td>${row.total_score ?? ""}</td>
    `;
    tbody.appendChild(tr);
  }

  $("count").textContent = `${rows.length} rows`;
  $("current").textContent = currentFile ? currentFile : "-";
}

function applyFilter() {
  const q = ($("search").value || "").trim().toLowerCase();
  if (!q) return renderTable(allRows);

  const filtered = allRows.filter(r =>
    String(r.rank ?? "").toLowerCase().includes(q) ||
    String(r.server ?? "").toLowerCase().includes(q) ||
    String(r.guild ?? "").toLowerCase().includes(q)
  );
  renderTable(filtered);
}

async function loadSnapshot(file) {
  currentFile = file;
  // ✅ Pages에서는 repo 경로가 있으니 "슬래시로 시작하면" 안됨
  allRows = await fetchJSON(`./snapshots/${file}`);
  applyFilter();
}

async function init() {
  try {
    const idx = await fetchJSON("./snapshots/index.json");

    const sel = $("date");
    sel.innerHTML = "";

    if (!idx.length) {
      $("status").textContent = "snapshots/index.json은 있지만 목록이 비어있음 (uploads에 xlsx가 없거나 파싱 결과가 0일 수 있음)";
      return;
    }

    for (const item of idx) {
      const opt = document.createElement("option");
      opt.value = item.file;
      opt.textContent = `${item.label} (${item.count})`;
      sel.appendChild(opt);
    }

    sel.addEventListener("change", () => loadSnapshot(sel.value));
    $("search").addEventListener("input", applyFilter);

    await loadSnapshot(sel.value);
    $("status").textContent = "loaded";
  } catch (e) {
    console.error(e);
    $("status").textContent = `ERROR: ${e.message}`;
  }
}

init();
