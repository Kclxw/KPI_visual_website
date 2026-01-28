下面是一份可直接放进项目文档的 **IFIR ROW 表落库方案报告**，包含字段设计、唯一值策略、以及示意代码（ETL 计算 content_hash，建表 SQL）。

---

# IFIR ROW 表落库方案报告

## 1. 目标与定位

IFIR ROW 是 IFIR 指标的月度汇总事实表，主要用于：

1. 计算 IFIR（分子与分母）
2. 支撑按 月，ODM，Segment，Model 的趋势与对比分析
3. 为后续下钻到 IFIR DETAIL 提供筛选入口（例如按月、按工厂、按机型）

特点：

* ROW 表来自聚合结果，天然不保证存在稳定业务主键
* 需要支持幂等导入（同一批数据重复导入不能产生重复行）
* 需要能够稳定定位某一行记录（便于排查与溯源）

因此采用：**自增 id 作为物理主键 + 内容哈希作为业务唯一键**。

---

## 2. 源字段全量落库与字段解释

源文件：IFIR ROW.xlsx
字段共 14 列，全部落库。

| Excel 字段       | 入库字段名          | 类型建议         | 解释                     |
| -------------- | -------------- | ------------ | ---------------------- |
| Delivery_month | delivery_month | DATE         | 出货月（月首日），IFIR 的时间主轴    |
| BRAND          | brand          | VARCHAR(32)  | 品牌                     |
| GEO            | geo            | VARCHAR(16)  | 地区，例如 PRC              |
| Product_line   | product_line   | VARCHAR(32)  | 产品线                    |
| Segment        | segment        | VARCHAR(64)  | 业务段                    |
| SERIES         | series         | VARCHAR(128) | 系列                     |
| Model          | model          | VARCHAR(128) | 机型                     |
| PLANT          | plant          | VARCHAR(64)  | 工厂                     |
| Mach_type      | mach_type      | VARCHAR(64)  | 平台字段，当前阶段不作为核心分析口径，但保留 |
| Supplier_NEW   | supplier_new   | VARCHAR(128) | ODM，空值统一转为 None        |
| BOX CLAIM      | box_claim      | INT          | IFIR 分子，事件数，整数         |
| BOX MM         | box_mm         | INT          | IFIR 分母，出货量或基数，整数      |
| YEAR           | year_ignore    | SMALLINT     | 溯源字段，不参与统计             |
| MONTH          | month_ignore   | TINYINT      | 溯源字段，不参与统计             |

说明：

* `BOX CLAIM` 与 `BOX MM` 在 Excel 中可能以浮点读入，但值形态为整数，落库使用 INT
* `YEAR` 与 `MONTH` 明确为不参与统计字段，建议字段名加 ignore 避免误用
* `Supplier_NEW` 允许源数据为空，但落库时统一存为字符串 `None`，便于查询一致性

---

## 3. 主键与唯一值设计

### 3.1 主键

* `id` BIGINT AUTO_INCREMENT
  用途：稳定引用某一行，便于日志、报表、异常定位。

### 3.2 唯一值

ROW 表无稳定业务主键，采用：

* `content_hash` CHAR(32) NOT NULL UNIQUE

用途：

* 幂等导入
* 去重
* 用内容定位同一条记录

### 3.3 content_hash 计算规则

使用 MD5，对一行记录的关键字段进行规范化后拼接计算。

参与哈希的字段建议包含全部源字段，保证稳定：

* delivery_month
* brand
* geo
* product_line
* segment
* series
* model
* plant
* mach_type
* supplier_new
* box_claim
* box_mm
* year_ignore
* month_ignore

规范化规则：

1. 日期统一格式 `YYYY-MM-DD`，只保留日期，不带时间
2. 文本字段 trim 去空格
3. 空值统一替换为 `None`
4. 数字字段统一转为整数文本，避免 15 与 15.0 产生不同哈希
5. 用固定分隔符 `|` 拼接

---

## 4. 建表 SQL 示例（MySQL）

```sql
CREATE TABLE fact_ifir_row (
  id BIGINT NOT NULL AUTO_INCREMENT,
  content_hash CHAR(32) NOT NULL,

  delivery_month DATE NULL,
  brand VARCHAR(32) NULL,
  geo VARCHAR(16) NULL,
  product_line VARCHAR(32) NULL,
  segment VARCHAR(64) NULL,
  series VARCHAR(128) NULL,
  model VARCHAR(128) NULL,
  plant VARCHAR(64) NULL,
  mach_type VARCHAR(64) NULL,
  supplier_new VARCHAR(128) NULL,

  box_claim INT NOT NULL,
  box_mm INT NOT NULL,

  year_ignore SMALLINT NULL,
  month_ignore TINYINT NULL,

  src_file VARCHAR(255) NULL,
  etl_batch_id VARCHAR(64) NULL,
  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_content_hash (content_hash),

  KEY idx_month_odm_model (delivery_month, supplier_new, model),
  KEY idx_month_segment (delivery_month, segment),
  KEY idx_odm_plant (supplier_new, plant),
  KEY idx_month_plant (delivery_month, plant)
);
```

说明：

* `idx_month_odm_model` 支撑 ODM 层 月 → ODM → Model 趋势
* `idx_month_segment` 支撑 Segment 层趋势
* `idx_odm_plant` 支撑 ODM 下钻时的工厂集合过滤
* `idx_month_plant` 支撑按月按工厂去找明细入口

---

## 5. ETL 示意代码（计算 content_hash 并写入库）

### 5.1 Python 示例（pandas）

```python
import pandas as pd
import hashlib

def norm_text(x):
    if pd.isna(x):
        return "None"
    return str(x).strip()

def norm_int(x):
    if pd.isna(x) or x == "":
        return "None"
    # 兼容 Excel 读入的 15.0
    return str(int(float(x)))

def norm_date(x):
    if pd.isna(x):
        return "None"
    # pandas Timestamp 或 datetime
    return pd.to_datetime(x).date().isoformat()

def make_hash(row):
    parts = [
        norm_date(row["delivery_month"]),
        norm_text(row["brand"]),
        norm_text(row["geo"]),
        norm_text(row["product_line"]),
        norm_text(row["segment"]),
        norm_text(row["series"]),
        norm_text(row["model"]),
        norm_text(row["plant"]),
        norm_text(row["mach_type"]),
        norm_text(row["supplier_new"]),
        norm_int(row["box_claim"]),
        norm_int(row["box_mm"]),
        norm_int(row["year_ignore"]),
        norm_int(row["month_ignore"]),
    ]
    raw = "|".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

df = pd.read_excel("IFIR ROW.xlsx")

# 字段名对齐
df = df.rename(columns={
    "Delivery_month": "delivery_month",
    "BRAND": "brand",
    "GEO": "geo",
    "Product_line": "product_line",
    "Segment": "segment",
    "SERIES": "series",
    "Model": "model",
    "PLANT": "plant",
    "Mach_type": "mach_type",
    "Supplier_NEW": "supplier_new",
    "BOX CLAIM": "box_claim",
    "BOX MM": "box_mm",
    "YEAR": "year_ignore",
    "MONTH": "month_ignore",
})

# supplier_new 空值转 None
df["supplier_new"] = df["supplier_new"].fillna("None").astype(str).str.strip()

# 数值字段转 int
df["box_claim"] = df["box_claim"].fillna(0).astype(int)
df["box_mm"] = df["box_mm"].fillna(0).astype(int)

# 计算 content_hash
df["content_hash"] = df.apply(make_hash, axis=1)

# 写入数据库时用 INSERT IGNORE 或 ON DUPLICATE KEY UPDATE 实现幂等
```

### 5.2 MySQL 幂等写入示意

方案 A，忽略重复：

```sql
INSERT IGNORE INTO fact_ifir_row (
  content_hash, delivery_month, brand, geo, product_line, segment, series, model,
  plant, mach_type, supplier_new, box_claim, box_mm, year_ignore, month_ignore,
  src_file, etl_batch_id
) VALUES (...);
```

方案 B，重复则更新分子分母与溯源信息：

```sql
INSERT INTO fact_ifir_row (
  content_hash, delivery_month, brand, geo, product_line, segment, series, model,
  plant, mach_type, supplier_new, box_claim, box_mm, year_ignore, month_ignore,
  src_file, etl_batch_id
) VALUES (...)
ON DUPLICATE KEY UPDATE
  box_claim = VALUES(box_claim),
  box_mm = VALUES(box_mm),
  src_file = VALUES(src_file),
  etl_batch_id = VALUES(etl_batch_id),
  load_ts = CURRENT_TIMESTAMP;
```