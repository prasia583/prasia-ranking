import json
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

UPLOAD_DIR = Path("uploads")
OUT_DIR = Path("site") / "snapshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ✅ 결사 랭킹은 보통 이 시트에 있음
PREFERRED_SHEETS = ["통합정렬", "통합 정렬", "결사랭킹", "결사 랭킹"]

def safe_str(x):
    if x is None:
        return ""
    return str(x).strip()

def safe_num(x):
    # 엑셀 숫자/문자 혼용 대비
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return x
    s = str(x).strip()
    if s == "":
        return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except Exception:
        return s  # 숫자로 변환 불가면 원문 유지

def guess_label_from_filename(stem: str) -> str:
    # ranking_2026_03_05 -> 2026-03-05
    parts = stem.replace("-", "_").split("_")
    nums = [p for p in parts if p.isdigit()]
    if len(nums) >= 3:
        y, m, d = nums[-3], nums[-2], nums[-1]
        if len(y) == 4:
            return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    return stem

def pick_worksheet(wb):
    # 우선순위 시트 있으면 그걸 선택
    for name in PREFERRED_SHEETS:
        if name in wb.sheetnames:
            return wb[name], name
    # 없으면 첫 시트
    return wb[wb.sheetnames[0]], wb.sheetnames[0]

def normalize_header(v):
    # 공백/개행/특수문자 약간 정리
    return safe_str(v).replace("\n", "").replace("\r", "").replace(" ", "")

def build_header_map(ws, header_row=1, max_cols=80):
    """
    1행(헤더)에서 '순위/결사명/서버명/총점' 같은 헤더를 찾아 컬럼 인덱스로 매핑.
    """
    m = {}
    for col in range(1, max_cols + 1):
        v = ws.cell(row=header_row, column=col).value
        if v is None:
            continue
        key = normalize_header(v)

        # ✅ 통합정렬에서 자주 보이는 헤더들 (공백 제거 기준)
        # 예: '순위', '결사명', '서버명', '총점', '총점수', '총점수(합계)'...
        if key in ("순위",):
            m["rank"] = col
        elif key in ("결사명", "결사"):
            m["guild"] = col
        elif key in ("서버명", "서버"):
            m["server"] = col
        elif key in ("총점", "총점수", "총점수합계", "총점수(합계)", "총점수(합계)"):
            m["total_score"] = col
        elif key in ("토벌등급점수", "토벌등급점수합계", "토벌등급점수(합계)", "토벌등급점수합계"):
            m["hunt_score"] = col
        elif key in ("레벨별점수", "레벨별점수합계", "레벨별점수(합계)", "레벨별점수합계"):
            m["level_score"] = col

    return m

def parse_guild_ranking(ws):
    """
    ✅ 통합정렬 시트에서 결사 랭킹을 뽑는다.
    - 헤더 기반으로 컬럼을 찾아서 파싱
    """
    header = build_header_map(ws, header_row=1)

    # 헤더 매핑이 부족하면(엑셀 구조가 특이하면) fallback: 고정 위치 추정
    # 통합정렬 예시: A 순위, B 결사명, C 서버명, D 토벌등급점수, E 레벨별점수, F 총점수
    rank_col = header.get("rank", 1)
    guild_col = header.get("guild", 2)
    server_col = header.get("server", 3)
    hunt_col = header.get("hunt_score", 4)
    level_col = header.get("level_score", 5)
    total_col = header.get("total_score", 6)

    rows = []
    # 데이터는 보통 2행부터
    for r in range(2, ws.max_row + 1):
        rank = ws.cell(row=r, column=rank_col).value
        guild = ws.cell(row=r, column=guild_col).value
        server = ws.cell(row=r, column=server_col).value

        # 빈 줄 스킵
        if rank is None and (guild is None or safe_str(guild) == "") and (server is None or safe_str(server) == ""):
            continue

        hunt_score = ws.cell(row=r, column=hunt_col).value
        level_score = ws.cell(row=r, column=level_col).value
        total_score = ws.cell(row=r, column=total_col).value

        rows.append({
            "rank": safe_num(rank),
            "guild": safe_str(guild),
            "server": safe_str(server),
            "hunt_score": safe_num(hunt_score),
            "level_score": safe_num(level_score),
            "total_score": safe_num(total_score),
        })

    # rank 기준 정렬(혹시 엑셀 정렬이 깨져 있어도)
    def sort_key(x):
        v = x.get("rank")
        if isinstance(v, (int, float)):
            return v
        try:
            return int(str(v))
        except Exception:
            return 10**9

    rows.sort(key=sort_key)
    return rows

def build_snapshots_from_uploads():
    index = []

    xlsx_files = sorted(UPLOAD_DIR.glob("*.xlsx"))
    for xlsx_path in xlsx_files:
        stem = xlsx_path.stem
        label = guess_label_from_filename(stem)
        out_name = f"{stem}.json"
        out_path = OUT_DIR / out_name

        wb = load_workbook(xlsx_path, data_only=True)
        ws, used_sheet = pick_worksheet(wb)

        data = parse_guild_ranking(ws)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        index.append({
            "label": label,
            "file": out_name,     # site/app.js가 이 값으로 ./snapshots/${file} fetch
            "rows": len(data),
            "sheet": used_sheet,  # 디버깅용
        })

    # 라벨이 YYYY-MM-DD면 최신이 위로
    def sort_key(item):
        try:
            return datetime.strptime(item["label"], "%Y-%m-%d")
        except Exception:
            return datetime.min

    index.sort(key=sort_key, reverse=True)

    with open(OUT_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(index)} snapshot(s) into {OUT_DIR}")

if __name__ == "__main__":
    build_snapshots_from_uploads()
