-- ============================================================
-- [티켓 1-4] 커넥터 제품만
-- 요청자: 최동욱 영업팀장 (한결정밀)
--
--   커넥터 제품만 따로 보고 싶어요. 이름에 '커넥터'가 들어간 거요.
--
-- 출력 컬럼 : product_id, product_name
-- 정렬      : 자유 (순서 무관)
-- ------------------------------------------------------------
-- 저장 후 터미널에서  python play.py check   (결과만 보기: python play.py run)
-- 막히면            python play.py hint    (테이블 구조: python play.py schema)
-- ============================================================

select
    product_id,
    product_name
from products
where product_name LIKE '%커넥터%';


-- select * from products;

