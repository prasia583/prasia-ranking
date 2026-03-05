async function loadSnapshots() {
  // ✅ 현재 사이트 폴더(prasia-ranking/) 기준으로 snapshots 접근
  const res = await fetch("./snapshots/index.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`index.json fetch failed: ${res.status}`);

  const data = await res.json();

  const select = document.getElementById("date");
  select.innerHTML = "";

  // data.snapshots = [{date:"2026_03_05", file:"ranking_2026_03_05"}] 같은 형태를 기대
  (data.snapshots || []).forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s.file;          // ✅ 파일명(확장자 제외) 기준
    opt.textContent = s.date;    // ✅ 표시용 날짜
    select.appendChild(opt);
  });

  if (select.value) {
    loadRanking(select.value);
  }

  select.addEventListener("change", (e) => {
    loadRanking(e.target.value);
  });
}

async function loadRanking(fileBase) {
  const res = await fetch(`./snapshots/${fileBase}.json`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${fileBase}.json fetch failed: ${res.status}`);

  const rows = await res.json();

  const tbody = document.getElementById("rank");
  tbody.innerHTML = "";

  // ✅ build_snapshots.py가 배열로 만들고 있으니 배열 기준으로 렌더
  (rows || []).forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.rank ?? ""}</td>
      <td>${r.server ?? ""}</td>
      <td>${r.guild ?? ""}</td>
      <td>${r.total_score ?? r.score_total ?? ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

loadSnapshots().catch((err) => {
  console.error(err);
  const el = document.getElementById("status");
  if (el) el.textContent = "ERROR: " + err.message;
});
