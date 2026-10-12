-- ============================================================
-- [티켓 1-2] 1라인 설비 목록
-- 요청자: 한상철 설비보전 파트장 (한결정밀)
--
--   1라인(L1)에 있는 설비 목록 좀 보내 줘요. 설비번호 순으로요.
--
-- 출력 컬럼 : equip_id, equip_name, equip_type
-- 정렬      : equip_id 오름차순
-- ------------------------------------------------------------
-- 저장 후 터미널에서  python play.py check   (결과만 보기: python play.py run)
-- 막히면            python play.py hint    (테이블 구조: python play.py schema)
-- ============================================================

select
    equip_id,
    equip_name,
    equip_type
from equipment
where line_id = L1
order by equip_id;