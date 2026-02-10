кол/* Проект первого модуля: анализ данных для агентства недвижимости
 * 
 * Автор: Лукинова Диана
 * Дата: 10.10.2025
*/


-- Задача 1: Время активности объявлений
-- Определим аномальные значения (выбросы) по значению перцентилей:
WITH limits AS (
    SELECT
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats
),
-- Найдём id объявлений, которые не содержат выбросы, также оставим пропущенные данные:
filtered_id AS(
    SELECT id
    FROM real_estate.flats
    WHERE
        total_area < (SELECT total_area_limit FROM limits)
        AND (rooms < (SELECT rooms_limit FROM limits) OR rooms IS NULL)
        AND (balcony < (SELECT balcony_limit FROM limits) OR balcony IS NULL)
        AND ((ceiling_height < (SELECT ceiling_height_limit_h FROM limits)
            AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)) OR ceiling_height IS NULL)
    )
SELECT
CASE 
        WHEN a.days_exposition <= 30 THEN '1-30 days'
        WHEN a.days_exposition <= 90 THEN '31-90 days'
        WHEN a.days_exposition <= 180 THEN '91-180 days'
        WHEN a.days_exposition > 180 THEN '181+ days'
            ELSE 'active'
      END AS category,
CASE 
        WHEN city_id = '6X8I' THEN 'Санкт-Петербург'
            ELSE 'Ленинградская область'
      END AS place,
COUNT (f.id),
COUNT(*) / SUM(COUNT(*)) OVER() AS share_total,
COUNT(*) / SUM(COUNT(*)) OVER(PARTITION BY CASE 
        WHEN city_id = '6X8I' THEN 'Санкт-Петербург'
            ELSE 'Ленинградская область'
      END) AS share_region,
AVG(a.last_price / total_area) AS avg_price_for_1_metr,
AVG(total_area) AS avg_total_area,
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rooms) AS median_room_number,
AVG(rooms) AS avg_room_number,
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.balcony ) AS median_balcony_number,
AVG(balcony) AS avg_balcony_number
FROM filtered_id AS fi
LEFT JOIN real_estate.advertisement AS a USING (id)
LEFT JOIN real_estate.flats AS f USING (id)
WHERE type_id = 'F8EM' AND a.first_day_exposition BETWEEN DATE('2015-01-01') AND DATE('2018-12-31') --только города и только 2015-2018 годы
GROUP BY category, place
ORDER BY place, category, count DESC;


-- Задача 2: Сезонность объявлений
-- Определим аномальные значения (выбросы) по значению перцентилей:
WITH limits AS (
    SELECT
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_area) AS total_area_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY rooms) AS rooms_limit,
        PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY balcony) AS balcony_limit,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_h,
        PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY ceiling_height) AS ceiling_height_limit_l
    FROM real_estate.flats
),
-- Найдём id объявлений, которые не содержат выбросы, также оставим пропущенные данные:
filtered_id AS(
    SELECT id
    FROM real_estate.flats
    WHERE
        total_area < (SELECT total_area_limit FROM limits)
        AND (rooms < (SELECT rooms_limit FROM limits) OR rooms IS NULL)
        AND (balcony < (SELECT balcony_limit FROM limits) OR balcony IS NULL)
        AND ((ceiling_height < (SELECT ceiling_height_limit_h FROM limits)
            AND ceiling_height > (SELECT ceiling_height_limit_l FROM limits)) OR ceiling_height IS NULL)
    ),
adv_open AS (
SELECT EXTRACT(MONTH FROM a.first_day_exposition) AS month_name,
COUNT(*) AS op_count,
AVG(a.last_price / f.total_area) AS op_avg_price_for_1_metr,
AVG(f.total_area) AS op_avg_total_area
FROM filtered_id AS fi
LEFT JOIN real_estate.advertisement AS a ON a.id = fi.id
LEFT JOIN real_estate.flats AS f ON fi.id = f.id
WHERE EXTRACT(YEAR FROM a.first_day_exposition) >= 2015 AND EXTRACT(YEAR FROM a.first_day_exposition) <= 2018 AND type_id = 'F8EM' -- только города
GROUP BY month_name
),
adv_clos AS (
SELECT EXTRACT(MONTH FROM a.first_day_exposition + a.days_exposition::int) AS month_name,
COUNT(*) AS cl_count,
AVG(a.last_price / f.total_area) AS cl_avg_price_for_1_metr,
AVG(f.total_area) AS cl_avg_total_area
FROM filtered_id AS fi
LEFT JOIN real_estate.advertisement AS a ON a.id = fi.id
LEFT JOIN real_estate.flats AS f ON fi.id = f.id
WHERE EXTRACT(YEAR FROM a.first_day_exposition) >= 2015 AND EXTRACT(YEAR FROM a.first_day_exposition) <= 2018 AND a.days_exposition IS NOT NULL AND type_id = 'F8EM' -- только города
GROUP BY month_name
)
SELECT adv_open.month_name,
CASE 
		WHEN adv_open.month_name = 1  THEN 'Январь'
		WHEN adv_open.month_name = 2  THEN 'Февраль'
		WHEN adv_open.month_name = 3  THEN 'Март'
		WHEN adv_open.month_name = 4  THEN 'Апрель'
		WHEN adv_open.month_name = 5  THEN 'Май'
		WHEN adv_open.month_name = 6  THEN 'Июнь'
		WHEN adv_open.month_name = 7  THEN 'Июль'
		WHEN adv_open.month_name = 8  THEN 'Август'
		WHEN adv_open.month_name = 9  THEN 'Сентябрь'
		WHEN adv_open.month_name = 10 THEN 'Октябрь'
		WHEN adv_open.month_name = 11 THEN 'Ноябрь'
		WHEN adv_open.month_name = 12 THEN 'Декабрь' 
	END AS month_name_str,
op_count,
op_count / SUM(op_count) OVER() AS open_share,
RANK() over(ORDER BY op_count DESC) AS rank_op,
cl_count,
cl_count / SUM(cl_count) OVER() AS closed_share,
RANK() over(ORDER BY cl_count DESC) AS rank_cl,
ROUND(op_avg_price_for_1_metr::NUMERIC, 2) AS op_avg_price_for_1_metr,
ROUND(op_avg_total_area::NUMERIC, 2) AS op_avg_total_area,
ROUND(cl_avg_price_for_1_metr::NUMERIC, 2) AS cl_avg_price_for_1_metr,
ROUND(cl_avg_total_area::NUMERIC, 2) AS cl_avg_total_area
FROM adv_open
FULL JOIN adv_clos ON adv_open.month_name = adv_clos.month_name
ORDER BY adv_open.month_name;





    