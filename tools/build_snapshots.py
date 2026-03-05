import os, json, re
from openpyxl import load_workbook

UPLOADS="uploads"
SNAP="snapshots"

os.makedirs(SNAP,exist_ok=True)

files=os.listdir(UPLOADS)

dates=[]

for f in files:
    if f.endswith(".xlsx") or f.endswith(".xlsm"):
        m=re.search(r"\d{4}-\d{2}-\d{2}",f)
        if m:
            dates.append((m.group(),f))

dates.sort()

index={"snapshots":[]}

for d,f in dates:

    wb=load_workbook(os.path.join(UPLOADS,f),data_only=True)

    ws=wb["통합정렬"]

    rows=list(ws.iter_rows(values_only=True))

    headers=rows[0]

    data=[]

    for r in rows[1:]:

        if not r[0]:
            continue

        data.append({
            "rank":r[0],
            "guild":r[1],
            "server":r[2],
            "score_total":r[5]
        })

    out={
        "snapshot_date":d,
        "rankings":data
    }

    with open(f"{SNAP}/{d}.json","w",encoding="utf8") as w:
        json.dump(out,w,ensure_ascii=False,indent=2)

    index["snapshots"].append({"date":d})

with open(f"{SNAP}/index.json","w",encoding="utf8") as w:
    json.dump(index,w,indent=2)

print("done")
