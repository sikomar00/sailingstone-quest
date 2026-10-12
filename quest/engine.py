"""SAILINGSTONE QUEST 엔진: 진행 상태, 채점, 명령어."""
import datetime as _dt
import importlib.util
import inspect
import json
import random
import re
import sqlite3
import sys
import time
import traceback
from pathlib import Path

from . import dbgen, ui
from .missions_py import JUNG, PY_MISSIONS
from .missions_sql import SQL_MISSIONS, YUN
from .ui import bold, cyan, dim, gold, green, magenta, red, yellow

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "hangyeol.db"
WS = ROOT / "workspace"
SAVE = ROOT / "save.json"

MISSIONS = SQL_MISSIONS + PY_MISSIONS
for _m in MISSIONS:
    _m.setdefault("kind", "sql")
    _m.setdefault("exam", False)
    _m.setdefault("traps", [])
BY_ID = {m["id"]: m for m in MISSIONS}

CHAPTERS = {
    0: ("온보딩", "첫 출근"),
    1: ("기본 조회", "수습 1개월차"),
    2: ("집계", "수습 1개월차"),
    3: ("JOIN", "수습 2개월차"),
    4: ("서브쿼리·CASE·CTE", "수습 2개월차"),
    5: ("윈도우 함수·KPI", "수습 3개월차"),
    6: ("Python 자동화·정합성", "수습 3개월차"),
    7: ("전환 심사 PoC", "전환 심사"),
}
WEEKENDS = {1: "10/10~11", 2: "10/17~18", 3: "10/24~25", 4: "10/31~11/1", 5: "11/7~8"}
CH_WEEKEND = {0: 1, 1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 5}

CH_INTRO = {
    0: (YUN, "환영해요, {name} 님! 사수 윤서진이에요. 첫 고객사는 전기차 부품을 만드는 중견 제조사 (주)한결정밀이에요. "
             "고객사 팀장님들이 티켓으로 요청을 보내면 우리는 SQL로 답을 만들어요. 수습 3개월 동안 티켓을 처리하며 "
             "평가 점수를 쌓고, 마지막 PoC를 통과하면 정규직 전환이에요. 막히면 hint, 테이블 구조가 궁금하면 schema!"),
    1: (YUN, "수습 첫 주는 기본 조회예요. 원하는 행과 컬럼을 정확히 꺼내는 연습이죠. 이미 자신 있으면 "
             "python play.py exam 으로 승급 시험부터 봐도 돼요. 통과하면 이 장은 건너뛰어요."),
    2: (YUN, "이제 숫자를 묶어서 보는 집계예요. 고객사 질문의 70%가 '~별 합계·평균·건수'예요."),
    3: (YUN, "2개월차! 테이블을 잇는 JOIN이에요. 실무 버그의 절반이 여기서 나와요. LEFT JOIN과 NULL, "
             "그리고 행이 불어나는 현상을 조심하세요."),
    4: (YUN, "서브쿼리·CASE·CTE예요. 세일링스톤 공고에 쓰인 '복잡한 조건, 테이블 조합, 비즈니스 로직 구현'이 "
             "바로 이 구간이에요. 이 장을 끝내면 지원서의 SQL 항목을 자신 있게 써도 돼요."),
    5: (YUN, "3개월차, 윈도우 함수예요. 순위·누적·전월 대비·이동평균, 대시보드 KPI는 거의 다 여기서 나와요. "
             "마지막 승급 시험은 예지보전 로직이에요."),
    6: (YUN, "이제 SQL 결과를 파이썬으로 받아 자동화하고, 데이터가 믿을 만한지 검증할 차례예요. "
             "이번 장은 .py 파일에 solve 함수를 작성해요. pandas가 필요해요(pip install pandas)."),
    7: (JUNG, "{name} 님, 전환 심사입니다. 한결정밀 경영기획실이 경영진 KPI 대시보드 PoC를 요청했어요. "
              "지금까지 배운 걸 전부 쓰는 티켓 세 개예요. 결과 기다릴게요."),
}

THANKS = ["고마워요! 바로 회의에 쓸게요.", "오, 빠르네요. 딱 이거예요.", "덕분에 오늘 보고 끝냈어요.",
          "이거 엑셀로 하면 반나절인데… 고마워요.", "깔끔하네요. 다음에도 부탁해요.", "좋아요, 팀원들한테 공유할게요."]

BADGES = [
    ("first", "🎫 첫 티켓"),
    ("oneshot5", "🎯 원샷 5연속"),
    ("skip", "🚀 월반 (승급 시험 통과)"),
    ("intdiv", "🧮 정수 나눗셈 탈출"),
    ("fanout", "🌊 팬아웃 생존자"),
    ("detective", "🕵️ 데이터 탐정"),
    ("weekend", "🔥 주말 전사 (하루 10티켓)"),
    ("steady", "📅 꾸준함 (평일 복습 3일)"),
    ("hired", "🏁 정규직 전환"),
]

TABLE_DOC = {
    "lines": ("생산 라인 마스터", {"line_id": "라인 코드 L1~L5", "line_name": "라인명", "plant": "공장",
                                 "shifts": "교대 수 (0 = 아직 미가동)", "start_date": "가동 시작일"}),
    "products": ("제품 마스터", {"product_id": "제품 코드", "product_name": "제품명", "category": "분류",
                               "unit_price": "단가(원)", "std_shift_qty": "교대당 표준 생산량"}),
    "equipment": ("설비 마스터", {"equip_id": "설비 코드", "equip_name": "설비명", "line_id": "소속 라인",
                                "equip_type": "설비 유형", "install_date": "설치일"}),
    "workers": ("작업자", {"worker_id": "사번", "worker_name": "이름", "line_id": "소속 라인 (NULL = 미배정)",
                         "shift": "근무조", "hire_date": "입사일", "leave_date": "퇴사일 (NULL = 재직)"}),
    "production": ("교대별 생산 실적 (평일만, 공휴일 제외)",
                   {"prod_id": "실적 ID", "prod_date": "생산일 YYYY-MM-DD", "line_id": "라인",
                    "shift": "교대 '주간'/'야간'", "product_id": "제품", "planned_qty": "계획 수량",
                    "produced_qty": "생산 수량", "good_qty": "양품 수량 (불량 = 생산 - 양품)"}),
    "defects": ("불량 상세 (실적별·유형별)", {"defect_id": "ID", "prod_id": "생산 실적 ID",
                                         "defect_type": "불량 유형", "qty": "수량"}),
    "reason_codes": ("정지 사유 코드", {"reason_code": "코드", "reason_name": "사유명",
                                     "is_planned": "1 = 계획 정지, 0 = 비계획"}),
    "downtime": ("설비 정지 이력", {"downtime_id": "ID", "equip_id": "설비", "start_ts": "시작 YYYY-MM-DD HH:MM:SS",
                                 "end_ts": "종료", "reason_code": "사유 코드", "is_planned": "1 = 계획(정비·셋업), 0 = 비계획"}),
    "sensor_daily": ("설비 일별 센서 요약 (가동일만 기록)", {"equip_id": "설비", "reading_date": "측정일",
                                                     "avg_temp": "평균 온도(℃)", "max_vibration": "최대 진동(mm/s)"}),
    "customers": ("고객사", {"customer_id": "고객 코드", "customer_name": "고객사명", "region": "지역",
                           "grade": "등급 A/B/C"}),
    "orders": ("수주", {"order_id": "주문번호", "customer_id": "고객", "product_id": "제품",
                       "order_date": "주문일", "due_date": "납기일", "order_qty": "주문 수량"}),
    "shipments": ("출하 (주문 1건에 여러 번 가능)", {"shipment_id": "ID", "order_id": "주문번호",
                                                "ship_date": "출하일", "ship_qty": "출하 수량"}),
}
RELATIONS = [
    "production.product_id → products.product_id",
    "production.line_id    → lines.line_id",
    "defects.prod_id       → production.prod_id",
    "equipment.line_id     → lines.line_id",
    "downtime.equip_id     → equipment.equip_id",
    "downtime.reason_code  → reason_codes.reason_code",
    "sensor_daily.equip_id → equipment.equip_id",
    "workers.line_id       → lines.line_id",
    "orders.customer_id    → customers.customer_id",
    "orders.product_id     → products.product_id",
    "shipments.order_id    → orders.order_id",
]


# ───────────────────────── 상태 ─────────────────────────
def today():
    return _dt.date.today().isoformat()


def load():
    if SAVE.exists():
        return json.loads(SAVE.read_text(encoding="utf-8"))
    return None


def save(st):
    SAVE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def new_state(name):
    return {"name": name, "created": today(), "xp": 0, "cleared": {},
            "cur": {"id": None, "mode": "normal", "fails": 0, "hints": 0, "solution_seen": False},
            "intro_seen": [], "reviews": [], "perfect_streak": 0, "badges": [], "ended": False}


def next_normal(st):
    for m in MISSIONS:
        if m["id"] not in st["cleared"]:
            return m
    return None


def current(st):
    cur = st["cur"]
    if cur["mode"] in ("exam", "review") and cur["id"] in BY_ID:
        return BY_ID[cur["id"]]
    m = next_normal(st)
    if m and cur["id"] != m["id"]:
        st["cur"] = {"id": m["id"], "mode": "normal", "fails": 0, "hints": 0, "solution_seen": False}
    return m


def mission_file(m, mode="normal"):
    ext = ".py" if m["kind"] == "py" else ".sql"
    if mode == "review":
        return WS / "review" / f"{m['id']}-복습{ext}"
    return WS / f"ch{m['ch']}" / f"{m['id']}{ext}"


def rank_title(st):
    if st["ended"]:
        return "정규직 사원"
    m = next_normal(st)
    return CHAPTERS[m["ch"]][1] if m else "전환 심사"


# ───────────────────────── 파일 템플릿 ─────────────────────────
def _comment_block(m, prefix):
    lines = [prefix + " " + "=" * 60,
             f"{prefix} [티켓 {m['id']}] {m['title']}",
             f"{prefix} 요청자: {m['frm']}",
             prefix]
    for para in m["msg"].split("\n"):
        for l in ui.wrap(para, 70):
            lines.append(f"{prefix}   {l}" if l else prefix)
    lines.append(prefix)
    if m["kind"] == "py":
        lines.append(f"{prefix} 함수   : {m['sig']}")
        for l in ui.wrap("반환   : " + m["out"], 70):
            lines.append(f"{prefix} {l}")
    else:
        for l in ui.wrap("출력 컬럼 : " + m["out"], 70):
            lines.append(f"{prefix} {l}")
        lines.append(f"{prefix} 정렬      : {m.get('order') or '자유 (순서 무관)'}")
    lines += [prefix + " " + "-" * 60,
              f"{prefix} 저장 후 터미널에서  python play.py check   (결과만 보기: python play.py run)",
              f"{prefix} 막히면            python play.py hint    (테이블 구조: python play.py schema)",
              prefix + " " + "=" * 60]
    return "\n".join(lines)


def ensure_file(m, mode="normal", fresh=False):
    path = mission_file(m, mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not fresh:
        return path
    if m["kind"] == "py":
        args = m["sig"][m["sig"].index("(") + 1:-1]
        body = (_comment_block(m, "#") + "\nimport pandas as pd\n\n\n"
                f"def solve({args}):\n"
                "    # conn: 고객사 DB 연결 (sqlite3.Connection, 읽기 전용)\n"
                "    ...\n")
    else:
        body = _comment_block(m, "--") + "\n\n"
    path.write_text(body, encoding="utf-8")
    return path


# ───────────────────────── DB ─────────────────────────
def ro_conn():
    if not DB.exists():
        dbgen.build(DB)
    return sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)


def friendly_sql_error(e):
    s = str(e)
    tips = [
        ("no such column", "그런 컬럼이 없어요. python play.py schema <테이블> 로 컬럼명을 확인하세요. 별칭(p.xxx) 오타도 흔해요."),
        ("no such table", "그런 테이블이 없어요. python play.py schema 로 테이블 목록을 확인하세요."),
        ("ambiguous column", "두 테이블에 같은 이름의 컬럼이 있어요. 별칭.컬럼 (예: p.line_id) 으로 지정하세요."),
        ("misuse of aggregate", "집계 함수를 WHERE에 썼나요? 그룹 조건은 HAVING으로, 또는 서브쿼리로."),
        ("misuse of window", "윈도우 함수는 WHERE·GROUP BY에서 못 써요. WITH로 감싼 뒤 바깥에서 거르세요."),
        ("one statement at a time", "쿼리는 하나만 실행돼요. 연습용 쿼리는 지우거나 -- 로 주석 처리하세요."),
        ("syntax error", "문법 오류예요. 쉼표 빠짐·남음, 따옴표 짝, 키워드 순서(SELECT→FROM→WHERE→GROUP BY→HAVING→ORDER BY)를 확인하세요."),
        ("GROUP BY", "GROUP BY 관련 오류예요. SELECT의 일반 컬럼이 GROUP BY에 다 들어 있는지 확인하세요."),
        ("incomplete input", "쿼리가 덜 끝났어요. 괄호 짝이나 마지막 줄을 확인하세요."),
    ]
    for key, msg in tips:
        if key.lower() in s.lower():
            return f"{s}\n   → {msg}"
    return s


def read_sql_file(path):
    text = path.read_text(encoding="utf-8")
    code = "\n".join(l for l in text.splitlines() if not l.strip().startswith("--")).strip()
    return text if code else None


def exec_sql(sql):
    con = ro_conn()
    try:
        cur = con.execute(sql)
        if cur.description is None:
            return None, None
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchall()
    finally:
        con.close()


# ───────────────────────── 비교 ─────────────────────────
def norm(v):
    if v is None:
        return None
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        try:
            v = v.item()
        except Exception:
            pass
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, _dt.datetime):
        return v.date().isoformat() if (v.hour, v.minute, v.second) == (0, 0, 0) else v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, _dt.date):
        return v.isoformat()
    if isinstance(v, float):
        if v != v:
            return None
        return v
    if isinstance(v, int):
        return v
    return str(v).strip()


def close(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        return abs(a - b) <= 0.051
    return a == b


def row_close(r1, r2):
    return len(r1) == len(r2) and all(close(a, b) for a, b in zip(r1, r2))


def _key(r):
    return tuple("#n" if isinstance(v, (int, float)) else v for v in r)


def match_rows(exp, got):
    """순서 무관 비교. (exp에만 있는 행, got에만 있는 행) 반환."""
    buckets = {}
    for i, r in enumerate(got):
        buckets.setdefault(_key(r), []).append(i)
    used = set()
    missing = []
    for r in exp:
        found = None
        for i in buckets.get(_key(r), []):
            if i not in used and row_close(r, got[i]):
                found = i
                break
        if found is None:
            missing.append(r)
        else:
            used.add(found)
    extra = [got[i] for i in range(len(got)) if i not in used]
    return missing, extra


def compare_rows(exp, got, ordered):
    """반환: ('ok' | 'count' | 'values' | 'order', missing, extra)"""
    exp = [tuple(norm(v) for v in r) for r in exp]
    got = [tuple(norm(v) for v in r) for r in got]
    if len(exp) != len(got):
        missing, extra = match_rows(exp, got)
        return "count", missing, extra
    missing, extra = match_rows(exp, got)
    if missing or extra:
        return "values", missing, extra
    if ordered and not all(row_close(a, b) for a, b in zip(exp, got)):
        return "order", [], []
    return "ok", [], []


# ───────────────────────── 채점: SQL ─────────────────────────
def grade_sql(m, path, st):
    sql = read_sql_file(path)
    if not sql:
        return False, ["아직 쿼리가 비어 있어요. 파일 맨 아래에 쿼리를 쓰고 저장하세요.", dim(f"파일: {path}")], False
    try:
        cols, rows = exec_sql(sql)
    except Exception as e:
        return False, [red("SQL 오류: ") + friendly_sql_error(e), dim("(오류는 시도 횟수에 넣지 않아요)")], False
    if cols is None:
        return False, ["SELECT 결과가 없어요. 조회 쿼리를 작성하세요."], False
    ecols, erows = exec_sql(m["sol"])
    if len(cols) != len(ecols):
        return False, [f"컬럼 수가 달라요: 요청 {len(ecols)}개, 내 결과 {len(cols)}개.",
                       f"요청 컬럼: {', '.join(ecols)}", f"내 컬럼  : {', '.join(cols)}"], True
    ordered = bool(m.get("order"))
    status, missing, extra = compare_rows(erows, rows, ordered)
    if status == "ok":
        return True, [], True
    for t in m["traps"]:
        try:
            _, trows = exec_sql(t["sql"])
            if compare_rows(trows, rows, False)[0] == "ok":
                return False, [yellow("💡 자주 하는 실수예요: ") + t["msg"]], True
        except Exception:
            pass
    fb = []
    if status == "order":
        return False, [green("값은 전부 맞았어요! ") + f"정렬만 다시 확인하세요 → {m['order']}"], True
    if status == "count":
        fb.append(f"행 수가 달라요: 정답 {len(erows)}행, 내 결과 {len(rows)}행.")
        if len(rows) > len(erows):
            fb.append(dim("   행이 많다면: 조건 누락? JOIN으로 행이 불어났나? GROUP BY를 빠뜨렸나?"))
        else:
            fb.append(dim("   행이 적다면: 조건이 너무 강한가? INNER JOIN에서 짝 없는 행이 빠졌나? LIMIT?"))
    else:
        fb.append(f"행 수({len(rows)})는 맞는데 값이 다른 행이 {len(extra)}개 있어요.")
        fb.append(dim("   계산식, 반올림 자릿수, 정수 나눗셈, 필터 순서를 확인해 보세요."))
    if st["cur"]["fails"] >= 1:
        if extra:
            fb.append("   내 결과에만 있는 행 예시: " + yellow(str(extra[0])))
        if missing:
            fb.append("   정답에만 있는 행 예시   : " + cyan(str(missing[0])))
    else:
        fb.append(dim("   (한 번 더 틀리면 다른 행 예시를 보여 줄게요)"))
    return False, fb, True


# ───────────────────────── 채점: Python ─────────────────────────
def load_user_module(path):
    name = f"answer_{abs(hash(str(path)))}_{int(time.time() * 1000)}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def friendly_py_error(e, path):
    tb = traceback.extract_tb(e.__traceback__)
    mine = [f for f in tb if Path(f.filename).resolve() == path.resolve()]
    where = f" ({path.name} {mine[-1].lineno}번째 줄)" if mine else ""
    msg = f"{type(e).__name__}: {e}{where}"
    if isinstance(e, ModuleNotFoundError) and "pandas" in str(e):
        msg += "\n   → pandas가 없어요. 터미널에서: pip install pandas"
    elif isinstance(e, KeyError):
        msg += "\n   → 없는 컬럼 이름을 썼을 수 있어요. df.columns 로 확인하세요."
    elif isinstance(e, sqlite3.Error):
        msg += "\n   → " + friendly_sql_error(e)
    return msg


def to_rows(obj, cmp):
    if cmp == "df":
        try:
            import pandas as pd
        except ModuleNotFoundError:
            raise
        if not isinstance(obj, pd.DataFrame):
            tip = " groupby 결과는 Series예요. .reset_index() 를 붙이면 DataFrame이 돼요." if isinstance(obj, pd.Series) else ""
            return None, f"DataFrame을 반환해야 해요 (지금 반환: {type(obj).__name__}).{tip}"
        df = obj if isinstance(obj.index, pd.RangeIndex) else obj.reset_index()
        return [tuple(r) for r in df.itertuples(index=False, name=None)], None
    if cmp == "list":
        if hasattr(obj, "tolist") and not isinstance(obj, (list, tuple)):
            obj = obj.tolist()
        if not isinstance(obj, (list, tuple, set)):
            return None, f"리스트를 반환해야 해요 (지금 반환: {type(obj).__name__})"
        rows = []
        for x in obj:
            rows.append(tuple(x) if isinstance(x, (list, tuple)) else (x,))
        return rows, None
    return None, None


def grade_py(m, path, st):
    body = path.read_text(encoding="utf-8").split("def solve", 1)[-1]
    if "return" not in body:
        return False, ["아직 solve 함수가 아무것도 return 하지 않아요. 함수 안을 채우고 결과를 return 하세요."], False
    try:
        mod = load_user_module(path)
        fn = getattr(mod, "solve")
    except AttributeError:
        return False, ["solve 함수를 찾을 수 없어요. 함수 이름이 solve인지 확인하세요."], False
    except Exception as e:
        return False, [red("파일 실행 오류: ") + friendly_py_error(e, path)], False
    for args in m["calls"]:
        label = f"solve(conn{''.join(', ' + repr(a) for a in args)})"
        con1, con2 = ro_conn(), ro_conn()
        try:
            try:
                got = fn(con1, *args)
            except Exception as e:
                return False, [red(f"{label} 실행 중 오류: ") + friendly_py_error(e, path),
                               dim("(오류는 시도 횟수에 넣지 않아요)")], False
            exp = m["ref"](con2, *args)
        finally:
            con1.close()
            con2.close()
        if m["cmp"] == "dict":
            if not isinstance(got, dict):
                return False, [f"{label}: dict를 반환해야 해요 (지금 반환: {type(got).__name__})"], True
            gk = {str(k).strip(): norm(v) for k, v in got.items()}
            if set(gk) != set(exp):
                return False, [f"{label}: 키가 달라요. 필요한 키: {list(exp)} / 내 키: {list(gk)}"], True
            bad = [k for k in exp if not close(norm(exp[k]), gk[k])]
            if bad:
                fb = [f"{label}: 값이 다른 KPI가 있어요 → {', '.join(bad)}"]
                if st["cur"]["fails"] >= 1:
                    fb += [f"   {k}: 내 값 {gk[k]} / 정답 {exp[k]}" for k in bad]
                return False, fb, True
            continue
        rows, err = to_rows(got, m["cmp"])
        if err:
            return False, [f"{label}: {err}"], True
        erows, _ = to_rows(exp, m["cmp"])
        if erows and rows and len(erows[0]) != len(rows[0]):
            return False, [f"{label}: 컬럼(원소) 수가 달라요: 정답 {len(erows[0])}개, 내 결과 {len(rows[0])}개"], True
        status, missing, extra = compare_rows(erows, rows, ordered=(m["cmp"] == "df"))
        if status == "ok":
            continue
        if status == "order":
            return False, [green(f"{label}: 값은 다 맞았어요! ") + "정렬 순서만 확인하세요."], True
        fb = [f"{label}: 결과가 달라요 (정답 {len(erows)}개, 내 결과 {len(rows)}개)."]
        if st["cur"]["fails"] >= 1:
            if extra:
                fb.append("   내 결과에만 있는 예시: " + yellow(str(extra[0])))
            if missing:
                fb.append("   정답에만 있는 예시   : " + cyan(str(missing[0])))
        else:
            fb.append(dim("   (한 번 더 틀리면 다른 항목 예시를 보여 줄게요)"))
        return False, fb, True
    return True, [], True


# ───────────────────────── 화면 ─────────────────────────
def banner():
    print(cyan("  ⛵ ") + bold("SAILINGSTONE QUEST") + dim("  ·  세일링스톤 AI-BI 인턴 6기 수습 시뮬레이션"))


def chapter_counts(st, ch):
    ms = [m for m in MISSIONS if m["ch"] == ch]
    return sum(1 for m in ms if m["id"] in st["cleared"]), len(ms)


def maybe_intro(st, m):
    if m and m["ch"] not in st["intro_seen"]:
        who, text = CH_INTRO[m["ch"]]
        print()
        title, rank = CHAPTERS[m["ch"]]
        print(gold(f"━━━ {m['ch']}장 · {title}  ({rank}) ━━━"))
        ui.say(who, text.format(name=st["name"]))
        st["intro_seen"].append(m["ch"])
        save(st)


def show_ticket(st, m):
    mode = st["cur"]["mode"]
    path = ensure_file(m, mode)
    tag = {"exam": "  " + magenta("[승급 시험 모드]"), "review": "  " + magenta("[평일 복습 모드]")}.get(mode, "")
    print()
    lines = [f"요청자: {m['frm']}", ""]
    for para in m["msg"].split("\n"):
        lines += ui.wrap(para, 66) if para else [""]
    lines.append("")
    if m["kind"] == "py":
        lines.append(f"함수: {m['sig']}")
        lines += ui.wrap("반환: " + m["out"], 66)
    else:
        lines += ui.wrap("출력 컬럼: " + m["out"], 66)
        lines.append(f"정렬: {m.get('order') or '자유 (순서 무관)'}")
    lines.append(f"보상: {m['xp']} XP" + ("  (승급 시험: 통과하면 이 장의 남은 티켓 면제)" if m["exam"] and mode == "exam" else ""))
    print(ui.box(f"🎫 티켓 {m['id']}  {m['title']}", lines))
    print(tag)
    rel = path.relative_to(ROOT)
    print(f"  📄 VS Code에서 열기: {bold(str(rel))}")
    print(dim("  작성·저장 → python play.py check   |   결과 미리보기 → python play.py run   |   힌트 → python play.py hint"))


def status(st):
    banner()
    total = len(MISSIONS)
    done = len(st["cleared"])
    print(f"\n  👤 {bold(st['name'])} · {gold(rank_title(st))} · 평가 점수 {bold(str(st['xp']))} XP")
    print(f"  📈 진행 {ui.bar(done, total, 24)} {done}/{total} 티켓")
    print()
    for ch, (title, _) in CHAPTERS.items():
        c, n = chapter_counts(st, ch)
        mark = green("✔") if c == n else (yellow("▶") if c else dim("·"))
        wk = CH_WEEKEND[ch]
        print(f"   {mark} {ch}장 {ui.pad(title, 22)} {ui.bar(c, n, 12)} {c}/{n}  " + dim(f"주말{wk} {WEEKENDS[wk]}"))
    got = [b for k, b in BADGES if k in st["badges"]]
    if got:
        print("\n  🏅 " + "  ".join(got))
    need_review = [k for k, v in st["cleared"].items() if v.get("how") == "solution"]
    if need_review:
        print(dim(f"\n  📌 정답 보고 넘긴 티켓 {len(need_review)}개: 평일에 python play.py daily 로 복습하면 확실히 내 것이 돼요."))
    if st["ended"]:
        print(gold("\n  🏁 정규직 전환 완료! 평일 복습(python play.py daily)으로 감을 유지하세요."))
        return
    m = current(st)
    save(st)
    if m:
        mode = st["cur"]["mode"]
        tag = {"exam": " [승급 시험]", "review": " [복습]"}.get(mode, "")
        print(f"\n  ▶ 현재 티켓{tag}: {bold(m['id'])} {m['title']}  " + dim(f"({m['frm'].split(' (')[0]})"))
        print(dim("    python play.py ticket 으로 내용 보기"))
    print(dim("\n  명령: ticket · run · check · hint · schema · sql · map · exam · daily · back · help"))


# ───────────────────────── 보상 ─────────────────────────
def award_badges(st):
    new = []

    def give(k):
        if k not in st["badges"]:
            st["badges"].append(k)
            new.append(dict(BADGES)[k])
    cl = st["cleared"]
    if cl:
        give("first")
    if st["perfect_streak"] >= 5:
        give("oneshot5")
    if any(v.get("how") == "exam_skip" for v in cl.values()):
        give("skip")
    if "2-3" in cl and cl["2-3"].get("how") != "exam_skip":
        give("intdiv")
    if "4-5" in cl and cl["4-5"].get("how") != "exam_skip":
        give("fanout")
    if all(k in cl for k in ("6-3", "6-4", "6-5")):
        give("detective")
    if sum(1 for v in cl.values() if v.get("date") == today() and v.get("how") != "exam_skip") >= 10:
        give("weekend")
    if len(set(st["reviews"])) >= 3:
        give("steady")
    if st["ended"]:
        give("hired")
    for b in new:
        print(gold(f"  🏅 배지 획득: {b}"))


def on_success(st, m):
    cur = st["cur"]
    mode = cur["mode"]
    base = m["xp"]
    if mode == "review":
        gain = max(3, round(base * 0.15))
        st["xp"] += gain
        st["reviews"].append(today())
        if st["cleared"].get(m["id"], {}).get("how") == "solution":
            st["cleared"][m["id"]]["how"] = "relearned"
        print(green(f"\n  ✅ 복습 완료! +{gain} XP") + dim("  (기억에서 꺼내 쓰는 연습이 실력을 굳혀요)"))
        st["cur"] = {"id": None, "mode": "normal", "fails": 0, "hints": 0, "solution_seen": False}
        award_badges(st)
        save(st)
        return
    if cur["solution_seen"]:
        gain, how, note = round(base * 0.2), "solution", "정답 확인 후 처리"
        st["perfect_streak"] = 0
    else:
        mult = max(0.4, 1 - 0.2 * cur["hints"])
        gain = round(base * mult)
        perfect = cur["fails"] == 0 and cur["hints"] == 0
        bonus = round(base * 0.2) if perfect else 0
        gain += bonus
        how = "solve"
        note = f"원샷 보너스 +{bonus}" if perfect else (f"힌트 {cur['hints']}개 사용" if cur["hints"] else f"{cur['fails'] + 1}번째 시도")
        st["perfect_streak"] = st["perfect_streak"] + 1 if perfect else 0
    st["xp"] += gain
    st["cleared"][m["id"]] = {"xp": gain, "fails": cur["fails"], "hints": cur["hints"], "date": today(), "how": how}
    print()
    print(green(f"  ✅ 티켓 {m['id']} 처리 완료!  +{gain} XP") + dim(f"  ({note})"))
    who = m["frm"].split(" (")[0]
    print(f"  💬 {who}: {random.choice(THANKS)}")
    print(f"  🧠 획득 스킬: {bold(m['skill'])}")
    print(dim("  📝 실무 메모 (윤서진 선임)"))
    for l in ui.wrap(m["tip"], 64):
        print(dim("     " + l))
    if mode == "exam":
        skipped, skipped_xp = 0, 0
        for o in MISSIONS:
            if o["ch"] == m["ch"] and o["id"] not in st["cleared"]:
                g = round(o["xp"] * 0.5)
                st["cleared"][o["id"]] = {"xp": g, "fails": 0, "hints": 0, "date": today(), "how": "exam_skip"}
                st["xp"] += g
                skipped += 1
                skipped_xp += g
        if skipped:
            print(magenta(f"  🚀 승급 시험 통과! {m['ch']}장 남은 티켓 {skipped}개 면제 (+{skipped_xp} XP)"))
    st["cur"] = {"id": None, "mode": "normal", "fails": 0, "hints": 0, "solution_seen": False}
    c, n = chapter_counts(st, m["ch"])
    if c == n:
        title, _ = CHAPTERS[m["ch"]]
        print(gold(f"\n  🎉 {m['ch']}장 「{title}」 클리어!"))
    if m["id"] == "B-3":
        st["ended"] = True
        ending(st)
    award_badges(st)
    save(st)
    nxt = current(st)
    save(st)
    if nxt and not st["ended"]:
        maybe_intro(st, nxt)
        npath = ensure_file(nxt, st["cur"]["mode"])
        print(f"\n  ▶ 다음 티켓: {bold(nxt['id'])} {nxt['title']}")
        print(dim(f"    파일 준비됨: {npath.relative_to(ROOT)}  (요청 내용은 파일 맨 위에 있어요 · 자세히: python play.py ticket)"))


def ending(st):
    print()
    print(gold("━" * 64))
    ui.say(JUNG, f"{st['name']} 님, 전환 심사 결과를 알려 드립니다. 한결정밀 경영기획실에서 PoC 결과를 "
                 "그대로 경영회의에 올렸고, 본 사업 계약으로 이어졌어요. 정규직 전환을 축하합니다. "
                 "오늘부터 정식으로 AI-BI팀이에요.")
    print()
    ui.say(YUN, "아, 그리고 오정민 실장님이 마지막에 이렇게 물어보셨어요. '이거 말로 물어보면 SQL로 답해 주는 것도 "
                "돼요?' 그게 우리 다음 프로젝트, Text-to-SQL이에요. 지금까지 쓴 쿼리가 전부 그 테스트셋이 될 거예요.")
    print(gold("━" * 64))
    solved = sum(1 for v in st["cleared"].values() if v.get("how") == "solve")
    perfect = sum(1 for v in st["cleared"].values() if v.get("how") == "solve" and v["fails"] == 0 and v["hints"] == 0)
    print(f"\n  최종 평가 점수 {bold(str(st['xp']))} XP · 직접 해결 {solved}개 · 원샷 {perfect}개")
    print(dim("  지금까지 작성한 쿼리와 코드는 workspace 폴더에 전부 남아 있어요. 포트폴리오 재료로 쓰세요."))


# ───────────────────────── 명령 ─────────────────────────
def cmd_ticket(st, args):
    m = current(st)
    if not m:
        print(green("모든 티켓을 처리했어요! python play.py daily 로 복습할 수 있어요."))
        return
    maybe_intro(st, m)
    show_ticket(st, m)
    save(st)


def cmd_run(st, args):
    m = current(st)
    if not m:
        return print("진행 중인 티켓이 없어요.")
    path = ensure_file(m, st["cur"]["mode"])
    if m["kind"] == "sql":
        sql = read_sql_file(path)
        if not sql:
            return print(f"쿼리가 비어 있어요. {path.relative_to(ROOT)} 에 작성하세요.")
        try:
            cols, rows = exec_sql(sql)
        except Exception as e:
            return print(red("SQL 오류: ") + friendly_sql_error(e))
        if cols is None:
            return print("SELECT 결과가 없어요.")
        print(ui.table(cols, rows))
    else:
        try:
            mod = load_user_module(path)
            con = ro_conn()
            res = mod.solve(con, *m["calls"][0])
            con.close()
        except Exception as e:
            return print(red("오류: ") + friendly_py_error(e, path))
        print(dim(f"solve(conn{''.join(', ' + repr(a) for a in m['calls'][0])}) 반환값:"))
        try:
            import pandas as pd
            if isinstance(res, pd.DataFrame):
                with pd.option_context("display.max_rows", 30, "display.width", 120):
                    print(res)
                return
        except ModuleNotFoundError:
            pass
        print(repr(res)[:3000])
    print(dim("채점은 python play.py check"))


def cmd_check(st, args):
    m = current(st)
    if not m:
        return print("진행 중인 티켓이 없어요.")
    path = ensure_file(m, st["cur"]["mode"])
    print(dim(f"채점 중… [{m['id']}] {m['title']}"))
    ok, fb, counted = (grade_sql if m["kind"] == "sql" else grade_py)(m, path, st)
    if ok:
        on_success(st, m)
    else:
        if counted:
            st["cur"]["fails"] += 1
            save(st)
        print(red("  ❌ 아직이에요.") + (dim(f"  (오답 {st['cur']['fails']}회)") if counted else ""))
        for l in fb:
            print("  " + l)
        if st["cur"]["hints"] < 3:
            print(dim("  막히면 python play.py hint"))


def cmd_hint(st, args):
    m = current(st)
    if not m:
        return print("진행 중인 티켓이 없어요.")
    cur = st["cur"]
    if cur["hints"] < 3:
        cur["hints"] += 1
        save(st)
    for i in range(cur["hints"]):
        print(f"  💡 힌트 {i + 1}/3: {m['hints'][i]}")
    if cur["hints"] >= 3:
        print(dim("  그래도 막히면 python play.py solution 으로 모범 답안을 볼 수 있어요 (보상 20%, 복습 목록에 추가)."))
    else:
        print(dim(f"  (힌트 1개당 보상 -20%. 다음 힌트: python play.py hint)"))


def pretty_sql(s):
    if "\n" in s:
        return s
    for kw in [" FROM ", " LEFT JOIN ", " JOIN ", " WHERE ", " GROUP BY ", " HAVING ", " ORDER BY ", " LIMIT "]:
        s = s.replace(kw, "\n" + kw.strip() + " ")
    s = s.replace(") SELECT ", ")\nSELECT ")
    return s


def cmd_solution(st, args):
    m = current(st)
    if not m:
        return print("진행 중인 티켓이 없어요.")
    if st["cur"]["hints"] < 3:
        return print(f"힌트 3개를 먼저 다 보세요 (지금 {st['cur']['hints']}개). 스스로 떠올리는 과정이 실력이 돼요.")
    st["cur"]["solution_seen"] = True
    save(st)
    print(yellow("  📖 모범 답안 (직접 파일에 옮겨 적고 check 하세요. 보상은 20%, 복습 목록에 추가돼요)\n"))
    if m["kind"] == "sql":
        print(pretty_sql(m["sol"]))
    else:
        src = inspect.getsource(m["ref"])
        src = re.sub(r"def ref_\w+\(", "def solve(", src).replace("pd = _pd()", "import pandas as pd")
        print(src)


def cmd_schema(st, args):
    con = ro_conn()
    try:
        if args:
            t = args[0]
            if t not in TABLE_DOC:
                return print(f"그런 테이블이 없어요. 목록: {', '.join(TABLE_DOC)}")
            desc, cols = TABLE_DOC[t]
            n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(bold(f"\n  {t}") + f" — {desc} ({n}행)")
            for c in con.execute(f"PRAGMA table_info({t})").fetchall():
                print(f"    {ui.pad(c[1], 16)} {dim(ui.pad(c[2], 8))} {cols.get(c[1], '')}")
            cur = con.execute(f"SELECT * FROM {t} LIMIT 5")
            print("\n  샘플 5행")
            print(ui.table([d[0] for d in cur.description], cur.fetchall()))
        else:
            print(bold("\n  (주)한결정밀 DB 테이블 정의서") + dim("  — 자세히: python play.py schema <테이블>"))
            for t, (desc, cols) in TABLE_DOC.items():
                n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"   {bold(ui.pad(t, 14))} {ui.pad(desc, 34)} {dim(str(n) + '행')}")
                print(dim("      " + ", ".join(cols)))
            print(bold("\n  연결 키 (JOIN 할 때)"))
            for r in RELATIONS:
                print("   " + r)
    finally:
        con.close()


def cmd_sql(st, args):
    if args:
        sql = " ".join(args)
    else:
        p = WS / "scratch.sql"
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("-- 자유 연습장: 아무 쿼리나 써 보고 python play.py sql 로 실행하세요.\n\n"
                         "SELECT * FROM lines;\n", encoding="utf-8")
        sql = read_sql_file(p) or ""
        print(dim(f"(workspace/scratch.sql 실행)"))
    try:
        cols, rows = exec_sql(sql)
    except Exception as e:
        return print(red("SQL 오류: ") + friendly_sql_error(e))
    if cols is None:
        return print("결과 없음")
    print(ui.table(cols, rows, max_rows=30))


def cmd_map(st, args):
    banner()
    for ch, (title, rank) in CHAPTERS.items():
        wk = CH_WEEKEND[ch]
        print(gold(f"\n  {ch}장 {title}") + dim(f"  ({rank} · 목표: 주말{wk} {WEEKENDS[wk]})"))
        for m in [x for x in MISSIONS if x["ch"] == ch]:
            c = st["cleared"].get(m["id"])
            if c:
                how = {"solve": "", "exam_skip": dim(" 면제"), "solution": yellow(" 정답확인"), "relearned": cyan(" 복습완료")}.get(c["how"], "")
                mark = green("✔") + how
            elif current(st) and current(st)["id"] == m["id"]:
                mark = yellow("▶")
            else:
                mark = dim("·")
            title = magenta(m["title"]) if m["exam"] else m["title"]
            print(f"    {mark} {ui.pad(m['id'], 4)} {title} " + dim(f"{m['xp']}XP · {m['skill']}"))
    save(st)


def cmd_exam(st, args):
    m = next_normal(st)
    if not m:
        return print("모든 티켓을 처리했어요.")
    ex = [x for x in MISSIONS if x["ch"] == m["ch"] and x["exam"]]
    if not ex or m["ch"] in (0,):
        return print("이 장에는 승급 시험이 없어요.")
    if m["ch"] == 7:
        return print("전환 심사 PoC는 건너뛸 수 없어요. 차근차근 가요!")
    e = ex[0]
    if e["id"] in st["cleared"]:
        return print("이미 통과한 시험이에요.")
    st["cur"] = {"id": e["id"], "mode": "exam", "fails": 0, "hints": 0, "solution_seen": False}
    save(st)
    print(magenta(f"  🚀 {m['ch']}장 승급 시험에 도전합니다. 통과하면 이 장의 남은 티켓이 면제돼요(보상 50%)."))
    print(dim("  원래 진행으로 돌아가려면 python play.py back"))
    show_ticket(st, e)


def cmd_daily(st, args):
    pool = [BY_ID[k] for k, v in st["cleared"].items() if v.get("how") == "solution" and k in BY_ID]
    if not pool:
        pool = [BY_ID[k] for k, v in st["cleared"].items() if k in BY_ID and BY_ID[k]["id"] != "0-1"]
    if not pool:
        return print("복습할 티켓이 아직 없어요. 먼저 티켓을 처리해 보세요!")
    m = random.choice(pool)
    st["cur"] = {"id": m["id"], "mode": "review", "fails": 0, "hints": 0, "solution_seen": False}
    save(st)
    ensure_file(m, "review", fresh=True)
    print(magenta("  📅 평일 5분 복습: 예전에 푼 티켓을 빈 파일에서 다시 풀어요. 예전 파일은 보지 말고 기억에서!"))
    print(dim("  그만두려면 python play.py back"))
    show_ticket(st, m)


def cmd_back(st, args):
    st["cur"] = {"id": None, "mode": "normal", "fails": 0, "hints": 0, "solution_seen": False}
    save(st)
    m = current(st)
    save(st)
    print("원래 진행으로 돌아왔어요." + (f" 현재 티켓: {m['id']} {m['title']}" if m else ""))


def cmd_reset(st, args):
    ans = input("진행 상황을 전부 지울까요? workspace의 파일은 남아요. (yes 입력): ")
    if ans.strip().lower() == "yes":
        SAVE.unlink(missing_ok=True)
        print("초기화했어요. python play.py 로 다시 시작하세요.")


def cmd_help(st, args):
    banner()
    rows = [
        ("python play.py", "현재 상태와 다음 할 일"),
        ("python play.py ticket", "현재 티켓 내용 보기 + 작성 파일 만들기"),
        ("python play.py run", "작성한 쿼리·함수를 실행해 결과만 보기"),
        ("python play.py check", "채점하기"),
        ("python play.py hint", "힌트 (3단계, 1개당 보상 -20%)"),
        ("python play.py solution", "힌트 3개 후 모범 답안 (보상 20%)"),
        ("python play.py schema [테이블]", "테이블 정의서 / 컬럼 설명 + 샘플"),
        ("python play.py sql \"SELECT ...\"", "자유 쿼리 실행 (인자 없으면 workspace/scratch.sql)"),
        ("python play.py map", "전체 티켓 지도"),
        ("python play.py exam", "현재 장 승급 시험 (통과 시 남은 티켓 면제)"),
        ("python play.py daily", "평일 5분 복습"),
        ("python play.py back", "시험·복습 모드에서 원래 진행으로"),
        ("python play.py reset", "진행 초기화"),
    ]
    for c, d in rows:
        print(f"  {bold(ui.pad(c, 34))} {d}")


COMMANDS = {
    "ticket": cmd_ticket, "t": cmd_ticket, "run": cmd_run, "r": cmd_run, "check": cmd_check, "c": cmd_check,
    "hint": cmd_hint, "h": cmd_hint, "solution": cmd_solution, "schema": cmd_schema, "s": cmd_schema,
    "sql": cmd_sql, "q": cmd_sql, "map": cmd_map, "m": cmd_map, "exam": cmd_exam, "daily": cmd_daily,
    "back": cmd_back, "reset": cmd_reset, "help": cmd_help,
}


def main(argv):
    if sqlite3.sqlite_version_info < (3, 25, 0):
        print(yellow(f"주의: SQLite {sqlite3.sqlite_version} 은 윈도우 함수(5장)를 지원하지 않아요. Python을 최신으로 올려 주세요."))
    if not DB.exists():
        print(dim("고객사 DB를 만드는 중…"))
        dbgen.build(DB)
    st = load()
    if st is None:
        banner()
        print()
        name = input("  이름을 입력하세요 (엔터 = 영식): ").strip() or "영식"
        st = new_state(name)
        save(st)
        m = current(st)
        maybe_intro(st, m)
        save(st)
        show_ticket(st, m)
        return
    cmd = argv[0].lower() if argv else ""
    if not cmd:
        status(st)
        return
    fn = COMMANDS.get(cmd)
    if not fn:
        print(f"모르는 명령이에요: {cmd}")
        cmd_help(st, [])
        return
    fn(st, argv[1:])
