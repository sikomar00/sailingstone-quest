-- ============================================================
-- [티켓 1-3] 8월 5일 계획 미달 실적
-- 요청자: 박정훈 생산팀장 (한결정밀)
--
--   8월 5일 실적 중에 계획보다 덜 만든 교대가 있죠? 라인, 교대, 제품,
--   계획·실적 수량이랑 부족 수량까지 보여 줘요.
--
-- 출력 컬럼 : line_id, shift, product_id, planned_qty, produced_qty,
-- short_qty (= planned_qty - produced_qty)
-- 정렬      : 자유 (순서 무관)
-- ------------------------------------------------------------
-- 저장 후 터미널에서  python play.py check   (결과만 보기: python play.py run)
-- 막히면            python play.py hint    (테이블 구조: python play.py schema)
-- ============================================================

select
    line_id,
    shift,
    product_id,
    planned_qty,
    produced_qty,
    (planned_qty - produced_qty) AS short_qty
from production
where prod_date = '2026-08-05' and short_qty > 0
order by short_qty;

-- select * from production;

-- select
--     planned_qty,
--     produced_qty,
--     (planned_qty - produced_qty) AS short_qty
-- from production
-- where prod_date = '2026-08-05' and short_qty < 0;