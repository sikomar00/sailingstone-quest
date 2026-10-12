"""0~5장: SQL 미션.

각 미션의 정답 결과는 sol(모범 쿼리)을 실제 DB에 돌려서 만든다.
traps: 자주 하는 실수 쿼리. 사용자의 결과가 이 결과와 같으면 맞춤 피드백을 준다.
"""

YUN = "윤서진 선임 (세일링스톤, 사수)"
PARK = "박정훈 생산팀장 (한결정밀)"
LEE = "이미경 품질팀장 (한결정밀)"
CHOI = "최동욱 영업팀장 (한결정밀)"
HAN = "한상철 설비보전 파트장 (한결정밀)"
OH = "오정민 경영기획실장 (한결정밀)"

_DUR = "(julianday(d.end_ts) - julianday(d.start_ts)) * 1440"

SQL_MISSIONS = [
    # ───────────── 0장 온보딩 ─────────────
    dict(
        id="0-1", ch=0, title="첫 출근: DB 접속 확인", frm=YUN, xp=5,
        msg="영식 님, 오늘부터 한결정밀 프로젝트예요. 고객사 DB가 잘 붙었는지 확인할 겸 "
            "제품 마스터(products) 테이블 전체를 조회해 볼래요? 파일에 쿼리 쓰고 저장한 다음 "
            "터미널에서 python play.py check 하면 돼요.",
        out="products 테이블의 모든 컬럼, 모든 행",
        order=None,
        sol="SELECT * FROM products",
        hints=["모든 컬럼은 * 로 표현해요.",
               "기본 형태는 SELECT 컬럼 FROM 테이블 이에요.",
               "SELECT * FROM products;"],
        skill="SELECT *",
        tip="SELECT * 은 탐색할 때만 쓰세요. 리포트용 쿼리에는 필요한 컬럼만 적는 게 성능과 가독성 모두에 좋아요.",
    ),
    # ───────────── 1장 기본 조회 ─────────────
    dict(
        id="1-1", ch=1, title="견적용 단가표", frm=CHOI, xp=10,
        msg="견적 낼 때 쓰게 제품명이랑 단가만 비싼 순으로 뽑아 줄 수 있어요?",
        out="product_name, unit_price",
        order="unit_price 내림차순",
        sol="SELECT product_name, unit_price FROM products ORDER BY unit_price DESC",
        hints=["필요한 컬럼만 쉼표로 나열하면 돼요.",
               "정렬은 ORDER BY, 내림차순은 DESC.",
               "SELECT product_name, unit_price FROM products ORDER BY ... DESC;"],
        skill="컬럼 선택 · ORDER BY",
        tip="ORDER BY 없는 결과의 순서는 DB가 보장하지 않아요. 순서가 의미 있는 리포트는 반드시 ORDER BY.",
    ),
    dict(
        id="1-2", ch=1, title="1라인 설비 목록", frm=HAN, xp=10,
        msg="1라인(L1)에 있는 설비 목록 좀 보내 줘요. 설비번호 순으로요.",
        out="equip_id, equip_name, equip_type",
        order="equip_id 오름차순",
        sol="SELECT equip_id, equip_name, equip_type FROM equipment WHERE line_id = 'L1' ORDER BY equip_id",
        hints=["행을 거르는 조건은 WHERE.",
               "문자열 값은 작은따옴표로: 'L1'",
               "SELECT ... FROM equipment WHERE line_id = 'L1' ORDER BY equip_id;"],
        skill="WHERE",
        tip="SQL에서 문자열은 작은따옴표예요. 큰따옴표는 원래 컬럼·테이블 이름용이라 DB마다 다르게 동작할 수 있어요.",
    ),
    dict(
        id="1-3", ch=1, title="8월 5일 계획 미달 실적", frm=PARK, xp=10,
        msg="8월 5일 실적 중에 계획보다 덜 만든 교대가 있죠? 라인, 교대, 제품, 계획·실적 수량이랑 "
            "부족 수량까지 보여 줘요.",
        out="line_id, shift, product_id, planned_qty, produced_qty, short_qty (= planned_qty - produced_qty)",
        order=None,
        sol="SELECT line_id, shift, product_id, planned_qty, produced_qty, planned_qty - produced_qty AS short_qty "
            "FROM production WHERE prod_date = '2026-08-05' AND produced_qty < planned_qty",
        hints=["조건 두 개는 AND로 이어요. 날짜도 문자열: '2026-08-05'",
               "컬럼끼리 비교·계산도 돼요: produced_qty < planned_qty",
               "계산 컬럼에 이름 붙이기: planned_qty - produced_qty AS short_qty"],
        skill="AND 조건 · 계산 컬럼 · AS",
        tip="이 DB의 날짜는 'YYYY-MM-DD' 문자열이에요. 이 형식이면 문자열 비교·정렬 순서가 날짜 순서와 같아요.",
    ),
    dict(
        id="1-4", ch=1, title="커넥터 제품만", frm=CHOI, xp=10,
        msg="커넥터 제품만 따로 보고 싶어요. 이름에 '커넥터'가 들어간 거요.",
        out="product_id, product_name",
        order=None,
        sol="SELECT product_id, product_name FROM products WHERE product_name LIKE '%커넥터%'",
        hints=["부분 일치는 LIKE.",
               "%는 '아무 글자 0개 이상'이에요.",
               "WHERE product_name LIKE '%커넥터%'"],
        skill="LIKE 패턴 검색",
        tip="LIKE '%키워드%'는 앞에 %가 붙어 인덱스를 못 써서 큰 테이블에선 느려요. category 같은 분류 컬럼이 있으면 그걸 쓰는 게 정석이에요.",
    ),
    dict(
        id="1-5", ch=1, title="9월 고장 이력", frm=HAN, xp=10,
        msg="9월에 발생한 기계고장(BRK)이랑 전기고장(ELC)만 시간순으로 뽑아 줘요.",
        out="downtime_id, equip_id, start_ts, reason_code",
        order="start_ts 오름차순 (같으면 downtime_id)",
        sol="SELECT downtime_id, equip_id, start_ts, reason_code FROM downtime "
            "WHERE reason_code IN ('BRK', 'ELC') AND start_ts >= '2026-09-01' ORDER BY start_ts, downtime_id",
        hints=["여러 값 중 하나는 IN ('A', 'B').",
               "start_ts는 'YYYY-MM-DD HH:MM:SS' 문자열이라 start_ts >= '2026-09-01' 로 범위를 걸 수 있어요.",
               "WHERE reason_code IN ('BRK', 'ELC') AND start_ts >= '2026-09-01' ORDER BY start_ts, downtime_id"],
        skill="IN · 범위 조건",
        tip="start_ts LIKE '2026-09%' 도 되지만, 범위 조건(>=, <)이 인덱스를 쓸 수 있어서 실무에선 더 선호돼요.",
    ),
    dict(
        id="1-6", ch=1, title="라인 미배정 작업자", frm=YUN, xp=10,
        msg="고객사 인사팀이 그러는데 작업자 테이블에 라인이 비어 있는 사람이 있대요. 누군지 확인해 줄래요?",
        out="worker_id, worker_name",
        order=None,
        sol="SELECT worker_id, worker_name FROM workers WHERE line_id IS NULL",
        hints=["'비어 있다' = NULL 이에요.",
               "line_id = NULL 은 항상 거짓이에요. NULL 전용 비교가 따로 있어요.",
               "WHERE line_id IS NULL"],
        skill="IS NULL",
        traps=[dict(sql="SELECT worker_id, worker_name FROM workers WHERE line_id = NULL",
                    msg="결과가 0행이죠? NULL은 '값 없음'이라 = 로 비교하면 항상 거짓이에요. IS NULL을 쓰세요.")],
        tip="NULL은 비교·집계·조인에서 전부 특별하게 동작해요. 실무 숫자 버그의 단골 원인이니 계속 의식하세요.",
    ),
    dict(
        id="1-7", ch=1, title="고객사 지역", frm=CHOI, xp=10,
        msg="우리 고객사들 지역이 어디어디예요? 중복 없이요.",
        out="region",
        order=None,
        sol="SELECT DISTINCT region FROM customers",
        hints=["중복 제거 키워드가 있어요.",
               "SELECT 바로 뒤에 붙여요.",
               "SELECT DISTINCT region FROM customers;"],
        skill="DISTINCT",
        tip="DISTINCT는 중복 제거만 해요. '지역별 고객 수'처럼 세는 건 다음 장 GROUP BY의 일이에요.",
    ),
    dict(
        id="1-8", ch=1, exam=True, title="[승급 시험] 9월 둘째 주 야간 TOP 5", frm=PARK, xp=30,
        msg="9월 7일~11일 야간조 실적 중에 생산량 상위 5건만요. 날짜, 라인, 제품, 생산량, "
            "불량수량(생산 - 양품)까지.",
        out="prod_date, line_id, product_id, produced_qty, defect_qty (= produced_qty - good_qty)",
        order="produced_qty 내림차순 (같으면 prod_date 오름차순), 상위 5행",
        sol="SELECT prod_date, line_id, product_id, produced_qty, produced_qty - good_qty AS defect_qty "
            "FROM production WHERE shift = '야간' AND prod_date BETWEEN '2026-09-07' AND '2026-09-11' "
            "ORDER BY produced_qty DESC, prod_date LIMIT 5",
        hints=["범위는 BETWEEN A AND B (양 끝 포함).",
               "상위 N개는 ORDER BY ... DESC 뒤에 LIMIT N.",
               "WHERE shift = '야간' AND prod_date BETWEEN '2026-09-07' AND '2026-09-11' ORDER BY produced_qty DESC, prod_date LIMIT 5"],
        skill="BETWEEN · LIMIT (Top-N)",
        tip="Top-N 요청을 받으면 '5등이 동률이면 어떻게 할까요?'를 먼저 물어보세요. 이 질문을 하는 신입은 눈에 띄어요.",
    ),
    # ───────────── 2장 집계 ─────────────
    dict(
        id="2-1", ch=2, title="3분기 총 생산량", frm=PARK, xp=15,
        msg="3분기 전체 생산량이랑 양품 수량, 숫자 두 개만 딱 주세요.",
        out="total_produced, total_good",
        order=None,
        sol="SELECT SUM(produced_qty) AS total_produced, SUM(good_qty) AS total_good FROM production",
        hints=["합계 함수는 SUM.",
               "집계 함수 여러 개를 쉼표로 나란히 쓸 수 있어요.",
               "SELECT SUM(produced_qty) AS total_produced, SUM(good_qty) AS total_good FROM production;"],
        skill="SUM",
        tip="집계 결과는 행 전체가 한 줄로 접혀요. 다음 미션부터는 '무엇별로' 접을지 정하게 돼요.",
    ),
    dict(
        id="2-2", ch=2, title="라인별 생산량", frm=PARK, xp=15,
        msg="그걸 라인별로 나눠서 생산량 합계만 보여 줘요.",
        out="line_id, total_produced",
        order="line_id 오름차순",
        sol="SELECT line_id, SUM(produced_qty) AS total_produced FROM production GROUP BY line_id ORDER BY line_id",
        hints=["'~별로' = GROUP BY.",
               "SELECT에 쓴 일반 컬럼은 GROUP BY에도 있어야 해요.",
               "SELECT line_id, SUM(produced_qty) AS total_produced FROM production GROUP BY line_id ORDER BY line_id;"],
        skill="GROUP BY",
        tip="요청 문장에서 '~별'이 나오면 그게 GROUP BY 컬럼이에요. 요구사항을 쿼리로 번역하는 첫 번째 규칙.",
    ),
    dict(
        id="2-3", ch=2, title="라인별 불량률", frm=LEE, xp=15,
        msg="라인별 불량률(%)이요. 불량률 = (1 - 양품합계 / 생산합계) × 100, 소수 둘째 자리까지. 높은 순으로요.",
        out="line_id, defect_rate",
        order="defect_rate 내림차순",
        sol="SELECT line_id, ROUND((1 - SUM(good_qty) * 1.0 / SUM(produced_qty)) * 100, 2) AS defect_rate "
            "FROM production GROUP BY line_id ORDER BY defect_rate DESC",
        hints=["ROUND(값, 2)로 소수 둘째 자리.",
               "결과가 이상하게 0이나 100만 나온다면? SQLite에서 정수 / 정수 = 정수예요.",
               "SUM(good_qty) * 1.0 / SUM(produced_qty) 처럼 한쪽을 실수로 만들어요."],
        skill="비율 계산 · 정수 나눗셈 회피",
        traps=[dict(sql="SELECT line_id, ROUND((1 - SUM(good_qty) / SUM(produced_qty)) * 100, 2) AS defect_rate "
                        "FROM production GROUP BY line_id ORDER BY defect_rate DESC",
                    msg="전부 100이 나왔죠? 정수 / 정수는 정수 나눗셈이라 0이 돼요. 한쪽에 * 1.0 을 곱해 실수로 만드세요.")],
        tip="정수 나눗셈은 SQLite·PostgreSQL·SQL Server에서 다 일어나요(MySQL·Oracle은 아님). 비율 계산엔 습관적으로 * 1.0.",
    ),
    dict(
        id="2-4", ch=2, title="월별 생산량 추이", frm=OH, xp=15,
        msg="임원 보고용으로 월별(YYYY-MM) 생산량 합계가 필요해요.",
        out="month (예: 2026-07), total_produced",
        order="month 오름차순",
        sol="SELECT strftime('%Y-%m', prod_date) AS month, SUM(produced_qty) AS total_produced "
            "FROM production GROUP BY month ORDER BY month",
        hints=["날짜에서 연-월만 뽑아 그걸로 묶으면 돼요.",
               "SQLite: strftime('%Y-%m', prod_date) 또는 substr(prod_date, 1, 7)",
               "SELECT strftime('%Y-%m', prod_date) AS month, SUM(produced_qty) ... GROUP BY month ORDER BY month;"],
        skill="날짜 함수 · 월별 집계",
        tip="날짜 함수는 DB마다 달라요(SQLite strftime, MySQL DATE_FORMAT, Oracle TO_CHAR). 고객사 DB 종류부터 확인하는 게 습관이 돼야 해요.",
    ),
    dict(
        id="2-5", ch=2, title="설비 유형별 대수", frm=HAN, xp=15,
        msg="설비 유형별로 몇 대씩 있어요? 많은 순, 같으면 유형 이름 순으로요.",
        out="equip_type, equip_cnt",
        order="equip_cnt 내림차순, equip_type 오름차순",
        sol="SELECT equip_type, COUNT(*) AS equip_cnt FROM equipment GROUP BY equip_type "
            "ORDER BY equip_cnt DESC, equip_type",
        hints=["행 개수는 COUNT(*).",
               "정렬 기준이 두 개면 ORDER BY a DESC, b",
               "SELECT equip_type, COUNT(*) AS equip_cnt FROM equipment GROUP BY equip_type ORDER BY equip_cnt DESC, equip_type;"],
        skill="COUNT · 다중 정렬",
        tip="동률일 때 2차 정렬 기준을 정해 두면 리포트가 매번 같은 순서로 나와요. 고객이 '어제랑 순서가 달라요'라고 하는 걸 막아 줘요.",
    ),
    dict(
        id="2-6", ch=2, title="고장 잦은 설비", frm=HAN, xp=15,
        msg="기계고장(BRK)이 5번 이상 난 설비만 추려 줘요. 많은 순으로요.",
        out="equip_id, brk_cnt",
        order="brk_cnt 내림차순",
        sol="SELECT equip_id, COUNT(*) AS brk_cnt FROM downtime WHERE reason_code = 'BRK' "
            "GROUP BY equip_id HAVING COUNT(*) >= 5 ORDER BY brk_cnt DESC",
        hints=["행 조건(BRK만)은 WHERE, 그룹 조건(5번 이상)은 다른 키워드예요.",
               "묶은 뒤 거르는 건 HAVING.",
               "WHERE reason_code = 'BRK' GROUP BY equip_id HAVING COUNT(*) >= 5 ORDER BY brk_cnt DESC"],
        skill="HAVING",
        tip="WHERE는 묶기 전의 행을, HAVING은 묶은 뒤의 그룹을 걸러요. 면접 단골 질문이에요.",
    ),
    dict(
        id="2-7", ch=2, title="불량 유형별 수량", frm=LEE, xp=15,
        msg="불량 상세(defects) 기준으로 유형별 수량 합계, 많은 순으로요.",
        out="defect_type, total_qty",
        order="total_qty 내림차순",
        sol="SELECT defect_type, SUM(qty) AS total_qty FROM defects GROUP BY defect_type ORDER BY total_qty DESC",
        hints=["테이블이 defects로 바뀌었어요.",
               "SUM(qty)를 defect_type별로.",
               "SELECT defect_type, SUM(qty) AS total_qty FROM defects GROUP BY defect_type ORDER BY total_qty DESC;"],
        skill="집계 복습",
        tip="참고로 defects 합계가 production의 (생산 - 양품)과 정확히 같은지는… 언젠가 확인할 일이 생길 거예요.",
    ),
    dict(
        id="2-8", ch=2, exam=True, title="[승급 시험] 계획 미달 라인·월", frm=PARK, xp=40,
        msg="월·라인별 계획달성률(생산합계 / 계획합계 × 100, 소수 둘째 자리)이 96% 미만인 조합만 뽑아 줘요.",
        out="month, line_id, achieve_rate",
        order="month, line_id 오름차순",
        sol="SELECT strftime('%Y-%m', prod_date) AS month, line_id, "
            "ROUND(SUM(produced_qty) * 100.0 / SUM(planned_qty), 2) AS achieve_rate "
            "FROM production GROUP BY month, line_id HAVING achieve_rate < 96 ORDER BY month, line_id",
        hints=["GROUP BY에 컬럼 두 개: 월과 라인.",
               "비율은 * 100.0 으로 실수 계산, 조건은 HAVING.",
               "... GROUP BY month, line_id HAVING achieve_rate < 96 ORDER BY month, line_id"],
        skill="다중 GROUP BY · 비율 · HAVING",
        tip="'달성률 96% 미만' 같은 기준은 고객마다 달라요. 실무에선 기준값을 하드코딩하지 말고 KPI 정의서에서 받아 와야 해요.",
    ),
    # ───────────── 3장 JOIN ─────────────
    dict(
        id="3-1", ch=3, title="실적에 제품명 붙이기", frm=PARK, xp=20,
        msg="아까 8월 5일 실적, 제품코드 말고 제품명으로 볼 수 있어요? 라인, 교대, 제품명, 생산량이요.",
        out="line_id, shift, product_name, produced_qty",
        order=None,
        sol="SELECT p.line_id, p.shift, pr.product_name, p.produced_qty FROM production p "
            "JOIN products pr ON p.product_id = pr.product_id WHERE p.prod_date = '2026-08-05'",
        hints=["두 테이블을 공통 키로 잇는 게 JOIN.",
               "production.product_id = products.product_id",
               "FROM production p JOIN products pr ON p.product_id = pr.product_id WHERE p.prod_date = '2026-08-05'"],
        skill="INNER JOIN · 테이블 별칭",
        tip="별칭(p, pr)을 쓰면 쿼리가 짧아지고, 같은 이름의 컬럼이 어느 테이블 건지 헷갈리지 않아요.",
    ),
    dict(
        id="3-2", ch=3, title="설비 위치표", frm=HAN, xp=20,
        msg="설비마다 어느 공장, 어느 라인에 있는지 한 장으로 정리해 줘요.",
        out="equip_id, equip_name, line_name, plant",
        order="equip_id 오름차순",
        sol="SELECT e.equip_id, e.equip_name, l.line_name, l.plant FROM equipment e "
            "JOIN lines l ON e.line_id = l.line_id ORDER BY e.equip_id",
        hints=["equipment와 lines를 line_id로 이어요.",
               "line_name, plant는 lines 테이블에 있어요.",
               "FROM equipment e JOIN lines l ON e.line_id = l.line_id ORDER BY e.equip_id"],
        skill="JOIN 복습",
        tip="코드(L1)를 이름(1라인)으로 바꿔 주는 '마스터 테이블 조인'은 BI 리포트의 80%예요.",
    ),
    dict(
        id="3-3", ch=3, title="제품별 생산량", frm=OH, xp=20,
        msg="제품명, 카테고리별 3분기 생산량이요. 많은 순으로.",
        out="product_name, category, total_produced",
        order="total_produced 내림차순",
        sol="SELECT pr.product_name, pr.category, SUM(p.produced_qty) AS total_produced FROM production p "
            "JOIN products pr ON p.product_id = pr.product_id GROUP BY pr.product_name, pr.category "
            "ORDER BY total_produced DESC",
        hints=["JOIN한 뒤에 GROUP BY 하면 돼요.",
               "GROUP BY pr.product_name, pr.category",
               "FROM production p JOIN products pr ON ... GROUP BY pr.product_name, pr.category ORDER BY total_produced DESC"],
        skill="JOIN + GROUP BY",
        tip="JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY. 이 실행 순서를 머릿속에 두면 에러의 절반이 사라져요.",
    ),
    dict(
        id="3-4", ch=3, title="9월 수주 상세", frm=CHOI, xp=20,
        msg="9월 수주 건 목록 좀요. 주문번호, 주문일, 고객사명, 제품명, 수량.",
        out="order_id, order_date, customer_name, product_name, order_qty",
        order="order_date 오름차순 (같으면 order_id)",
        sol="SELECT o.order_id, o.order_date, c.customer_name, pr.product_name, o.order_qty FROM orders o "
            "JOIN customers c ON o.customer_id = c.customer_id JOIN products pr ON o.product_id = pr.product_id "
            "WHERE o.order_date >= '2026-09-01' ORDER BY o.order_date, o.order_id",
        hints=["테이블 세 개: orders, customers, products.",
               "JOIN을 두 번 이어 쓰면 돼요.",
               "FROM orders o JOIN customers c ON ... JOIN products pr ON ... WHERE o.order_date >= '2026-09-01'"],
        skill="3-테이블 JOIN",
        tip="조인이 늘어날수록 'FROM 다음 첫 테이블이 이 리포트의 한 행 단위'라는 걸 의식하세요. 여기선 주문 1건 = 1행.",
    ),
    dict(
        id="3-5", ch=3, title="미출하 주문", frm=CHOI, xp=20,
        msg="출하가 한 번도 안 된 주문이 있죠? 주문번호, 고객사명, 납기일이요.",
        out="order_id, customer_name, due_date",
        order="due_date 오름차순 (같으면 order_id)",
        sol="SELECT o.order_id, c.customer_name, o.due_date FROM orders o "
            "JOIN customers c ON o.customer_id = c.customer_id "
            "LEFT JOIN shipments s ON o.order_id = s.order_id WHERE s.shipment_id IS NULL "
            "ORDER BY o.due_date, o.order_id",
        hints=["짝이 없는 행도 살리는 JOIN이 있어요: LEFT JOIN.",
               "LEFT JOIN 후 오른쪽 테이블 값이 NULL인 행 = 짝이 없는 행.",
               "LEFT JOIN shipments s ON o.order_id = s.order_id WHERE s.shipment_id IS NULL"],
        skill="LEFT JOIN · 안티 조인",
        tip="NOT IN (서브쿼리)은 서브쿼리에 NULL이 하나라도 있으면 결과가 통째로 비어요. LEFT JOIN … IS NULL 이나 NOT EXISTS가 안전해요.",
    ),
    dict(
        id="3-6", ch=3, title="라인별 재직 인원", frm=PARK, xp=20,
        msg="라인별 현재 재직 인원이요(퇴사일 없는 사람). 아직 아무도 없는 신설 5라인도 0명으로 꼭 나오게요.",
        out="line_id, line_name, active_workers",
        order="line_id 오름차순",
        sol="SELECT l.line_id, l.line_name, COUNT(w.worker_id) AS active_workers FROM lines l "
            "LEFT JOIN workers w ON l.line_id = w.line_id AND w.leave_date IS NULL "
            "GROUP BY l.line_id, l.line_name ORDER BY l.line_id",
        hints=["기준 테이블은 lines (5라인도 나와야 하니까).",
               "COUNT(*)는 NULL 행도 1로 세요. 짝이 없으면 0이 나오게 하려면 COUNT(오른쪽 테이블 컬럼).",
               "FROM lines l LEFT JOIN workers w ON l.line_id = w.line_id AND w.leave_date IS NULL ... COUNT(w.worker_id)"],
        skill="LEFT JOIN + COUNT(컬럼)",
        traps=[
            dict(sql="SELECT l.line_id, l.line_name, COUNT(*) FROM lines l LEFT JOIN workers w "
                     "ON l.line_id = w.line_id AND w.leave_date IS NULL GROUP BY l.line_id, l.line_name",
                 msg="5라인이 1명으로 나오죠? COUNT(*)는 짝 없는 NULL 행도 1로 세요. COUNT(w.worker_id)로 바꾸세요."),
            dict(sql="SELECT l.line_id, l.line_name, COUNT(w.worker_id) FROM lines l LEFT JOIN workers w "
                     "ON l.line_id = w.line_id GROUP BY l.line_id, l.line_name",
                 msg="퇴사자까지 셌어요. leave_date IS NULL 조건을 추가하세요."),
            dict(sql="SELECT l.line_id, l.line_name, COUNT(w.worker_id) FROM lines l JOIN workers w "
                     "ON l.line_id = w.line_id AND w.leave_date IS NULL GROUP BY l.line_id, l.line_name",
                 msg="5라인이 사라졌죠? INNER JOIN은 짝이 없는 행을 버려요. LEFT JOIN으로."),
        ],
        tip="LEFT JOIN에서 오른쪽 테이블 조건을 WHERE에 쓰면 짝 없는 행이 지워지는 경우가 많아요. 그래서 ON에 같이 두는 패턴을 익혀 두세요.",
    ),
    dict(
        id="3-7", ch=3, title="라인별 비계획 정지 시간", frm=HAN, xp=20,
        msg="라인별 비계획 정지(is_planned = 0) 시간 합계를 분 단위로요. 소수 첫째 자리, 큰 순으로요.",
        out="line_name, unplanned_min",
        order="unplanned_min 내림차순",
        sol=f"SELECT l.line_name, ROUND(SUM({_DUR}), 1) AS unplanned_min FROM downtime d "
            "JOIN equipment e ON d.equip_id = e.equip_id JOIN lines l ON e.line_id = l.line_id "
            "WHERE d.is_planned = 0 GROUP BY l.line_name ORDER BY unplanned_min DESC",
        hints=["downtime → equipment → lines 순으로 이어요.",
               "두 시각의 차이(일) = julianday(end_ts) - julianday(start_ts). 분으로 바꾸려면 × 1440.",
               "ROUND(SUM((julianday(d.end_ts) - julianday(d.start_ts)) * 1440), 1)"],
        skill="시각 차이 계산 · 다단 JOIN",
        tip="시간 차 계산도 DB마다 달라요(SQLite julianday, MySQL TIMESTAMPDIFF, PostgreSQL 빼기). 숫자가 좀 커 보이지 않나요? 기억해 두세요.",
    ),
    dict(
        id="3-8", ch=3, title="주문별 미출하 잔량", frm=CHOI, xp=20,
        msg="주문별로 아직 못 보낸 수량(잔량)이 있는 건 전부요. 주문번호, 주문수량, 출하합계(없으면 0), 잔량.",
        out="order_id, order_qty, shipped_qty, remain_qty",
        order="remain_qty 내림차순 (같으면 order_id)",
        sol="SELECT o.order_id, o.order_qty, COALESCE(SUM(s.ship_qty), 0) AS shipped_qty, "
            "o.order_qty - COALESCE(SUM(s.ship_qty), 0) AS remain_qty FROM orders o "
            "LEFT JOIN shipments s ON o.order_id = s.order_id GROUP BY o.order_id, o.order_qty "
            "HAVING remain_qty > 0 ORDER BY remain_qty DESC, o.order_id",
        hints=["출하가 없는 주문도 포함해야 하니 LEFT JOIN.",
               "출하가 없으면 SUM은 NULL. NULL을 0으로 바꾸는 함수: COALESCE(x, 0)",
               "COALESCE(SUM(s.ship_qty), 0) AS shipped_qty ... HAVING remain_qty > 0"],
        skill="LEFT JOIN + 집계 · COALESCE",
        traps=[dict(sql="SELECT o.order_id, o.order_qty, SUM(s.ship_qty), o.order_qty - SUM(s.ship_qty) AS remain_qty "
                        "FROM orders o LEFT JOIN shipments s ON o.order_id = s.order_id GROUP BY o.order_id, o.order_qty "
                        "HAVING remain_qty > 0 ORDER BY remain_qty DESC, o.order_id",
                    msg="출하가 아예 없는 주문이 빠졌어요. SUM이 NULL이면 계산 결과도 NULL이라 HAVING에서 걸러져요. COALESCE로 0 처리를."),
               ],
        tip="NULL + 숫자 = NULL. 계산식에 들어가는 집계값엔 COALESCE를 습관처럼.",
    ),
    dict(
        id="3-9", ch=3, exam=True, title="[승급 시험] 8월 정지 사유 리포트", frm=HAN, xp=50,
        msg="8월 비계획 정지를 사유명별로 정리해 줘요. 사유명, 건수, 총 정지시간(분, 소수 첫째 자리), "
            "발생한 라인 수. 총 정지시간 큰 순으로요.",
        out="reason_name, stop_cnt, total_min, line_cnt",
        order="total_min 내림차순",
        sol=f"SELECT r.reason_name, COUNT(*) AS stop_cnt, ROUND(SUM({_DUR}), 1) AS total_min, "
            "COUNT(DISTINCT e.line_id) AS line_cnt FROM downtime d "
            "JOIN reason_codes r ON d.reason_code = r.reason_code JOIN equipment e ON d.equip_id = e.equip_id "
            "WHERE d.is_planned = 0 AND d.start_ts >= '2026-08-01' AND d.start_ts < '2026-09-01' "
            "GROUP BY r.reason_name ORDER BY total_min DESC",
        hints=["사유명은 reason_codes, 라인은 equipment에 있어요.",
               "서로 다른 값의 개수는 COUNT(DISTINCT 컬럼).",
               "8월 범위: d.start_ts >= '2026-08-01' AND d.start_ts < '2026-09-01'"],
        skill="다중 JOIN · COUNT(DISTINCT)",
        tip="월 범위는 '>= 이번 달 1일 AND < 다음 달 1일'로 쓰는 게 안전해요. 말일·시각 처리 실수가 없어요.",
    ),
    # ───────────── 4장 서브쿼리 · CASE · CTE ─────────────
    dict(
        id="4-1", ch=4, title="평균보다 비싼 제품", frm=CHOI, xp=25,
        msg="평균 단가보다 비싼 제품만 단가 높은 순으로요.",
        out="product_name, unit_price",
        order="unit_price 내림차순",
        sol="SELECT product_name, unit_price FROM products "
            "WHERE unit_price > (SELECT AVG(unit_price) FROM products) ORDER BY unit_price DESC",
        hints=["평균 단가를 먼저 구하는 쿼리를 괄호 안에 넣을 수 있어요.",
               "WHERE unit_price > (SELECT ...)",
               "WHERE unit_price > (SELECT AVG(unit_price) FROM products)"],
        skill="스칼라 서브쿼리",
        tip="WHERE unit_price > AVG(unit_price)는 에러예요. 집계는 WHERE에서 못 쓰니까 서브쿼리로 값을 먼저 만들어요.",
    ),
    dict(
        id="4-2", ch=4, title="8월 고장 설비", frm=HAN, xp=25,
        msg="8월에 기계고장(BRK)이 한 번이라도 난 설비 목록이요. 설비번호, 설비명.",
        out="equip_id, equip_name",
        order="equip_id 오름차순",
        sol="SELECT equip_id, equip_name FROM equipment WHERE equip_id IN ("
            "SELECT equip_id FROM downtime WHERE reason_code = 'BRK' "
            "AND start_ts >= '2026-08-01' AND start_ts < '2026-09-01') ORDER BY equip_id",
        hints=["'~한 적이 있는' = IN (서브쿼리) 또는 EXISTS.",
               "JOIN으로 하면 고장 횟수만큼 설비가 중복돼요.",
               "WHERE equip_id IN (SELECT equip_id FROM downtime WHERE reason_code = 'BRK' AND ...)"],
        skill="IN 서브쿼리 · EXISTS",
        traps=[dict(sql="SELECT e.equip_id, e.equip_name FROM equipment e JOIN downtime d ON e.equip_id = d.equip_id "
                        "WHERE d.reason_code = 'BRK' AND d.start_ts >= '2026-08-01' AND d.start_ts < '2026-09-01' "
                        "ORDER BY e.equip_id",
                    msg="같은 설비가 여러 번 나오죠? JOIN은 고장 건수만큼 행을 늘려요. IN/EXISTS를 쓰거나 DISTINCT로."),
               ],
        tip="'존재 여부'만 필요할 땐 EXISTS가 의도를 가장 잘 드러내요. 리뷰어가 읽기 쉬운 쿼리가 좋은 쿼리예요.",
    ),
    dict(
        id="4-3", ch=4, title="교대 실적 등급 분포", frm=PARK, xp=25,
        msg="교대 실적마다 등급을 매겨 주세요. 생산이 계획 이상이면 '달성', 계획의 95% 이상이면 '근접', "
            "나머지는 '미달'. 등급별 건수만 보면 돼요.",
        out="grade, cnt",
        order=None,
        sol="SELECT CASE WHEN produced_qty >= planned_qty THEN '달성' "
            "WHEN produced_qty * 1.0 / planned_qty >= 0.95 THEN '근접' ELSE '미달' END AS grade, "
            "COUNT(*) AS cnt FROM production GROUP BY grade",
        hints=["조건에 따라 값을 바꾸는 건 CASE WHEN ... THEN ... ELSE ... END.",
               "CASE는 위에서부터 첫 번째로 맞는 조건만 적용돼요. 그리고 정수 나눗셈 주의!",
               "CASE WHEN produced_qty >= planned_qty THEN '달성' WHEN produced_qty * 1.0 / planned_qty >= 0.95 THEN '근접' ELSE '미달' END"],
        skill="CASE WHEN",
        traps=[dict(sql="SELECT CASE WHEN produced_qty >= planned_qty THEN '달성' "
                        "WHEN produced_qty / planned_qty >= 0.95 THEN '근접' ELSE '미달' END AS grade, "
                        "COUNT(*) FROM production GROUP BY grade",
                    msg="'근접'이 사라졌죠? produced_qty / planned_qty가 정수 나눗셈이라 0이 됐어요. * 1.0 을."),
               ],
        tip="CASE로 만든 '등급 컬럼'은 고객 KPI 정의를 SQL로 옮기는 기본 도구예요. 기준이 바뀌면 여기만 고치면 되도록 한곳에 모아 두세요.",
    ),
    dict(
        id="4-4", ch=4, title="주간·야간 나란히", frm=PARK, xp=25,
        msg="라인별로 주간·야간 생산량을 한 줄에 나란히 보여 줘요. 야간이 없는 라인은 0으로.",
        out="line_id, day_qty, night_qty",
        order="line_id 오름차순",
        sol="SELECT line_id, SUM(CASE WHEN shift = '주간' THEN produced_qty ELSE 0 END) AS day_qty, "
            "SUM(CASE WHEN shift = '야간' THEN produced_qty ELSE 0 END) AS night_qty "
            "FROM production GROUP BY line_id ORDER BY line_id",
        hints=["SUM 안에 CASE를 넣으면 조건에 맞는 값만 더할 수 있어요.",
               "조건에 안 맞으면 0을 더하게: ELSE 0",
               "SUM(CASE WHEN shift = '주간' THEN produced_qty ELSE 0 END) AS day_qty"],
        skill="조건부 집계 (피벗)",
        traps=[dict(sql="SELECT line_id, SUM(CASE WHEN shift = '주간' THEN produced_qty END), "
                        "SUM(CASE WHEN shift = '야간' THEN produced_qty END) FROM production GROUP BY line_id ORDER BY line_id",
                    msg="4라인 야간이 NULL이죠? ELSE가 없으면 NULL이 들어가요. ELSE 0 을 붙이세요."),
               ],
        tip="이 '조건부 집계'가 엑셀 피벗을 SQL로 하는 방법이에요. BI 대시보드용 마트 테이블 만들 때 매일 써요.",
    ),
    dict(
        id="4-5", ch=4, title="고객사별 주문 vs 출하 (함정 주의)", frm=CHOI, xp=25,
        msg="고객사별 총 주문수량과 총 출하수량을 비교하고 싶어요. 수주 데이터 전체 기준, 고객사명 순으로요.",
        out="customer_name, order_qty_total, ship_qty_total",
        order="customer_name 오름차순",
        sol="WITH s AS (SELECT order_id, SUM(ship_qty) AS shipped FROM shipments GROUP BY order_id) "
            "SELECT c.customer_name, SUM(o.order_qty) AS order_qty_total, COALESCE(SUM(s.shipped), 0) AS ship_qty_total "
            "FROM orders o JOIN customers c ON o.customer_id = c.customer_id LEFT JOIN s ON o.order_id = s.order_id "
            "GROUP BY c.customer_name ORDER BY c.customer_name",
        hints=["주문 1건에 출하가 2건이면, JOIN 결과에서 그 주문은 몇 줄이 될까요?",
               "출하를 주문 단위로 먼저 묶은 다음(서브쿼리나 WITH) 조인하세요.",
               "WITH s AS (SELECT order_id, SUM(ship_qty) AS shipped FROM shipments GROUP BY order_id) SELECT ... LEFT JOIN s ON ..."],
        skill="팬아웃 회피 · 사전 집계 · WITH",
        traps=[dict(sql="SELECT c.customer_name, SUM(o.order_qty), SUM(s.ship_qty) FROM orders o "
                        "JOIN customers c ON o.customer_id = c.customer_id LEFT JOIN shipments s ON o.order_id = s.order_id "
                        "GROUP BY c.customer_name ORDER BY c.customer_name",
                    msg="주문수량이 실제보다 커졌어요. 팬아웃이에요! 출하가 2건인 주문은 JOIN 후 2줄이 돼서 order_qty가 두 번 더해져요. 출하를 주문별로 먼저 묶은 뒤 조인하세요."),
               ],
        tip="대시보드 숫자가 '이상하게 크다'면 대부분 팬아웃이에요. 조인 전에 '이 키가 양쪽에서 1:1인가?'를 항상 확인하세요. 면접에서 이 경험을 말할 수 있으면 강력해요.",
    ),
    dict(
        id="4-6", ch=4, title="3분기 납기 준수율", frm=CHOI, xp=25,
        msg="납기일이 7/1~9/30인 주문의 납기 준수율이요. 준수 = 주문수량 이상 출하를 마쳤고 "
            "마지막 출하일이 납기일 이하. 미출하·부분출하는 미준수예요.",
        out="total_orders, on_time_orders, on_time_rate (%, 소수 둘째 자리)",
        order=None,
        sol="WITH s AS (SELECT order_id, SUM(ship_qty) AS shipped, MAX(ship_date) AS last_ship "
            "FROM shipments GROUP BY order_id) "
            "SELECT COUNT(*) AS total_orders, "
            "SUM(CASE WHEN s.shipped >= o.order_qty AND s.last_ship <= o.due_date THEN 1 ELSE 0 END) AS on_time_orders, "
            "ROUND(SUM(CASE WHEN s.shipped >= o.order_qty AND s.last_ship <= o.due_date THEN 1 ELSE 0 END) * 100.0 "
            "/ COUNT(*), 2) AS on_time_rate "
            "FROM orders o LEFT JOIN s ON o.order_id = s.order_id "
            "WHERE o.due_date BETWEEN '2026-07-01' AND '2026-09-30'",
        hints=["WITH로 주문별 출하합계·마지막 출하일을 먼저 만들어요.",
               "주문 기준 LEFT JOIN 후, 준수 여부를 CASE로 1/0 만들고 SUM.",
               "SUM(CASE WHEN s.shipped >= o.order_qty AND s.last_ship <= o.due_date THEN 1 ELSE 0 END)"],
        skill="CTE (WITH) · KPI 계산",
        tip="KPI는 '분모가 뭐냐'에서 싸움이 나요. 여기선 '납기일 기준'이었죠. 주문일 기준이면 숫자가 달라져요. 정의를 문서로 합의하는 게 BI 엔지니어의 일이에요.",
    ),
    dict(
        id="4-7", ch=4, title="라인별 최고 실적", frm=PARK, xp=25,
        msg="라인마다 생산량이 가장 많았던 교대 실적이요. 동률이면 다 보여 줘요.",
        out="line_id, prod_date, shift, produced_qty",
        order="line_id, prod_date, shift 오름차순",
        sol="SELECT p.line_id, p.prod_date, p.shift, p.produced_qty FROM production p "
            "WHERE p.produced_qty = (SELECT MAX(p2.produced_qty) FROM production p2 WHERE p2.line_id = p.line_id) "
            "ORDER BY p.line_id, p.prod_date, p.shift",
        hints=["'그 라인의 최댓값'은 바깥 행의 라인에 따라 달라져요.",
               "서브쿼리 안에서 바깥 테이블 별칭을 참조할 수 있어요(상관 서브쿼리).",
               "WHERE p.produced_qty = (SELECT MAX(p2.produced_qty) FROM production p2 WHERE p2.line_id = p.line_id)"],
        skill="상관 서브쿼리",
        tip="같은 문제를 다음 장의 윈도우 함수로도 풀 수 있어요. 데이터가 크면 보통 윈도우 함수가 더 빨라요.",
    ),
    dict(
        id="4-8", ch=4, exam=True, title="[승급 시험] 등급·월별 납기 준수율", frm=OH, xp=60,
        msg="고객 등급(A/B/C)별, 납기월별 납기 준수율이 필요해요. 대상은 납기일 7/1~9/30 주문, "
            "준수 정의는 지난번이랑 같아요.",
        out="grade, due_month, total_orders, on_time_orders, on_time_rate (%, 소수 둘째 자리)",
        order="grade, due_month 오름차순",
        sol="WITH s AS (SELECT order_id, SUM(ship_qty) AS shipped, MAX(ship_date) AS last_ship "
            "FROM shipments GROUP BY order_id) "
            "SELECT c.grade, strftime('%Y-%m', o.due_date) AS due_month, COUNT(*) AS total_orders, "
            "SUM(CASE WHEN s.shipped >= o.order_qty AND s.last_ship <= o.due_date THEN 1 ELSE 0 END) AS on_time_orders, "
            "ROUND(SUM(CASE WHEN s.shipped >= o.order_qty AND s.last_ship <= o.due_date THEN 1 ELSE 0 END) * 100.0 "
            "/ COUNT(*), 2) AS on_time_rate "
            "FROM orders o JOIN customers c ON o.customer_id = c.customer_id LEFT JOIN s ON o.order_id = s.order_id "
            "WHERE o.due_date BETWEEN '2026-07-01' AND '2026-09-30' "
            "GROUP BY c.grade, due_month ORDER BY c.grade, due_month",
        hints=["4-6 쿼리에 고객 등급과 납기월을 더하면 돼요.",
               "customers를 JOIN하고 GROUP BY c.grade, 납기월.",
               "... GROUP BY c.grade, strftime('%Y-%m', o.due_date) ORDER BY ..."],
        skill="CTE + CASE + JOIN + 다중 GROUP BY",
        tip="이 쿼리가 세일링스톤 공고의 '비즈니스 로직 구현' 수준이에요. 여기까지 왔으면 서류의 SQL 항목은 자신 있게 써도 돼요.",
    ),
    # ───────────── 5장 윈도우 함수 · KPI ─────────────
    dict(
        id="5-1", ch=5, title="라인별 TOP 3 교대", frm=PARK, xp=30,
        msg="라인별 생산량 상위 3개 교대 실적에 순위를 매겨 줘요. 동률이면 날짜 빠른 것, 그다음 교대 이름 순.",
        out="line_id, rn, prod_date, shift, produced_qty",
        order="line_id, rn 오름차순",
        sol="WITH r AS (SELECT line_id, prod_date, shift, produced_qty, ROW_NUMBER() OVER "
            "(PARTITION BY line_id ORDER BY produced_qty DESC, prod_date, shift) AS rn FROM production) "
            "SELECT line_id, rn, prod_date, shift, produced_qty FROM r WHERE rn <= 3 ORDER BY line_id, rn",
        hints=["그룹별 순위 = ROW_NUMBER() OVER (PARTITION BY 그룹 ORDER BY 기준)",
               "윈도우 함수 결과는 같은 쿼리의 WHERE에서 못 써요. WITH로 한 번 감싸요.",
               "WITH r AS (SELECT ..., ROW_NUMBER() OVER (PARTITION BY line_id ORDER BY produced_qty DESC, prod_date, shift) AS rn FROM production) SELECT ... WHERE rn <= 3"],
        skill="ROW_NUMBER · PARTITION BY",
        tip="'그룹별 Top N'은 데이터 직무 SQL 테스트 출제율 1위예요. 이 패턴은 손이 기억할 때까지.",
    ),
    dict(
        id="5-2", ch=5, title="제품별 매출 순위", frm=CHOI, xp=30,
        msg="출하 기준 제품별 매출(출하수량 × 단가)과 순위요. 금액이 같으면 같은 순위로.",
        out="product_name, revenue, rnk",
        order="rnk, product_name 오름차순",
        sol="SELECT pr.product_name, SUM(s.ship_qty * pr.unit_price) AS revenue, "
            "RANK() OVER (ORDER BY SUM(s.ship_qty * pr.unit_price) DESC) AS rnk FROM shipments s "
            "JOIN orders o ON s.order_id = o.order_id JOIN products pr ON o.product_id = pr.product_id "
            "GROUP BY pr.product_name ORDER BY rnk, pr.product_name",
        hints=["shipments → orders → products 순으로 이어야 단가가 나와요.",
               "동률 같은 순위 = RANK(). 집계값 위에 윈도우를 씌울 수 있어요.",
               "RANK() OVER (ORDER BY SUM(s.ship_qty * pr.unit_price) DESC) AS rnk"],
        skill="RANK · 집계 위의 윈도우",
        tip="ROW_NUMBER(동률 무시) / RANK(1,1,3) / DENSE_RANK(1,1,2). 차이를 말로 설명할 수 있게 해 두세요.",
    ),
    dict(
        id="5-3", ch=5, title="1라인 9월 누적 생산", frm=PARK, xp=30,
        msg="1라인 9월 일별 생산량(주간+야간 합)이랑 월 누적 생산량을 같이 보여 줘요.",
        out="prod_date, daily_qty, cum_qty",
        order="prod_date 오름차순",
        sol="SELECT prod_date, SUM(produced_qty) AS daily_qty, "
            "SUM(SUM(produced_qty)) OVER (ORDER BY prod_date) AS cum_qty FROM production "
            "WHERE line_id = 'L1' AND prod_date >= '2026-09-01' GROUP BY prod_date ORDER BY prod_date",
        hints=["먼저 날짜별로 GROUP BY.",
               "누적합 = SUM(...) OVER (ORDER BY 날짜). 집계값의 누적이면 SUM(SUM(x)) OVER (...)",
               "SUM(SUM(produced_qty)) OVER (ORDER BY prod_date) AS cum_qty"],
        skill="누적합 SUM() OVER",
        tip="목표 대비 누적 진척률(누적 생산 / 월 목표) 대시보드가 이 쿼리 하나로 나와요.",
    ),
    dict(
        id="5-4", ch=5, title="전월 대비 증감률", frm=OH, xp=30,
        msg="월별 총 생산량, 전월 생산량, 증감률(%, 소수 둘째 자리)이요. 7월은 전월 데이터가 없으니 비워 두고요.",
        out="month, total_produced, prev_produced, change_pct",
        order="month 오름차순",
        sol="WITH m AS (SELECT strftime('%Y-%m', prod_date) AS month, SUM(produced_qty) AS total_produced "
            "FROM production GROUP BY month) "
            "SELECT month, total_produced, LAG(total_produced) OVER (ORDER BY month) AS prev_produced, "
            "ROUND((total_produced - LAG(total_produced) OVER (ORDER BY month)) * 100.0 "
            "/ LAG(total_produced) OVER (ORDER BY month), 2) AS change_pct FROM m ORDER BY month",
        hints=["이전 행 값 = LAG(컬럼) OVER (ORDER BY 기준)",
               "월별 합계를 WITH로 먼저 만들고, 그 위에서 LAG.",
               "(total_produced - LAG(total_produced) OVER (ORDER BY month)) * 100.0 / LAG(total_produced) OVER (ORDER BY month)"],
        skill="LAG · 증감률",
        tip="첫 달의 NULL은 '데이터 없음'이 정답이에요. 0으로 채우면 증감률이 무한대가 돼요. 비워 두는 것도 설계예요.",
    ),
    dict(
        id="5-5", ch=5, title="프레스 #1 진동 이동평균", frm=HAN, xp=30,
        msg="프레스 #1(E31)의 9월 일별 최대진동이랑 7일 이동평균(당일 포함 최근 7개 측정값 평균, 소수 둘째 자리)이요. "
            "9월 초 값도 8월 말 측정값을 포함해서 계산해야 해요.",
        out="reading_date, max_vibration, ma7",
        order="reading_date 오름차순",
        sol="WITH w AS (SELECT reading_date, max_vibration, ROUND(AVG(max_vibration) OVER "
            "(ORDER BY reading_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS ma7 "
            "FROM sensor_daily WHERE equip_id = 'E31') "
            "SELECT reading_date, max_vibration, ma7 FROM w WHERE reading_date >= '2026-09-01' ORDER BY reading_date",
        hints=["범위 지정 윈도우: AVG(x) OVER (ORDER BY 날짜 ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)",
               "9월로 먼저 거르면 8월 말 값이 빠져요. 윈도우를 먼저 계산하고 바깥에서 9월만 남기세요.",
               "WITH w AS (SELECT ..., ROUND(AVG(max_vibration) OVER (ORDER BY reading_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS ma7 FROM sensor_daily WHERE equip_id = 'E31') SELECT ... FROM w WHERE reading_date >= '2026-09-01'"],
        skill="이동평균 · ROWS BETWEEN · 필터 순서",
        traps=[dict(sql="SELECT reading_date, max_vibration, ROUND(AVG(max_vibration) OVER "
                        "(ORDER BY reading_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) FROM sensor_daily "
                        "WHERE equip_id = 'E31' AND reading_date >= '2026-09-01' ORDER BY reading_date",
                    msg="9월 첫 며칠 값만 다르죠? WHERE가 윈도우보다 먼저 실행돼서 8월 말 값이 빠졌어요. 전체에서 윈도우를 먼저 → 바깥에서 9월 필터."),
               ],
        tip="'필터 → 윈도우' 순서 실수는 시계열 리포트의 대표 버그예요. 부트캠프 시계열 분석에서 본 rolling과 같은 개념이에요.",
    ),
    dict(
        id="5-6", ch=5, title="설비별 평균 고장 간격 (MTBF)", frm=HAN, xp=30,
        msg="설비별 기계고장(BRK) 평균 간격을 일 단위로요. 간격 = 직전 BRK 시작시각부터 이번 BRK 시작시각까지. "
            "BRK 2회 이상 설비만, 간격 짧은 순.",
        out="equip_id, brk_cnt, avg_gap_days (소수 첫째 자리)",
        order="avg_gap_days 오름차순 (같으면 equip_id)",
        sol="WITH b AS (SELECT equip_id, julianday(start_ts) - julianday(LAG(start_ts) OVER "
            "(PARTITION BY equip_id ORDER BY start_ts)) AS gap FROM downtime WHERE reason_code = 'BRK') "
            "SELECT equip_id, COUNT(*) AS brk_cnt, ROUND(AVG(gap), 1) AS avg_gap_days FROM b "
            "GROUP BY equip_id HAVING COUNT(*) >= 2 ORDER BY avg_gap_days, equip_id",
        hints=["설비별로 직전 고장 시각 = LAG(start_ts) OVER (PARTITION BY equip_id ORDER BY start_ts)",
               "간격(일) = julianday(현재) - julianday(직전). 첫 고장은 NULL이고, AVG는 NULL을 무시해요.",
               "WITH b AS (SELECT equip_id, julianday(start_ts) - julianday(LAG(start_ts) OVER (...)) AS gap FROM downtime WHERE reason_code = 'BRK') SELECT equip_id, COUNT(*), ROUND(AVG(gap), 1) ..."],
        skill="LAG로 간격 계산 · MTBF",
        tip="MTBF(평균 고장 간격)와 MTTR(평균 수리 시간)은 설비보전 KPI의 기본이에요. 예지보전 PoC 미팅에서 반드시 나와요.",
    ),
    dict(
        id="5-7", ch=5, title="라인별 불량 비중", frm=LEE, xp=30,
        msg="라인별 불량수량(생산 - 양품 합)이랑 전체 불량 대비 비중(%, 소수 둘째 자리)이요. 큰 순으로.",
        out="line_id, defect_qty, share_pct",
        order="defect_qty 내림차순",
        sol="SELECT line_id, SUM(produced_qty - good_qty) AS defect_qty, "
            "ROUND(SUM(produced_qty - good_qty) * 100.0 / SUM(SUM(produced_qty - good_qty)) OVER (), 2) AS share_pct "
            "FROM production GROUP BY line_id ORDER BY defect_qty DESC",
        hints=["전체 합계를 각 행 옆에 붙이는 방법: SUM(x) OVER ()",
               "집계값의 전체 합이면 SUM(SUM(x)) OVER ()",
               "SUM(produced_qty - good_qty) * 100.0 / SUM(SUM(produced_qty - good_qty)) OVER ()"],
        skill="SUM() OVER () · 구성비",
        tip="파레토 분석(상위 몇 개가 전체의 80%?)도 이 구성비에 누적합을 더하면 바로 나와요.",
    ),
    dict(
        id="5-8", ch=5, exam=True, title="[승급 시험] 예지보전: 진동 이상 감지", frm=HAN, xp=70,
        msg="예지보전 PoC 첫 단추예요. 9월 측정값 중에 최대진동이 '직전 7개 측정값 평균(당일 제외)'의 1.3배 이상인 날을 "
            "전 설비에서 뽑아 줘요. 그리고 그날을 포함해 3일 이내(당일~+3일)에 실제로 비계획 고장(BRK 또는 ELC)이 "
            "시작됐는지 Y/N으로 표시해 줘요. 직전 7개에는 8월 값도 포함돼야 해요.",
        out="equip_id, reading_date, max_vibration, prev7_avg (소수 둘째 자리), failure_within_3d ('Y'/'N')",
        order="equip_id, reading_date 오름차순",
        sol="WITH s AS (SELECT equip_id, reading_date, max_vibration, AVG(max_vibration) OVER "
            "(PARTITION BY equip_id ORDER BY reading_date ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS prev7_avg "
            "FROM sensor_daily) "
            "SELECT s.equip_id, s.reading_date, s.max_vibration, ROUND(s.prev7_avg, 2) AS prev7_avg, "
            "CASE WHEN EXISTS (SELECT 1 FROM downtime d WHERE d.equip_id = s.equip_id "
            "AND d.reason_code IN ('BRK', 'ELC') "
            "AND date(d.start_ts) BETWEEN s.reading_date AND date(s.reading_date, '+3 days')) "
            "THEN 'Y' ELSE 'N' END AS failure_within_3d "
            "FROM s WHERE s.reading_date >= '2026-09-01' AND s.max_vibration >= s.prev7_avg * 1.3 "
            "ORDER BY s.equip_id, s.reading_date",
        hints=["당일 제외 직전 7개: ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING, 설비별로 PARTITION BY.",
               "윈도우는 전체 기간에 대해 WITH 안에서 계산하고, 9월 필터와 1.3배 조건은 바깥에서.",
               "Y/N: CASE WHEN EXISTS (SELECT 1 FROM downtime d WHERE d.equip_id = s.equip_id AND d.reason_code IN ('BRK','ELC') AND date(d.start_ts) BETWEEN s.reading_date AND date(s.reading_date, '+3 days')) THEN 'Y' ELSE 'N' END"],
        skill="윈도우 + EXISTS + 날짜 연산 (예지보전 로직)",
        tip="결과에서 Y 비율이 이 규칙의 정밀도(precision)예요. 고객 PoC에선 '경보 몇 건 중 몇 건이 진짜였나'를 이렇게 보여 줘요. LS 부트캠프 예지보전과 바로 연결되는 이야기예요.",
    ),
]
