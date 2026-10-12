"""6장(Python 자동화·정합성)과 7장(전환 심사 PoC) 미션.

kind="py" 미션은 workspace의 .py 파일에 solve(...) 함수를 작성한다.
채점기는 같은 인자로 모범 함수(ref)와 사용자 함수를 호출해 결과를 비교한다.
"""
from .missions_sql import YUN, PARK, LEE, CHOI, HAN, OH

JUNG = "정다은 팀장 (세일링스톤 AI-BI팀)"

# ───────────── KPI 정의서 (보스 미션 공용) ─────────────
B1_SQL = """WITH valid AS (
    SELECT e.line_id, strftime('%Y-%m', d.start_ts) AS month,
           (julianday(d.end_ts) - julianday(d.start_ts)) * 1440 AS dur
    FROM downtime d JOIN equipment e ON d.equip_id = e.equip_id
    WHERE d.is_planned = 0 AND d.end_ts IS NOT NULL AND d.end_ts > d.start_ts
      AND (julianday(d.end_ts) - julianday(d.start_ts)) * 1440 <= 1440
),
stop AS (SELECT line_id, month, SUM(dur) AS stop_min FROM valid GROUP BY line_id, month),
eq AS (SELECT line_id, COUNT(*) AS n_equip FROM equipment GROUP BY line_id),
plan AS (SELECT line_id, strftime('%Y-%m', prod_date) AS month, COUNT(*) * 480 AS plan_min
         FROM production GROUP BY line_id, month)
SELECT p.month, p.line_id,
       ROUND((1 - COALESCE(s.stop_min, 0) / eq.n_equip / p.plan_min) * 100, 2) AS availability
FROM plan p JOIN eq ON p.line_id = eq.line_id
LEFT JOIN stop s ON p.line_id = s.line_id AND p.month = s.month
ORDER BY p.month, p.line_id"""

B2_SQL = """WITH valid AS (
    SELECT e.line_id, strftime('%Y-%m', d.start_ts) AS month,
           (julianday(d.end_ts) - julianday(d.start_ts)) * 1440 AS dur
    FROM downtime d JOIN equipment e ON d.equip_id = e.equip_id
    WHERE d.is_planned = 0 AND d.end_ts IS NOT NULL AND d.end_ts > d.start_ts
      AND (julianday(d.end_ts) - julianday(d.start_ts)) * 1440 <= 1440
),
stop AS (SELECT line_id, month, SUM(dur) AS stop_min FROM valid GROUP BY line_id, month),
eq AS (SELECT line_id, COUNT(*) AS n_equip FROM equipment GROUP BY line_id),
prod AS (SELECT line_id, strftime('%Y-%m', prod_date) AS month, COUNT(*) * 480 AS plan_min,
                ROUND((1 - SUM(good_qty) * 1.0 / SUM(produced_qty)) * 100, 2) AS defect_rate,
                ROUND(SUM(produced_qty) * 100.0 / SUM(planned_qty), 2) AS achieve_rate
         FROM production GROUP BY line_id, month)
SELECT p.month, p.line_id,
       ROUND((1 - COALESCE(s.stop_min, 0) / eq.n_equip / p.plan_min) * 100, 2) AS availability,
       p.defect_rate, p.achieve_rate
FROM prod p JOIN eq ON p.line_id = eq.line_id
LEFT JOIN stop s ON p.line_id = s.line_id AND p.month = s.month
ORDER BY p.month, p.line_id"""

OTD_SQL = """WITH s AS (SELECT order_id, SUM(ship_qty) AS shipped, MAX(ship_date) AS last_ship
           FROM shipments GROUP BY order_id)
SELECT ROUND(SUM(CASE WHEN s.shipped >= o.order_qty AND s.last_ship <= o.due_date THEN 1 ELSE 0 END)
             * 100.0 / COUNT(*), 2) AS otd
FROM orders o LEFT JOIN s ON o.order_id = s.order_id
WHERE strftime('%Y-%m', o.due_date) = ?"""

KPI_DOC = (
    "[KPI 정의서 v1]\n"
    "① 계획 가동시간(분) = 해당 라인·월의 생산실적(production) 행 수 × 480  (교대 1회 = 480분)\n"
    "② 비계획 정지시간(분) = 해당 라인 설비들의 비계획 정지(is_planned = 0) 시간 합 ÷ 그 라인의 설비 대수\n"
    "   · 정지의 월은 start_ts 기준\n"
    "   · 데이터 오류 레코드는 제외: end_ts 없음, end_ts ≤ start_ts, 지속 1440분 초과\n"
    "③ 가동률(%) = (1 - ② ÷ ①) × 100\n"
    "④ 불량률(%) = (1 - 양품 합 ÷ 생산 합) × 100\n"
    "⑤ 계획달성률(%) = 생산 합 ÷ 계획 합 × 100\n"
    "⑥ 납기준수율(%) = 납기일이 해당 월인 주문 중 '주문수량 이상 출하 완료 & 마지막 출하일 ≤ 납기일' 비율\n"
    "※ 모든 비율은 소수 둘째 자리"
)


def _pd():
    import pandas as pd
    return pd


# ───────────── 모범 함수 ─────────────
def ref_6_1(conn):
    pd = _pd()
    return pd.read_sql("SELECT line_id, SUM(produced_qty) AS total_produced FROM production "
                       "GROUP BY line_id ORDER BY line_id", conn)


def ref_6_2(conn):
    pd = _pd()
    df = pd.read_sql("SELECT prod_date, line_id, produced_qty, good_qty FROM production", conn)
    df["month"] = df["prod_date"].str[:7]
    g = df.groupby(["month", "line_id"])[["produced_qty", "good_qty"]].sum()
    g["defect_rate"] = ((1 - g["good_qty"] / g["produced_qty"]) * 100).round(2)
    return g["defect_rate"].unstack("line_id")


def ref_6_3(conn):
    pd = _pd()
    p = pd.read_sql("SELECT prod_id, produced_qty - good_qty AS dq FROM production", conn)
    d = pd.read_sql("SELECT prod_id, SUM(qty) AS dsum FROM defects GROUP BY prod_id", conn)
    m = p.merge(d, on="prod_id", how="left")
    m["dsum"] = m["dsum"].fillna(0)
    return sorted(int(x) for x in m.loc[m["dq"] != m["dsum"], "prod_id"])


def ref_6_4(conn):
    pd = _pd()
    o = pd.read_sql("SELECT order_id, order_qty FROM orders", conn)
    s = pd.read_sql("SELECT order_id, SUM(ship_qty) AS shipped FROM shipments GROUP BY order_id", conn)
    m = o.merge(s, on="order_id", how="left")
    return sorted(m.loc[m["shipped"] > m["order_qty"], "order_id"].tolist())


def ref_6_5(conn):
    pd = _pd()
    d = pd.read_sql("SELECT downtime_id, start_ts, end_ts FROM downtime", conn)
    dur = (pd.to_datetime(d["end_ts"]) - pd.to_datetime(d["start_ts"])).dt.total_seconds() / 60
    bad = d["end_ts"].isna() | (dur <= 0) | (dur > 1440)
    return sorted(int(x) for x in d.loc[bad, "downtime_id"])


def ref_6_6(conn, month):
    pd = _pd()
    return pd.read_sql("SELECT line_id, ROUND(SUM(produced_qty) * 100.0 / SUM(planned_qty), 2) AS achieve_rate "
                       "FROM production WHERE strftime('%Y-%m', prod_date) = ? "
                       "GROUP BY line_id ORDER BY line_id", conn, params=(month,))


def ref_6_7(conn, ratio):
    pd = _pd()
    s = pd.read_sql("SELECT equip_id, reading_date, max_vibration FROM sensor_daily "
                    "ORDER BY equip_id, reading_date", conn)
    s["prev7"] = s.groupby("equip_id")["max_vibration"].transform(lambda x: x.rolling(7).mean().shift(1))
    hit = s[s["prev7"].notna() & (s["max_vibration"] >= s["prev7"] * ratio)]
    return sorted(zip(hit["equip_id"], hit["reading_date"]))


def ref_b3(conn, month):
    pd = _pd()
    avail = pd.read_sql(B1_SQL, conn)
    a = avail.loc[avail["month"] == month, "availability"].mean()
    p = pd.read_sql("SELECT SUM(produced_qty) AS pq, SUM(good_qty) AS gq, SUM(planned_qty) AS plq "
                    "FROM production WHERE strftime('%Y-%m', prod_date) = ?", conn, params=(month,))
    pq, gq, plq = float(p["pq"][0]), float(p["gq"][0]), float(p["plq"][0])
    otd = pd.read_sql(OTD_SQL, conn, params=(month,))["otd"][0]
    return {
        "가동률": round(float(a), 2),
        "불량률": round((1 - gq / pq) * 100, 2),
        "계획달성률": round(pq / plq * 100, 2),
        "납기준수율": round(float(otd), 2),
    }


PY_TEMPLATE_HEAD = "import pandas as pd\n\n\n"

PY_MISSIONS = [
    # ───────────── 6장 Python 자동화 · 정합성 ─────────────
    dict(
        id="6-1", ch=6, kind="py", title="쿼리 결과를 파이썬으로", frm=YUN, xp=30,
        msg="이제 쿼리 결과를 파이썬으로 받아서 자동화할 차례예요. pandas.read_sql로 라인별 총 생산량을 "
            "DataFrame으로 돌려주는 함수를 만들어 볼래요?",
        out="DataFrame — 컬럼 [line_id, total_produced], line_id 오름차순",
        sig="solve(conn)", calls=[()], cmp="df", ref=ref_6_1,
        hints=["pd.read_sql(쿼리문자열, conn) 이 DataFrame을 돌려줘요.",
               "쿼리는 2장에서 이미 써 봤어요(2-2).",
               "return pd.read_sql(\"SELECT line_id, SUM(produced_qty) AS total_produced FROM production GROUP BY line_id ORDER BY line_id\", conn)"],
        skill="pandas.read_sql",
        tip="SQL로 줄이고(집계) → pandas로 다듬는(가공·시각화) 분업이 실무 기본이에요. 원본 전체를 파이썬으로 끌어오면 느려요.",
    ),
    dict(
        id="6-2", ch=6, kind="py", title="월 × 라인 불량률 표", frm=LEE, xp=30,
        msg="월(행) × 라인(열) 불량률(%) 표가 필요해요. 엑셀에 바로 붙일 수 있게요.",
        out="DataFrame — 인덱스: 월(YYYY-MM, 오름차순), 컬럼: L1, L2, L3, L4, 값: 불량률(%) 소수 둘째 자리",
        sig="solve(conn)", calls=[()], cmp="df", ref=ref_6_2,
        hints=["원자료를 read_sql로 가져와 월 컬럼을 만들어요: df['prod_date'].str[:7]",
               "groupby(['month', 'line_id'])로 합계 → 불량률 계산 → 피벗",
               "g = df.groupby(['month','line_id'])[['produced_qty','good_qty']].sum(); rate = ((1 - g.good_qty / g.produced_qty) * 100).round(2); return rate.unstack('line_id')"],
        skill="groupby · pivot(unstack)",
        tip="SQL의 조건부 집계(4-4)와 pandas의 unstack/pivot_table은 같은 일을 해요. 상황에 따라 편한 쪽을 쓰면 돼요.",
    ),
    dict(
        id="6-3", ch=6, kind="py", title="[정합성 ①] 불량 상세 vs 실적", frm=LEE, xp=30,
        msg="큰일이에요. 불량 상세(defects)를 다 더한 값이 생산 실적의 불량수량(생산 - 양품)이랑 안 맞는 실적이 "
            "있다는 제보가 들어왔어요. 어떤 prod_id인지 찾아 줘요.",
        out="list[int] — 안 맞는 prod_id, 오름차순 (불량 상세가 아예 없으면 합계 0으로 간주)",
        sig="solve(conn)", calls=[()], cmp="list", ref=ref_6_3,
        hints=["production의 (produced_qty - good_qty)와 defects를 prod_id별로 합친 값을 비교해요.",
               "defects가 없는 실적도 있으니 how='left'로 merge하고, 빈 값은 0으로(fillna).",
               "m = p.merge(d, on='prod_id', how='left'); m['dsum'] = m['dsum'].fillna(0); return sorted(m.loc[m.dq != m.dsum, 'prod_id'].tolist())"],
        skill="merge · 정합성 검증",
        tip="2-7에서 '언젠가 확인할 일'이라고 했던 게 이거예요. BI 프로젝트 초반 2주는 보통 이런 검증으로 시작해요. 숫자를 믿을 수 있어야 대시보드도 의미가 있어요.",
    ),
    dict(
        id="6-4", ch=6, kind="py", title="[정합성 ②] 과출하 주문", frm=CHOI, xp=30,
        msg="출하 합계가 주문수량보다 많은 주문이 있대요. 시스템 입력 실수 같은데, 주문번호 좀 찾아 줘요.",
        out="list[str] — 과출하 order_id, 오름차순",
        sig="solve(conn)", calls=[()], cmp="list", ref=ref_6_4,
        hints=["주문별 출하 합계를 먼저 만들어요(SQL GROUP BY든 pandas groupby든).",
               "orders와 합쳐서 shipped > order_qty 인 것만.",
               "SQL 한 방도 가능: SELECT o.order_id FROM orders o JOIN (SELECT order_id, SUM(ship_qty) AS s FROM shipments GROUP BY order_id) x ON ... WHERE x.s > o.order_qty"],
        skill="사전 집계 + 비교 검증",
        tip="검증 결과는 '고객사에 확인 요청할 목록'으로 정리해 공유하는 게 다음 단계예요. 고치는 건 고객사 현업의 권한이에요.",
    ),
    dict(
        id="6-5", ch=6, kind="py", title="[정합성 ③] 정지 이력 이상 레코드", frm=HAN, xp=30,
        msg="정지 이력에 이상한 기록이 섞여 있대요. 종료시각이 없거나, 종료가 시작보다 이르거나 같거나, "
            "24시간(1440분)을 넘는 건 전부 찾아 줘요.",
        out="list[int] — 이상 downtime_id, 오름차순",
        sig="solve(conn)", calls=[()], cmp="list", ref=ref_6_5,
        hints=["pd.to_datetime으로 시각을 바꾸면 빼기가 돼요.",
               "(end - start).dt.total_seconds() / 60 = 분. 결측은 isna()로.",
               "bad = d.end_ts.isna() | (dur <= 0) | (dur > 1440)"],
        skill="결측·이상치 탐지",
        tip="3-7, 3-9에서 뽑은 정지시간이 사실 이 레코드들 때문에 부풀려져 있었어요. 집계 전에 검증부터 돌리는 게 순서예요. 보스 미션에서 이걸 제외하게 돼요.",
    ),
    dict(
        id="6-6", ch=6, kind="py", title="월만 바꾸면 되는 함수", frm=PARK, xp=30,
        msg="매달 라인별 계획달성률을 뽑는데, 월만 바꿔 넣으면 되게 함수로 만들어 줘요. 다음 달부터는 제가 직접 돌릴게요.",
        out="solve(conn, month) — month는 'YYYY-MM'. DataFrame [line_id, achieve_rate(%, 소수 둘째 자리)], line_id 오름차순",
        sig="solve(conn, month)", calls=[("2026-07",), ("2026-09",)], cmp="df", ref=ref_6_6,
        hints=["쿼리에 값을 넣을 땐 f-string 말고 파라미터: pd.read_sql(sql, conn, params=(month,))",
               "SQL 안에는 물음표: WHERE strftime('%Y-%m', prod_date) = ?",
               "pd.read_sql(\"SELECT line_id, ROUND(SUM(produced_qty) * 100.0 / SUM(planned_qty), 2) AS achieve_rate FROM production WHERE strftime('%Y-%m', prod_date) = ? GROUP BY line_id ORDER BY line_id\", conn, params=(month,))"],
        skill="파라미터 쿼리 · 함수화",
        tip="f-string으로 SQL을 조립하면 SQL 인젝션 위험이 있어요. 고객사 시스템에 붙는 코드라면 리뷰에서 바로 지적받아요. 파라미터 바인딩이 정답이에요.",
    ),
    dict(
        id="6-7", ch=6, kind="py", exam=True, title="[승급 시험] 진동 이상 감지 함수", frm=HAN, xp=70,
        msg="5-8 규칙을 설비보전팀이 매일 돌릴 수 있게 함수로 만들어 줘요. 기준 배수(ratio)는 바꿀 수 있어야 해요. "
            "전 설비·전 기간 대상, 최대진동이 직전 7개 측정값 평균(당일 제외)의 ratio배 이상인 날. "
            "직전 측정값이 7개가 안 되는 초반 날짜는 제외.",
        out="solve(conn, ratio) — list[tuple] [(equip_id, reading_date), ...] 오름차순",
        sig="solve(conn, ratio)", calls=[(1.3,), (1.5,)], cmp="list", ref=ref_6_7,
        hints=["설비별로 정렬한 뒤 groupby('equip_id')['max_vibration']에 rolling(7).mean()",
               "당일 제외 = rolling 결과를 shift(1). 처음 7개는 NaN이 돼서 자연히 빠져요.",
               "s['prev7'] = s.groupby('equip_id')['max_vibration'].transform(lambda x: x.rolling(7).mean().shift(1)); hit = s[s.prev7.notna() & (s.max_vibration >= s.prev7 * ratio)]; return sorted(zip(hit.equip_id, hit.reading_date))"],
        skill="rolling · shift · 함수화 (예지보전 자동화)",
        tip="이제 이 함수를 스케줄러(cron, n8n)에 걸고 결과를 메일·슬랙으로 보내면 '예지보전 알림 PoC'가 돼요. 부트캠프 n8n 과정과 바로 연결돼요.",
    ),
    # ───────────── 7장 전환 심사 PoC ─────────────
    dict(
        id="B-1", ch=7, kind="sql", title="[PoC 1/3] 라인·월 가동률", frm=OH, xp=80,
        msg="경영진 보고용 KPI 대시보드 PoC를 세일링스톤에 맡기기로 했어요. 첫 번째로 라인·월별 가동률이요. "
            "정의는 아래 KPI 정의서 ①~③ 그대로 해 주세요.\n\n" + KPI_DOC,
        out="month, line_id, availability (%, 소수 둘째 자리) — L1~L4 × 7~9월 = 12행",
        order="month, line_id 오름차순",
        sol=B1_SQL,
        hints=["CTE를 단계별로: ① 계획시간(plan) ② 유효한 정지만(valid) → 라인·월 합계(stop) ③ 라인별 설비 수(eq)",
               "정지가 없는 라인·월도 있을 수 있어요 → plan 기준 LEFT JOIN + COALESCE(stop_min, 0)",
               "SELECT p.month, p.line_id, ROUND((1 - COALESCE(s.stop_min, 0) / eq.n_equip / p.plan_min) * 100, 2) AS availability FROM plan p JOIN eq ON ... LEFT JOIN stop s ON p.line_id = s.line_id AND p.month = s.month"],
        skill="다단계 CTE · KPI 정의 구현",
        tip="정의서를 문장 단위로 CTE에 1:1 대응시키면, 고객이 '이 숫자 어떻게 나온 거예요?'라고 물을 때 바로 설명할 수 있어요.",
    ),
    dict(
        id="B-2", ch=7, kind="sql", title="[PoC 2/3] 라인·월 종합 KPI 표", frm=OH, xp=80,
        msg="좋아요. 그 가동률 옆에 불량률(④)이랑 계획달성률(⑤)을 붙여서 라인·월 종합표로 만들어 주세요. "
            "이게 대시보드 메인 화면이 될 거예요.\n\n" + KPI_DOC,
        out="month, line_id, availability, defect_rate, achieve_rate (모두 %, 소수 둘째 자리) — 12행",
        order="month, line_id 오름차순",
        sol=B2_SQL,
        hints=["B-1 쿼리의 plan CTE를 '생산 집계 CTE'로 확장하면 돼요.",
               "같은 GROUP BY(line_id, month)에서 계획시간, 불량률, 달성률을 한 번에 계산할 수 있어요.",
               "prod AS (SELECT line_id, strftime('%Y-%m', prod_date) AS month, COUNT(*) * 480 AS plan_min, ROUND((1 - SUM(good_qty) * 1.0 / SUM(produced_qty)) * 100, 2) AS defect_rate, ROUND(SUM(produced_qty) * 100.0 / SUM(planned_qty), 2) AS achieve_rate FROM production GROUP BY line_id, month)"],
        skill="KPI 마트 쿼리",
        tip="이런 '라인 × 월 × KPI' 테이블을 데이터 마트라고 해요. Tableau나 Power BI는 이 마트를 읽어서 그림만 그려요. 진짜 일은 이 쿼리에 있어요.",
    ),
    dict(
        id="B-3", ch=7, kind="py", exam=True, title="[PoC 3/3] 경영진 월간 리포트 함수", frm=OH, xp=120,
        msg="마지막이에요. 월만 넣으면 전사 KPI 네 개를 돌려주는 함수를 만들어 주세요. 이걸 매달 경영회의 자료에 씁니다.\n"
            "· 가동률: 해당 월 L1~L4 가동률(B-1)의 단순 평균\n"
            "· 불량률·계획달성률: 해당 월 전사 합계 기준 (④, ⑤)\n"
            "· 납기준수율: 납기일이 해당 월인 주문 기준 (⑥)\n\n" + KPI_DOC,
        out="solve(conn, month) — dict {'가동률': x, '불량률': x, '계획달성률': x, '납기준수율': x} (모두 %, 소수 둘째 자리)",
        sig="solve(conn, month)", calls=[("2026-08",), ("2026-09",)], cmp="dict", ref=ref_b3,
        hints=["지금까지 만든 쿼리들을 재사용하세요. B-1 쿼리 결과에서 해당 월만 골라 평균.",
               "전사 합계는 SUM(produced_qty), SUM(good_qty), SUM(planned_qty)를 해당 월로 한 번에.",
               "납기준수율은 4-6 쿼리에 WHERE strftime('%Y-%m', o.due_date) = ? 를 붙이고 params=(month,)"],
        skill="KPI 자동 리포트 (SQL + Python 통합)",
        tip="축하해요. 이게 세일링스톤 AI-BI 엔지니어 일의 축소판이에요. 고객 요구 → KPI 정의 → SQL 로직 → 자동화. 면접에서 이 흐름을 그대로 설명하세요.",
    ),
]
