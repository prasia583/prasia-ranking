import os
import json
from openpyxl import load_workbook

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "snapshots"

def safe_str(v):
    if v is None:
        return ""
    return str(v).strip()

def safe_num(v):
    if v is None or v == "":
        return None
    try:
        # 엑셀 숫자/문자 모두 처리
        return float(v) if (isinstance(v, float) or isinstance(v, int)) else float(str(v).replace(",", ""))
    except:
        return None

os.makedirs(OUTPUT_DIR, exist_ok=True)

index = []  # snapshots/index.json 목록 만들기

for fname in sorted(os.listdir(UPLOAD_DIR)):
    if not fname.lower().endswith(".xlsx"):
        continue

    path = os.path.join(UPLOAD_DIR, fname)
    wb = load_workbook(path, data_only=True)

    # ✅ 시트 이름을 고정하지 말고 "첫 시트"를 사용 (시트명 때문에 실패하는 경우 방지)
    sheet_name = wb.sheetnames[0]
    ws = wb[sheet_name]

    rows = []
    # 2행부터: 1행은 헤더라고 가정
    for r in ws.iter_rows(min_row=2, values_only=True):
        # r은 튜플. 길이가 짧을 수 있으니 안전하게 꺼내기
        rank = r[0] if len(r) > 0 else None
        guild = r[1] if len(r) > 1 else None
        server = r[2] if len(r) > 2 else None
        hunt_score = r[3] if len(r) > 3 else None
        level_score = r[4] if len(r) > 4 else None
        total_score = r[5] if len(r) > 5 else None

        # rank가 비어있으면 스킵
        if rank is None or safe_str(rank) == "":
            continue

        rows.append({
            "rank": safe_str(rank),
            "guild": safe_str(guild),
            "server": safe_str(server),
            "hunt_score": safe_num(hunt_score),
            "level_score": safe_num(level_score),
            "total_score": safe_num(total_score),
        })

    out_name = fname.rsplit(".", 1)[0] + ".json"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    index.append({
        "file": out_name,
        "label": fname.rsplit(".", 1)[0],   # 드롭다운 표시용
        "sheet": sheet_name,
        "count": len(rows)
    })

# ✅ snapshots 목록 파일 생성 (사이트에서 이걸 읽게 할거임)
with open(os.path.join(OUTPUT_DIR, "index.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print("Snapshots created:", len(index))
