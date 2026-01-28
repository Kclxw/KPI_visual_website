好，**继续（jixu）**。下面是你这套体系里**最后一张、也是你之前反复强调“不能乱来”的关键表**：
👉 **ODM → PLANT 映射表**。
我会非常克制，只做你**已经确认且必要的事情**。

---

# map_odm_to_plant 表落库方案报告

## 1) 这张表为什么必须存在（而且只能这么存在）

你之前已经把逻辑说得非常清楚，我先**复述你认可的事实逻辑**，确认我们在同一页上：

> **正确的分析链路是：**
>
> 1. KPI **只能在 ROW 表中计算**（IFIR ROW / RA ROW）
> 2. ODM 只存在于 **ROW 层**（Supplier_NEW）
> 3. DETAIL 表 **没有 ODM 概念，只有 PLANT**
> 4. 因此：
>
> **ODM 下钻 DETAIL ≠ 直接在 DETAIL 按 Supplier_NEW 过滤**
> **而是：**
>
> `ROW（算 KPI） → 选 ODM → 找该 ODM 对应的 PLANT 集合 → 去 DETAIL 按 PLANT + 时间过滤`

👉 这一步 **必须有一张“ODM ↔ PLANT”的桥接表**
👉 而且这张表 **只能从 ROW 表“计算得出”**，不能人工维护

---

## 2) 表的定位与约束

### 表名

**`map_odm_to_plant`**

### 本质

* 不是事实表
* 不是维表
* 是一张 **稳定映射表（Bridge / Mapping Table）**

### 约束原则（非常重要）

* **不做时间维度**
* **不做 KPI**
* **不做去重后的推断**
* **只忠实反映：ROW 表里真实出现过的关系**

---

## 3) 数据来源（只允许这两个）

| KPI 类型 | 来源表             |
| ------ | --------------- |
| IFIR   | `fact_ifir_row` |
| RA     | `fact_ra_row`   |

**禁止**从 DETAIL 表反推 ODM（你已经明确这是错的）。

---

## 4) 字段设计（极简、不可扩展）

> 你之前说得很清楚：
> **PLANT 和 PLANT_OLD 本质一致，只是叫法不同**

因此统一字段名为 `plant`。

### 字段列表

| 字段名          | 类型           | 解释                                  |
| ------------ | ------------ | ----------------------------------- |
| kpi_type     | VARCHAR(16)  | KPI 类型：`IFIR` / `RA`                |
| supplier_new | VARCHAR(128) | ODM 名称（Supplier_NEW），空值统一为 `'None'` |
| plant        | VARCHAR(64)  | 工厂（PLANT / PLANT_OLD）               |
| load_ts      | DATETIME     | 生成时间                                |

---

## 5) 主键设计（明确、不可争议）

### 复合主键（唯一约束）

```text
(kpi_type, supplier_new, plant)
```

解释：

* 同一 KPI 体系下
* 一个 ODM
* 可以对应多个 PLANT
* 但 **同一组合只允许出现一次**

👉 **这张表不需要自增 id**

---

## 6) 建表 SQL（MySQL）

```sql
CREATE TABLE map_odm_to_plant (
  kpi_type VARCHAR(16) NOT NULL,
  supplier_new VARCHAR(128) NOT NULL,
  plant VARCHAR(64) NOT NULL,

  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (kpi_type, supplier_new, plant),

  KEY idx_supplier (supplier_new),
  KEY idx_plant (plant)
);
```

---

## 7) 映射关系的计算方式（只从 ROW 计算）

### IFIR 映射来源

```sql
INSERT IGNORE INTO map_odm_to_plant (kpi_type, supplier_new, plant)
SELECT DISTINCT
  'IFIR' AS kpi_type,
  COALESCE(TRIM(supplier_new), 'None') AS supplier_new,
  TRIM(plant) AS plant
FROM fact_ifir_row
WHERE plant IS NOT NULL;
```

### RA 映射来源

```sql
INSERT IGNORE INTO map_odm_to_plant (kpi_type, supplier_new, plant)
SELECT DISTINCT
  'RA' AS kpi_type,
  COALESCE(TRIM(supplier_new), 'None') AS supplier_new,
  TRIM(plant) AS plant
FROM fact_ra_row
WHERE plant IS NOT NULL;
```

⚠️ 注意：

* **不加时间条件**
* **不加 Model / Segment 条件**
* **只要关系曾经出现过，就保留**

---

## 8) 这张表在真实分析中的用法（非常关键）

### ODM 下钻 IFIR DETAIL（你认可的正确方式）

```sql
-- 1. 在 ROW 算 KPI，选中 ODM
-- 2. 找该 ODM 对应的 PLANT
SELECT plant
FROM map_odm_to_plant
WHERE kpi_type = 'IFIR'
  AND supplier_new = :selected_odm;
```

```sql
-- 3. 用 PLANT + 月份 去 DETAIL
SELECT *
FROM fact_ifir_detail
WHERE delivery_month BETWEEN :m_start AND :m_end
  AND plant IN (:plant_list);
```

RA 完全同理，只是换 `kpi_type = 'RA'` 和 `claim_month`。

