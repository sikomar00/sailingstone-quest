-- ============================================================
-- [티켓 1-5] 9월 고장 이력
-- 요청자: 한상철 설비보전 파트장 (한결정밀)
--
--   9월에 발생한 기계고장(BRK)이랑 전기고장(ELC)만 시간순으로 뽑아 줘요.
--
-- 출력 컬럼 : downtime_id, equip_id, start_ts, reason_code
-- 정렬      : start_ts 오름차순 (같으면 downtime_id)
-- ------------------------------------------------------------
-- 저장 후 터미널에서  python play.py check   (결과만 보기: python play.py run)
-- 막히면            python play.py hint    (테이블 구조: python play.py schema)
-- ============================================================

select
    downtime_id,
    equip_id,
    start_ts,
    reason_code
from downtime
where start_ts LIKE '2026-09%' and (reason_code = 'BRK' or reason_code = 'ELC')
-- where reason_code in ('BRK', 'ELC') 
--     and start_ts >= '2026-09-01 00:00:00' 
--     and start_ts < '2026-10-01 00:00:00'
order by start_ts, downtime_id;

-- select * from downtime;

-- 2. start_ts = '2026-09%'
--   '=' 연산자는 와일드카드(%)를 인식하지 못하고 문자열 그대로 비교합니다. 패턴 매칭을 하려면 LIKE를 쓰거나 날짜 범위 조건을 주어야 합니다.

-- where start_ts LIKE '2026-09%' and reason_code = 'BRK' or reason_code = 'ELC' <<< AND 연산자가 OR 연산자보다 우선순위가 높da
