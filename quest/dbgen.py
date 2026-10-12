"""가상 고객사 (주)한결정밀의 3분기(2026.07~09) 공장 데이터베이스를 만든다.

시드가 고정되어 있어서 누가 몇 번 만들어도 같은 데이터가 나온다.
일부 레코드에는 일부러 '데이터 오류'를 심어 두었다 (6장 정합성 검증 미션용).
"""
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

START = date(2026, 7, 1)
END = date(2026, 9, 30)
HOLIDAYS = {"2026-08-17", "2026-09-24", "2026-09-25"}  # 광복절 대체공휴일, 추석 연휴

SCHEMA = """
CREATE TABLE lines (
    line_id     TEXT PRIMARY KEY,
    line_name   TEXT,
    plant       TEXT,
    shifts      INTEGER,
    start_date  TEXT
);
CREATE TABLE products (
    product_id     TEXT PRIMARY KEY,
    product_name   TEXT,
    category       TEXT,
    unit_price     INTEGER,
    std_shift_qty  INTEGER
);
CREATE TABLE equipment (
    equip_id      TEXT PRIMARY KEY,
    equip_name    TEXT,
    line_id       TEXT,
    equip_type    TEXT,
    install_date  TEXT
);
CREATE TABLE workers (
    worker_id    TEXT PRIMARY KEY,
    worker_name  TEXT,
    line_id      TEXT,
    shift        TEXT,
    hire_date    TEXT,
    leave_date   TEXT
);
CREATE TABLE production (
    prod_id       INTEGER PRIMARY KEY,
    prod_date     TEXT,
    line_id       TEXT,
    shift         TEXT,
    product_id    TEXT,
    planned_qty   INTEGER,
    produced_qty  INTEGER,
    good_qty      INTEGER
);
CREATE TABLE defects (
    defect_id    INTEGER PRIMARY KEY,
    prod_id      INTEGER,
    defect_type  TEXT,
    qty          INTEGER
);
CREATE TABLE reason_codes (
    reason_code  TEXT PRIMARY KEY,
    reason_name  TEXT,
    is_planned   INTEGER
);
CREATE TABLE downtime (
    downtime_id  INTEGER PRIMARY KEY,
    equip_id     TEXT,
    start_ts     TEXT,
    end_ts       TEXT,
    reason_code  TEXT,
    is_planned   INTEGER
);
CREATE TABLE sensor_daily (
    equip_id       TEXT,
    reading_date   TEXT,
    avg_temp       REAL,
    max_vibration  REAL,
    PRIMARY KEY (equip_id, reading_date)
);
CREATE TABLE customers (
    customer_id    TEXT PRIMARY KEY,
    customer_name  TEXT,
    region         TEXT,
    grade          TEXT
);
CREATE TABLE orders (
    order_id     TEXT PRIMARY KEY,
    customer_id  TEXT,
    product_id   TEXT,
    order_date   TEXT,
    due_date     TEXT,
    order_qty    INTEGER
);
CREATE TABLE shipments (
    shipment_id  INTEGER PRIMARY KEY,
    order_id     TEXT,
    ship_date    TEXT,
    ship_qty     INTEGER
);
"""

LINES = [
    ("L1", "1라인", "천안공장", 2, "2019-03-01"),
    ("L2", "2라인", "천안공장", 2, "2020-06-01"),
    ("L3", "3라인", "구미공장", 2, "2018-09-01"),
    ("L4", "4라인", "구미공장", 1, "2022-01-10"),
    ("L5", "5라인(신설)", "구미공장", 0, "2026-10-15"),
]

PRODUCTS = [
    ("P01", "고전압 커넥터 A", "커넥터", 12500, 1200),
    ("P02", "고전압 커넥터 B", "커넥터", 15800, 1000),
    ("P03", "신호 커넥터 S", "커넥터", 3200, 3000),
    ("P04", "배터리 하네스 H1", "하네스", 48000, 300),
    ("P05", "배터리 하네스 H2", "하네스", 52000, 250),
    ("P06", "모터 브래킷 M", "브래킷", 7600, 1500),
    ("P07", "방열 브래킷 T", "브래킷", 9100, 1300),
    ("P08", "실링 가스켓 G", "소모품", 1500, 5000),
]
LINE_PRODUCTS = {"L1": ["P01", "P02"], "L2": ["P04", "P05"], "L3": ["P06", "P07"], "L4": ["P08", "P03"]}

EQUIPMENT = [
    ("E11", "사출성형기 #1", "L1", "사출", "2019-03-01"),
    ("E12", "자동조립기 #1", "L1", "조립", "2019-03-01"),
    ("E13", "비전검사기 #1", "L1", "검사", "2023-05-20"),
    ("E21", "전선절단기", "L2", "절단", "2020-06-01"),
    ("E22", "단자압착기", "L2", "압착", "2020-06-01"),
    ("E23", "하네스조립대", "L2", "조립", "2021-02-15"),
    ("E31", "프레스 #1", "L3", "프레스", "2018-09-01"),
    ("E32", "프레스 #2", "L3", "프레스", "2021-11-01"),
    ("E33", "용접로봇", "L3", "용접", "2024-04-01"),
    ("E41", "가스켓성형기", "L4", "사출", "2022-01-10"),
    ("E42", "자동포장기", "L4", "포장", "2025-03-03"),
]

REASONS = [
    ("PM", "예방정비", 1),
    ("SET", "모델교체 셋업", 1),
    ("BRK", "기계고장", 0),
    ("ELC", "전기고장", 0),
    ("MAT", "자재대기", 0),
    ("QLT", "품질이상 정지", 0),
]

CUSTOMERS = [
    ("C01", "가람모빌리티", "수도권", "A"),
    ("C02", "누리전장", "충청", "A"),
    ("C03", "다온오토", "영남", "B"),
    ("C04", "라온배터리", "충청", "A"),
    ("C05", "마루EV", "수도권", "B"),
    ("C06", "바른모터스", "영남", "C"),
    ("C07", "새봄테크", "호남", "B"),
    ("C08", "아라에너지", "호남", "C"),
    ("C09", "자람부품", "수도권", "C"),
    ("C10", "하늘전자", "영남", "B"),
]

SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권"]
GIVEN = ["민준", "서연", "도윤", "지우", "하준", "수아", "예준", "지민", "시우", "하은",
         "주원", "윤서", "지호", "채원", "건우", "다은", "우진", "소율", "현우", "지아",
         "선우", "은서", "연우", "가은", "정우", "유나", "승현", "예린", "태윤", "나연"]

SHIFT_START = {"주간": 8, "야간": 20}
SHIFTS_BY_LINE = {"L1": ["주간", "야간"], "L2": ["주간", "야간"], "L3": ["주간", "야간"], "L4": ["주간"]}


def workdays():
    d = START
    while d <= END:
        if d.weekday() < 5 and d.isoformat() not in HOLIDAYS:
            yield d
        d += timedelta(days=1)


def ts(dt_):
    return dt_.strftime("%Y-%m-%d %H:%M:%S")


def product_for(line_id, d):
    prods = LINE_PRODUCTS[line_id]
    if line_id == "L4":
        return "P03" if d.weekday() == 4 else "P08"
    week = d.isocalendar()[1]
    half = 0 if d.weekday() < 3 else 1
    return prods[(week + half) % len(prods)]


def build(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    rnd = random.Random(20261127)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.executescript(SCHEMA)
    cur.executemany("INSERT INTO lines VALUES (?,?,?,?,?)", LINES)
    cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", PRODUCTS)
    cur.executemany("INSERT INTO equipment VALUES (?,?,?,?,?)", EQUIPMENT)
    cur.executemany("INSERT INTO reason_codes VALUES (?,?,?)", REASONS)
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", CUSTOMERS)

    # ---------------- 작업자 ----------------
    workers = []
    line_cycle = ["L1", "L1", "L2", "L2", "L3", "L3", "L4"]
    for i in range(30):
        wid = f"W{i + 1:03d}"
        name = SURNAMES[i % len(SURNAMES)] + GIVEN[(i * 7) % len(GIVEN)]
        line = None if i in (5, 17, 26) else line_cycle[i % len(line_cycle)]
        shift = "주간" if (line == "L4" or i % 2 == 0) else "야간"
        if line is None:
            shift = "주간"
        hire = date(2015, 1, 1) + timedelta(days=rnd.randint(0, 365 * 11))
        hire = min(hire, date(2026, 6, 30))
        leave = None
        if i in (3, 11, 20, 28):
            leave = (date(2026, 7, 1) + timedelta(days=rnd.randint(0, 80))).isoformat()
        workers.append((wid, name, line, shift, hire.isoformat(), leave))
    cur.executemany("INSERT INTO workers VALUES (?,?,?,?,?,?)", workers)

    days = list(workdays())

    # ---------------- 정지 이력 ----------------
    brk_rate = {"E31": 0.07, "E22": 0.05, "E12": 0.03}
    downtime = []
    failures = []  # (equip_id, date) 비계획 고장(BRK/ELC) 발생일 — 센서 패턴용
    unplanned_min = {}  # (line, date, shift) -> 분

    def add_dt(equip, line, d, shift, minutes_from_start, dur, code, planned):
        start = datetime(d.year, d.month, d.day, SHIFT_START[shift]) + timedelta(minutes=minutes_from_start)
        end = start + timedelta(minutes=dur)
        downtime.append([equip, ts(start), ts(end), code, planned])
        if not planned:
            key = (line, d.isoformat(), shift)
            unplanned_min[key] = unplanned_min.get(key, 0) + dur
            if code in ("BRK", "ELC"):
                failures.append((equip, d))

    prev_product = {}
    for d in days:
        for idx, (eid, _, line, _, _) in enumerate(EQUIPMENT):
            # 격주 월요일 예방정비 (설비마다 엇갈리게)
            if d.weekday() == 0 and (d.isocalendar()[1] + idx) % 2 == 0:
                add_dt(eid, line, d, "주간", rnd.randint(0, 50), rnd.randint(60, 120), "PM", 1)
            for shift in SHIFTS_BY_LINE[line]:
                r = rnd.random()
                if r < brk_rate.get(eid, 0.015):
                    add_dt(eid, line, d, shift, rnd.randint(10, 400), rnd.randint(30, 240), "BRK", 0)
                elif rnd.random() < 0.01:
                    add_dt(eid, line, d, shift, rnd.randint(10, 400), rnd.randint(20, 120), "ELC", 0)
                if rnd.random() < 0.02:
                    add_dt(eid, line, d, shift, rnd.randint(10, 420), rnd.randint(10, 60), "MAT", 0)
                q_rate = 0.06 if (line == "L3" and d.month == 9) else 0.01
                if rnd.random() < q_rate:
                    add_dt(eid, line, d, shift, rnd.randint(10, 420), rnd.randint(15, 90), "QLT", 0)
        # 모델 교체 셋업
        for line in ("L1", "L2", "L3", "L4"):
            p = product_for(line, d)
            if prev_product.get(line) and prev_product[line] != p:
                first_equip = [e[0] for e in EQUIPMENT if e[2] == line][0]
                add_dt(first_equip, line, d, "주간", 0, rnd.randint(20, 45), "SET", 1)
            prev_product[line] = p

    downtime.sort(key=lambda r: (r[1], r[0]))
    # 데이터 오류 심기: 종료시각 누락 1건, 날짜 오타(수일 지속) 2건, 시각 역전 1건
    unplanned_idx = [i for i, r in enumerate(downtime) if r[4] == 0 and r[3] in ("MAT", "QLT")]
    pick = rnd.sample(unplanned_idx, 4)
    downtime[pick[0]][2] = None
    for i in pick[1:3]:
        s = datetime.strptime(downtime[i][1], "%Y-%m-%d %H:%M:%S")
        downtime[i][2] = ts(s + timedelta(days=rnd.choice([2, 3]), minutes=rnd.randint(20, 50)))
    s = datetime.strptime(downtime[pick[3]][1], "%Y-%m-%d %H:%M:%S")
    downtime[pick[3]][2] = ts(s - timedelta(minutes=rnd.randint(30, 90)))
    cur.executemany(
        "INSERT INTO downtime (equip_id, start_ts, end_ts, reason_code, is_planned) VALUES (?,?,?,?,?)",
        downtime,
    )

    # ---------------- 생산 실적 + 불량 ----------------
    defect_rate = {"L1": 0.012, "L2": 0.028, "L3": 0.015, "L4": 0.008}
    types = ["치수불량", "외관불량", "기능불량", "이물혼입"]
    prod_rows, defect_rows = [], []
    pid = 0
    for d in days:
        for line in ("L1", "L2", "L3", "L4"):
            for shift in SHIFTS_BY_LINE[line]:
                pid += 1
                prod = product_for(line, d)
                std = dict((p[0], p[4]) for p in PRODUCTS)[prod]
                planned = std if shift == "주간" else int(round(std * 0.95 / 10.0)) * 10
                eff = min(1.06, max(0.85, rnd.gauss(0.985, 0.03)))
                lost = unplanned_min.get((line, d.isoformat(), shift), 0)
                n_eq = len([e for e in EQUIPMENT if e[2] == line])
                produced = planned * eff - planned * (lost / 480.0) * 0.55
                produced = int(max(planned * 0.5, produced))
                rate = defect_rate[line] * (2.3 if (line == "L3" and d.month == 9) else 1.0)
                dq = int(round(produced * rate * rnd.uniform(0.4, 1.6)))
                good = produced - dq
                prod_rows.append((pid, d.isoformat(), line, shift, prod, planned, produced, good))
                if dq > 0:
                    if line == "L3" and d.month == 9:
                        w = [0.65, 0.2, 0.1, 0.05]
                    elif line == "L2":
                        w = [0.2, 0.25, 0.4, 0.15]
                    else:
                        w = [0.35, 0.35, 0.15, 0.15]
                    counts = {}
                    for t in rnd.choices(types, weights=w, k=dq):
                        counts[t] = counts.get(t, 0) + 1
                    for t in types:
                        if counts.get(t):
                            defect_rows.append([pid, t, counts[t]])
    # 데이터 오류 심기: 불량 상세 합계 ≠ (생산 - 양품) 7건
    by_pid = {}
    for i, r in enumerate(defect_rows):
        by_pid.setdefault(r[0], []).append(i)
    multi = sorted(p for p, idxs in by_pid.items() if len(idxs) >= 2)
    bad = rnd.sample(multi, 7)
    to_delete = set()
    for k, p in enumerate(bad):
        idxs = by_pid[p]
        if k < 4:
            defect_rows[idxs[0]][2] += rnd.randint(2, 6)
        else:
            to_delete.add(idxs[-1])
    defect_rows = [r for i, r in enumerate(defect_rows) if i not in to_delete]
    cur.executemany("INSERT INTO production VALUES (?,?,?,?,?,?,?,?)", prod_rows)
    cur.executemany("INSERT INTO defects (prod_id, defect_type, qty) VALUES (?,?,?)", defect_rows)

    # ---------------- 센서 (가동일에만 기록) ----------------
    fail_idx = {}
    day_index = {d: i for i, d in enumerate(days)}
    for eq, d in failures:
        if d in day_index:
            fail_idx.setdefault(eq, set()).add(day_index[d])
    sensor_rows = []
    for eid, _, line, _, _ in EQUIPMENT:
        base_v = rnd.uniform(1.8, 4.2)
        base_t = rnd.uniform(38, 62)
        mult = [min(1.12, max(0.9, rnd.gauss(1.0, 0.04))) for _ in days]
        for fi in fail_idx.get(eid, ()):
            if fi - 1 >= 0:
                mult[fi - 1] = max(mult[fi - 1], rnd.uniform(1.5, 1.8))
            if fi - 2 >= 0:
                mult[fi - 2] = max(mult[fi - 2], rnd.uniform(1.15, 1.3))
            mult[fi] = max(mult[fi], rnd.uniform(1.3, 1.55))
        # 고장으로 이어지지 않은 오탐 스파이크
        fails = fail_idx.get(eid, set())
        for _ in range(2):
            cand = [i for i in range(10, len(days)) if all(abs(i - f) > 6 for f in fails)]
            if cand:
                i = rnd.choice(cand)
                mult[i] = rnd.uniform(1.45, 1.65)
        for i, d in enumerate(days):
            v = round(base_v * mult[i], 3)
            t = round(base_t * (1 + (mult[i] - 1) * 0.3) + rnd.gauss(0, 0.8), 1)
            sensor_rows.append((eid, d.isoformat(), t, v))
    cur.executemany("INSERT INTO sensor_daily VALUES (?,?,?,?)", sensor_rows)

    # ---------------- 수주 + 출하 ----------------
    orders, ships = [], []
    seq_by_month = {}
    od = date(2026, 6, 15)
    qty_unit = {"P01": 100, "P02": 100, "P03": 500, "P04": 20, "P05": 20, "P06": 100, "P07": 100, "P08": 1000}
    while od <= date(2026, 9, 28):
        if od.weekday() < 5:
            for _ in range(rnd.choice([1, 2, 2, 3])):
                cust = rnd.choice(CUSTOMERS)[0]
                prod = rnd.choice(PRODUCTS)[0]
                key = od.strftime("%y%m")
                seq_by_month[key] = seq_by_month.get(key, 0) + 1
                oid = f"SO{key}-{seq_by_month[key]:03d}"
                due = od + timedelta(days=rnd.randint(7, 21))
                qty = qty_unit[prod] * rnd.randint(2, 15)
                orders.append((oid, cust, prod, od.isoformat(), due.isoformat(), qty))
        od += timedelta(days=1)

    cutoff = END
    for oid, cust, prod, o_s, d_s, qty in orders:
        o, due = date.fromisoformat(o_s), date.fromisoformat(d_s)
        r = rnd.random()
        if due > cutoff:
            outcome = "none" if r < 0.5 else ("partial" if r < 0.8 else "full")
        else:
            outcome = "full" if r < 0.8 else ("partial" if r < 0.92 else "none")
        if outcome == "none":
            continue
        late = rnd.random() < 0.18
        last = due + timedelta(days=rnd.randint(1, 6)) if late else due - timedelta(days=rnd.randint(0, 5))
        last = max(last, o + timedelta(days=2))
        last = min(last, cutoff)
        if outcome == "full":
            if rnd.random() < 0.3 and qty >= 2 * qty_unit[prod]:
                first_q = (qty // 2 // qty_unit[prod]) * qty_unit[prod]
                first_d = max(o + timedelta(days=1), last - timedelta(days=rnd.randint(2, 6)))
                ships.append([oid, first_d.isoformat(), first_q])
                ships.append([oid, last.isoformat(), qty - first_q])
            else:
                ships.append([oid, last.isoformat(), qty])
        else:
            part = max(qty_unit[prod], (qty * rnd.randint(3, 7) // 10 // qty_unit[prod]) * qty_unit[prod])
            if part >= qty:
                part = qty - qty_unit[prod]
            if part > 0:
                ships.append([oid, last.isoformat(), part])
    # 데이터 오류 심기: 주문 수량보다 많이 출하된 주문 2건
    single_full = {}
    order_qty = {o[0]: o[5] for o in orders}
    sums = {}
    for s in ships:
        sums[s[0]] = sums.get(s[0], 0) + s[2]
    full_orders = sorted(o for o, s in sums.items() if s == order_qty[o] and o < "SO2609")
    for oid in rnd.sample(full_orders, 2):
        last_d = max(s[1] for s in ships if s[0] == oid)
        ships.append([oid, last_d, rnd.choice([20, 50, 100])])
    ships.sort(key=lambda s: (s[1], s[0]))
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)
    cur.executemany("INSERT INTO shipments (order_id, ship_date, ship_qty) VALUES (?,?,?)", ships)

    con.commit()
    con.close()
    return path


if __name__ == "__main__":
    p = build(Path(__file__).resolve().parent.parent / "data" / "hangyeol.db")
    print("생성 완료:", p)
