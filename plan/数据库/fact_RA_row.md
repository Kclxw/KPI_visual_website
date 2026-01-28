=好，**继续**。下面是 **RA ROW** 的**完整落库方案报告**，格式、严谨度与 IFIR ROW / IFIR DETAIL 完全一致，且**严格遵循你已经确认的前提**：

* `PLANT_OLD` 与 `PLANT` **语义一致** → 入库统一字段名 `plant`
* **ROW 表无天然业务主键**
* 采用 **自增 id + content_hash（内容哈希）** 保证唯一性
* **RA 的时间主轴是 Claim_month**
* `Mach_type` 字段 **保留但当前不作为分析口径**

---

# RA ROW 表落库方案报告

## 1) 目标与定位

**RA ROW** 是 RA 指标的**月度汇总事实表**，每一行表示在某一索赔月下、某一产品与组织口径的 **RA 分子 / 分母聚合结果**，用于：

* 计算 RA（RA CLAIM / RA MM）
* 支撑按 **月 → ODM / Segment / Model** 的趋势分析
* 作为 RA 下钻到 RA DETAIL 的**唯一入口表**

特点：

* 来自聚合结果
* 不存在天然稳定业务主键
* 同一组合在不同批次导出中可能重复出现

因此采用工程上最稳妥的方式：
**自增 id 作为物理主键 + content_hash 作为业务唯一键**

---

## 2) 源字段全量落库（RA row.xlsx 全部字段）

RA row.xlsx 一共包含 **14 个字段**：

1. `Claim_month`
2. `BRAND`
3. `GEO`
4. `Product_line`
5. `Segment`
6. `SERIES`
7. `Model`
8. `Supplier_NEW`
9. `PLANT_OLD`
10. `Mach_type`
11. `RA CLAIM`
12. `RA MM`
13. `Year`
14. `Month`

---

## 3) 字段设计：字段名、类型、解释（匹配 Excel 数据形态）

> 数据形态核对结论：
>
> * `Claim_month`：月首日期（DATE）
> * `RA CLAIM / RA MM / Year / Month`：Excel 中为 float，但**值全为整数**
> * `Supplier_NEW`：存在空值
> * `PLANT_OLD`：字符串，与 IFIR 中 `PLANT` 语义一致

### 建议 MySQL 字段设计（snake_case）

| 入库字段名        | 源列名          | 类型(MySQL)    |           允许空 | 解释                    |
| ------------ | ------------ | ------------ | ------------: | --------------------- |
| id           | —            | BIGINT       |            NO | 自增主键                  |
| content_hash | —            | CHAR(32)     |            NO | 行内容唯一哈希（MD5）          |
| claim_month  | Claim_month  | DATE         |           YES | 索赔归属月（RA 时间主轴）        |
| brand        | BRAND        | VARCHAR(32)  |           YES | 品牌                    |
| geo          | GEO          | VARCHAR(16)  |           YES | 地区                    |
| product_line | Product_line | VARCHAR(32)  |           YES | 产品线                   |
| segment      | Segment      | VARCHAR(64)  |           YES | 业务段                   |
| series       | SERIES       | VARCHAR(128) |           YES | 系列                    |
| model        | Model        | VARCHAR(128) |           YES | 机型                    |
| plant        | PLANT_OLD    | VARCHAR(64)  |           YES | 工厂（与 DETAIL.PLANT 同义） |
| supplier_new | Supplier_NEW | VARCHAR(128) |           YES | ODM（空值统一转 `'None'`）   |
| mach_type    | Mach_type    | VARCHAR(64)  |           YES | 平台字段（暂不作为分析口径）        |
| ra_claim     | INT          | NO           |         RA 分子 |                       |
| ra_mm        | INT          | NO           |         RA 分母 |                       |
| year_ignore  | SMALLINT     | YES          | 年份溯源字段（不参与统计） |                       |
| month_ignore | TINYINT      | YES          | 月份溯源字段（不参与统计） |                       |

---

## 4) 主键与唯一值设计

### 4.1 物理主键

* `id BIGINT AUTO_INCREMENT PRIMARY KEY`

### 4.2 业务唯一性（幂等导入）

* `content_hash CHAR(32) UNIQUE`

### 4.3 content_hash 计算规则（RA ROW）

**参与 hash 的字段（顺序固定）：**

* claim_month
* brand
* geo
* product_line
* segment
* series
* model
* plant
* supplier_new
* mach_type
* ra_claim
* ra_mm
* year_ignore
* month_ignore

**规范化规则（与 IFIR ROW 完全一致）：**

1. 日期 → `YYYY-MM-DD`
2. 文本 → `trim`，空值 → `'None'`
3. 数值 → 强制转整数文本（避免 `15` vs `15.0`）
4. 用 `|` 拼接后 MD5

---

## 5) 建表 SQL（MySQL）

```sql
CREATE TABLE fact_ra_row (
  id BIGINT NOT NULL AUTO_INCREMENT,
  content_hash CHAR(32) NOT NULL,

  claim_month DATE NULL,
  brand VARCHAR(32) NULL,
  geo VARCHAR(16) NULL,
  product_line VARCHAR(32) NULL,
  segment VARCHAR(64) NULL,
  series VARCHAR(128) NULL,
  model VARCHAR(128) NULL,

  plant VARCHAR(64) NULL,
  supplier_new VARCHAR(128) NULL,
  mach_type VARCHAR(64) NULL,

  ra_claim INT NOT NULL,
  ra_mm INT NOT NULL,

  year_ignore SMALLINT NULL,
  month_ignore TINYINT NULL,

  src_file VARCHAR(255) NULL,
  etl_batch_id VARCHAR(64) NULL,
  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_content_hash (content_hash),

  KEY idx_month_odm_model (claim_month, supplier_new, model),
  KEY idx_month_segment (claim_month, segment),
  KEY idx_odm_plant (supplier_new, plant),
  KEY idx_month_plant (claim_month, plant)
);
```

---

## 6) ETL 示意代码（Python / pandas）

```python
import pandas as pd
import hashlib

def norm_text(x):
    if pd.isna(x):
        return "None"
    return str(x).strip()

def norm_int(x):
    if pd.isna(x):
        return "None"
    return str(int(float(x)))

def norm_date(x):
    if pd.isna(x):
        return "None"
    return pd.to_datetime(x).date().isoformat()

def make_hash(row):
    parts = [
        norm_date(row["claim_month"]),
        norm_text(row["brand"]),
        norm_text(row["geo"]),
        norm_text(row["product_line"]),
        norm_text(row["segment"]),
        norm_text(row["series"]),
        norm_text(row["model"]),
        norm_text(row["plant"]),
        norm_text(row["supplier_new"]),
        norm_text(row["mach_type"]),
        norm_int(row["ra_claim"]),
        norm_int(row["ra_mm"]),
        norm_int(row["year_ignore"]),
        norm_int(row["month_ignore"]),
    ]
    raw = "|".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

df = pd.read_excel("RA row.xlsx")

df = df.rename(columns={
    "Claim_month": "claim_month",
    "BRAND": "brand",
    "GEO": "geo",
    "Product_line": "product_line",
    "Segment": "segment",
    "SERIES": "series",
    "Model": "model",
    "PLANT_OLD": "plant",
    "Supplier_NEW": "supplier_new",
    "Mach_type": "mach_type",
    "RA CLAIM": "ra_claim",
    "RA MM": "ra_mm",
    "Year": "year_ignore",
    "Month": "month_ignore",
})

df["supplier_new"] = df["supplier_new"].fillna("None").astype(str).str.strip()
df["ra_claim"] = df["ra_claim"].astype(int)
df["ra_mm"] = df["ra_mm"].astype(int)

df["content_hash"] = df.apply(make_hash, axis=1)
```

---

## 7) 这张表在你系统中的实际作用

* **RA KPI 计算**：
  `SUM(ra_claim) / SUM(ra_mm)`（按你选定的维度）
* **趋势分析**：
  `claim_month` 为横轴
* **ODM 下钻**：
  `supplier_new → plant → RA DETAIL`
* **Segment / Model 分析**：
  完全对齐 IFIR 的分析结构，逻辑一致
