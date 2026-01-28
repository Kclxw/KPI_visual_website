-- ============================================================
-- ODM到PLANT映射种子数据
-- 来源: plan/数据库/ODM.json
-- 日期: 2026-01-26
-- ============================================================

USE kpi_visual;

-- 清空旧数据
TRUNCATE TABLE map_odm_to_plant;

-- ============================================================
-- IFIR 映射数据
-- ============================================================
INSERT INTO map_odm_to_plant (kpi_type, supplier_new, plant) VALUES
-- BOE
('IFIR', 'BOE', 'BOE'),
('IFIR', 'BOE', 'BOEKT-SZH'),
('IFIR', 'BOE', 'BOEVT-HF'),
('IFIR', 'BOE', 'DAEWOO-WH'),
('IFIR', 'BOE', 'None'),
('IFIR', 'BOE', 'TECHCOM-QUANTA'),
('IFIR', 'BOE', 'TPV-GORZOW'),
('IFIR', 'BOE', 'WISTRON-ZS'),
-- BOE/HUNTKEY
('IFIR', 'BOE/HUNTKEY', 'BOE'),
('IFIR', 'BOE/HUNTKEY', 'HUNKEY-HF'),
('IFIR', 'BOE/HUNTKEY', 'LINXEE-BJ'),
('IFIR', 'BOE/HUNTKEY', 'None'),
('IFIR', 'BOE/HUNTKEY', 'TPV'),
-- BOE/TPV
('IFIR', 'BOE/TPV', 'BOE'),
('IFIR', 'BOE/TPV', 'TPV'),
-- DAEWOO
('IFIR', 'DAEWOO', 'DAEWOO-WH'),
('IFIR', 'DAEWOO', 'None'),
('IFIR', 'DAEWOO', 'SAMSUNG-TJ'),
-- FOXCONN
('IFIR', 'FOXCONN', 'FOXCONN-CQ'),
('IFIR', 'FOXCONN', 'HUNKEY-HF'),
('IFIR', 'FOXCONN', 'HYP'),
('IFIR', 'FOXCONN', 'None'),
('IFIR', 'FOXCONN', 'TPV'),
('IFIR', 'FOXCONN', 'USI-TW'),
-- FOXCONN/HUNTKEY
('IFIR', 'FOXCONN/HUNTKEY', 'FOXCONN-CQ'),
('IFIR', 'FOXCONN/HUNTKEY', 'HUNKEY-HF'),
('IFIR', 'FOXCONN/HUNTKEY', 'None'),
('IFIR', 'FOXCONN/HUNTKEY', 'TPV'),
-- FOXCONN/HUNTKEY/TPV
('IFIR', 'FOXCONN/HUNTKEY/TPV', 'FOXCONN-CQ'),
('IFIR', 'FOXCONN/HUNTKEY/TPV', 'HUNKEY-HF'),
('IFIR', 'FOXCONN/HUNTKEY/TPV', 'TPV'),
-- FOXCONN/TPV
('IFIR', 'FOXCONN/TPV', 'FOXCONN-CQ'),
('IFIR', 'FOXCONN/TPV', 'None'),
('IFIR', 'FOXCONN/TPV', 'TPV'),
('IFIR', 'FOXCONN/TPV', 'TPV-BJ'),
-- HUNKEY
('IFIR', 'HUNKEY', 'HUNKEY-HF'),
('IFIR', 'HUNKEY', 'None'),
-- HUNTKEY
('IFIR', 'HUNTKEY', 'HUNKEY-HF'),
('IFIR', 'HUNTKEY', 'None'),
-- HUNTKEY/TPV/FOXCONN
('IFIR', 'HUNTKEY/TPV/FOXCONN', 'HUNKEY-HF'),
('IFIR', 'HUNTKEY/TPV/FOXCONN', 'TPV'),
-- HYP
('IFIR', 'HYP', 'HYP'),
('IFIR', 'HYP', 'None'),
-- HYP/TPV
('IFIR', 'HYP/TPV', 'HYP'),
('IFIR', 'HYP/TPV', 'TPV'),
-- INX
('IFIR', 'INX', 'None'),
('IFIR', 'INX', 'SAMSUNG-TJ'),
-- LENOVO
('IFIR', 'LENOVO', 'None'),
-- LINXEE
('IFIR', 'LINXEE', 'LINXEE-BJ'),
-- SAMSUNG
('IFIR', 'SAMSUNG', 'None'),
('IFIR', 'SAMSUNG', 'SAMSUNG-TJ'),
-- SAMSUNG/INX
('IFIR', 'SAMSUNG/INX', 'SAMSUNG-TJ'),
-- TPV
('IFIR', 'TPV', 'None'),
('IFIR', 'TPV', 'TPV'),
('IFIR', 'TPV', 'TPV-BJ'),
('IFIR', 'TPV', 'TPV-GORZOW'),
-- TPV/FOXCONN
('IFIR', 'TPV/FOXCONN', 'FOXCONN-CQ'),
('IFIR', 'TPV/FOXCONN', 'None'),
('IFIR', 'TPV/FOXCONN', 'TPV'),
-- TPV/HUNTKEY
('IFIR', 'TPV/HUNTKEY', 'HUNKEY-HF'),
('IFIR', 'TPV/HUNTKEY', 'TPV'),
-- USI
('IFIR', 'USI', 'USI-TW'),
-- None
('IFIR', 'None', 'HYP'),
('IFIR', 'None', 'None'),
('IFIR', 'None', 'TPV');

-- ============================================================
-- RA 映射数据
-- ============================================================
INSERT INTO map_odm_to_plant (kpi_type, supplier_new, plant) VALUES
-- 3NOD
('RA', '3NOD', '3NOD-SZ'),
-- BOE
('RA', 'BOE', 'BOE'),
('RA', 'BOE', 'BOEKT-SZH'),
('RA', 'BOE', 'BOEVT-HF'),
('RA', 'BOE', 'FOXCONN-CQ'),
('RA', 'BOE', 'HUNKEY-HF'),
('RA', 'BOE', 'HYP'),
('RA', 'BOE', 'LINXEE-BJ'),
('RA', 'BOE', 'None'),
('RA', 'BOE', 'QISDA-SZ'),
('RA', 'BOE', 'SAMSUNG-TJ'),
('RA', 'BOE', 'TECHCOM-QUANTA'),
('RA', 'BOE', 'TPV'),
('RA', 'BOE', 'TPV-BJ'),
('RA', 'BOE', 'TPV-GORZOW'),
('RA', 'BOE', 'USI-TW'),
('RA', 'BOE', 'WISTRON-ZS'),
-- BUD
('RA', 'BUD', 'BUD'),
-- CMI
('RA', 'CMI', 'CMI'),
-- DAEWOO
('RA', 'DAEWOO', 'DAEWOO-WH'),
-- FOXCONN
('RA', 'FOXCONN', 'FOXCONN-CQ'),
('RA', 'FOXCONN', 'HUNKEY-HF'),
('RA', 'FOXCONN', 'HYP'),
('RA', 'FOXCONN', 'None'),
('RA', 'FOXCONN', 'TPV'),
('RA', 'FOXCONN', 'TPV-BJ'),
('RA', 'FOXCONN', 'USI-TW'),
-- HACHENG
('RA', 'HACHENG', 'HACHENG'),
-- HUNKEY
('RA', 'HUNKEY', 'HUNKEY-HF'),
('RA', 'HUNKEY', 'None'),
-- HUNTKEY
('RA', 'HUNTKEY', 'HUNKEY-HF'),
('RA', 'HUNTKEY', 'None'),
-- HYP
('RA', 'HYP', 'HYP'),
('RA', 'HYP', 'None'),
-- INX
('RA', 'INX', 'None'),
('RA', 'INX', 'SAMSUNG-TJ'),
-- LENOVO
('RA', 'LENOVO', 'None'),
-- LINXEE
('RA', 'LINXEE', 'LINXEE-BJ'),
-- QISDA
('RA', 'QISDA', 'DAEWOO-WH'),
('RA', 'QISDA', 'QISDA-SZ'),
('RA', 'QISDA', 'None'),
('RA', 'QISDA', 'WISTRON-ZS'),
-- SAMSUNG
('RA', 'SAMSUNG', 'None'),
('RA', 'SAMSUNG', 'SAMSUNG-TJ'),
-- TPV
('RA', 'TPV', 'None'),
('RA', 'TPV', 'TPV'),
('RA', 'TPV', 'TPV-BJ'),
('RA', 'TPV', 'TPV-GORZOW'),
-- USI
('RA', 'USI', 'USI-TW'),
-- WISTRON
('RA', 'WISTRON', 'WISTRON-ZS'),
-- YON
('RA', 'YON', 'YON'),
-- ZAL
('RA', 'ZAL', 'ZAL'),
-- None
('RA', 'None', 'None'),
('RA', 'None', 'TPV');

-- ============================================================
-- 验证
-- ============================================================
SELECT kpi_type, COUNT(DISTINCT supplier_new) AS odm_count, COUNT(*) AS mapping_count
FROM map_odm_to_plant
GROUP BY kpi_type;

SELECT 'ODM mapping seed data loaded!' AS message;
