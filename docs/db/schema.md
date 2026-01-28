# 数据库Schema设计文档

> **版本**: v1.1  
> **数据库**: MySQL 8.0+  
> **更新日期**: 2026-01-26  
> **设计来源**: plan/数据库/*.md

---

## 一、数据库概览

### 1.1 数据库信息

- **数据库名**: kpi_visual
- **字符集**: utf8mb4
- **排序规则**: utf8mb4_unicode_ci

### 1.2 表清单

| 表名 | 说明 | 粒度 | 主键策略 |
|------|------|------|----------|
| fact_ifir_row | IFIR月度聚合表 | 出货月x维度组合 | 自增id + content_hash |
| fact_ifir_detail | IFIR事件明细表 | 单条索赔事件 | claim_nbr |
| fact_ra_row | RA月度聚合表 | 索赔月x维度组合 | 自增id + content_hash |
| fact_ra_detail | RA事件明细表 | 单条维修事件 | claim_nbr |
| map_odm_to_plant | ODM工厂映射表 | ODMxPlant | 复合主键 |
| upload_task | 上传任务表 | 单次上传任务 | 自增id |

### 1.3 核心设计原则

1. **ROW表无天然业务主键** - 采用自增id + content_hash(MD5)保证唯一性
2. **DETAIL表有业务主键** - 采用claim_nbr作为主键，入库前去重
3. **YEAR/MONTH字段** - 命名为year_ignore/month_ignore，明确不参与统计
4. **ODM映射表** - 复合主键(kpi_type, supplier_new, plant)，只从ROW表计算

---

## 二、fact_ifir_row 表

**来源**: plan/数据库/fact_IFIR_row.md

**用途**: 
- 计算IFIR（分子BOX CLAIM / 分母BOX MM）
- 支撑按月、ODM、Segment、Model的趋势分析

**唯一性**: content_hash (MD5哈希，包含全部14个源字段)

| 字段名 | 类型 | 说明 | Excel映射 |
|--------|------|------|-----------|
| id | BIGINT | 自增主键 | - |
| content_hash | CHAR(32) | 内容哈希 | - |
| delivery_month | DATE | 出货月(IFIR时间主轴) | Delivery_month |
| brand | VARCHAR(32) | 品牌 | BRAND |
| geo | VARCHAR(16) | 地区 | GEO |
| product_line | VARCHAR(32) | 产品线 | Product_line |
| segment | VARCHAR(64) | 业务段 | Segment |
| series | VARCHAR(128) | 系列 | SERIES |
| model | VARCHAR(128) | 机型 | Model |
| plant | VARCHAR(64) | 工厂 | PLANT |
| mach_type | VARCHAR(64) | 平台字段 | Mach_type |
| supplier_new | VARCHAR(128) | ODM(空值转None) | Supplier_NEW |
| box_claim | INT | IFIR分子 | BOX CLAIM |
| box_mm | INT | IFIR分母 | BOX MM |
| year_ignore | SMALLINT | 溯源字段 | YEAR |
| month_ignore | TINYINT | 溯源字段 | MONTH |

---

## 三、fact_ifir_detail 表

**来源**: plan/数据库/fact_IFIR_detail.md

**主键**: claim_nbr（入库前去重）

**去重规则**:
1. 优先保留claim_date更晚的一行
2. 若相同，优先保留lastsln非空/文本更完整的行

共36个字段，分为7组：
- A.时间: claim_nbr, claim_month, claim_date, delivery_month, delivery_day
- B.区域: geo_2012, financial_region, plant
- C.产品: brand, segment, segment2, style, series, model, mtm, serial_nbr
- D.服务: stationname, station_id, data_source, lastsln
- E.故障: failure_code, fault_category, mach_desc, problem_descr, problem_descr_by_tech
- F.零部件: commodity, down_part_code, part_nbr, part_desc, part_supplier, part_barcode, packing_lot_no
- G.索赔: claim_item_nbr, claim_status, channel, cust_nbr

---

## 四、fact_ra_row 表

**来源**: plan/数据库/fact_RA_row.md

**关键差异**:
- 时间主轴是claim_month（索赔月），不是delivery_month
- PLANT_OLD入库统一字段名为plant
- KPI指标为ra_claim / ra_mm

---

## 五、map_odm_to_plant 表

**来源**: plan/数据库/map_odm_to_plant.md

**本质**: 稳定映射表（Bridge Table）

**约束**:
- 不做时间维度
- 不从DETAIL反推
- 只忠实反映ROW表里真实出现过的关系

**主键**: (kpi_type, supplier_new, plant)

---

## 六、ODM下钻正确方式

```sql
-- 1. 在ROW算KPI，选中ODM
-- 2. 找该ODM对应的PLANT
SELECT plant FROM map_odm_to_plant
WHERE kpi_type = 'IFIR' AND supplier_new = :odm;

-- 3. 用PLANT + 月份去DETAIL
SELECT * FROM fact_ifir_detail
WHERE delivery_month BETWEEN :start AND :end
  AND plant IN (:plant_list);
```

---

## 七、脚本文件

```
scripts/db/
  init.sql               # 建表DDL
  seed_odm_mapping.sql   # ODM映射种子数据
```
