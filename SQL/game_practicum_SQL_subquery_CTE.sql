/* Проект «Секреты Тёмнолесья»
 * Цель проекта: изучить влияние характеристик игроков и их игровых персонажей 
 * на покупку внутриигровой валюты «райские лепестки», а также оценить 
 * активность игроков при совершении внутриигровых покупок
 * 
 * Автор: Лукинова Диана
 * Дата: 25.09.2025
*/

-- Часть 1. Исследовательский анализ данных
-- Задача 1. Исследование доли платящих игроков

-- 1.1. Доля платящих пользователей по всем данным:
SELECT COUNT(u.id) AS total_users,
SUM(payer) AS paying_users,
SUM(payer)::real / COUNT(u.id) AS paying_users_share
FROM fantasy.users AS u
ORDER BY paying_users_share DESC;

-- 1.2. Доля платящих пользователей в разрезе расы персонажа:
SELECT r.race,
SUM(payer) AS paying_users_race,
COUNT(id) AS users_race,
SUM(payer)::REAL / COUNT(id) AS paying_users_race_share
FROM fantasy.users AS u
LEFT JOIN fantasy.race AS r ON r.race_id = u.race_id
GROUP BY r.race
ORDER BY paying_users_race_share DESC;

-- Задача 2. Исследование внутриигровых покупок
-- 2.1. Статистические показатели по полю amount:
SELECT COUNT(*) AS total_buying,
SUM(amount) AS total_amount,
MIN(amount) AS min_amount,
MAX(amount) AS max_amount,
AVG(amount) AS avg_amount,
PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY amount) AS median,
STDDEV(amount) AS stddev
FROM fantasy.events;

-- 2.2: Аномальные нулевые покупки:
SELECT COUNT(*) AS zero_amount,
COUNT(*)::real / (SELECT COUNT(*) FROM fantasy.events) AS zero_amount_share
FROM fantasy.events
WHERE amount = 0;

-- 2.3: Популярные эпические предметы:
SELECT i.game_items,
COUNT(e.item_code) AS item,
(SELECT COUNT(item_code) FROM fantasy.events WHERE amount <> 0) AS total_items,
COUNT(e.item_code) / (SELECT COUNT(item_code) FROM fantasy.events WHERE amount <> 0)::REAL AS item_share,
COUNT(DISTINCT e.id)::REAL / (SELECT COUNT(DISTINCT id) FROM fantasy.events WHERE amount <> 0) AS share_of_people
FROM fantasy.events AS e
LEFT JOIN fantasy.items AS i ON e.item_code = i.item_code
WHERE e.amount <> 0
GROUP BY i.game_items
ORDER BY share_of_people DESC;

-- Часть 2. Решение ad hoc-задачbи
-- Задача: Зависимость активности игроков от расы персонажа:
WITH number_of_reg_us AS (
SELECT u.race_id,
COUNT(*) AS total_users
FROM fantasy.users AS u
GROUP BY u.race_id
),
race_stat AS (
SELECT u.race_id,
COUNT(DISTINCT e.id) AS buying_users,
COUNT(DISTINCT u.id) FILTER (WHERE u.payer = 1)::REAL 
            / COUNT(DISTINCT e.id) AS payer_users_share,
SUM(e.amount) AS total_amount
FROM fantasy.events AS e
LEFT JOIN fantasy.users AS u ON u.id = e.id
WHERE e.amount <> 0
GROUP BY u.race_id
),
tot_ord_stat AS (
SELECT u.race_id,
COUNT(DISTINCT e.transaction_id) AS total_orders
FROM fantasy.events AS e
LEFT JOIN fantasy.users AS u ON u.id = e.id
WHERE e.amount <> 0
GROUP BY u.race_id
)
SELECT race,
n.total_users,
buying_users,
buying_users::REAL / n.total_users AS buying_share,
payer_users_share,
total_orders::real / buying_users AS avg_number_of_purch,
total_amount::REAL / buying_users AS avg_amount_of_purch,
total_amount::REAL / total_orders AS avg_sum_amount
FROM number_of_reg_us AS n
LEFT JOIN race_stat USING(race_id)
JOIN tot_ord_stat USING(race_id)
JOIN fantasy.race USING(race_id)
ORDER BY avg_number_of_purch DESC;