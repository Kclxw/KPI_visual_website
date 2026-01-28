下面是 **IFIR DETAIL（你写的 DERAIL 我按 DETAIL 理解）** 的**完整落库方案报告**（全字段、类型匹配、字段解释、主键为 `Claim_Nbr`，并按你要求“你会在入库前去重”来设计）。

---

# IFIR DETAIL 表落库方案报告（主键 = Claim_Nbr）

## 1) 目标与定位

**IFIR DETAIL** 是 IFIR 指标的事件级明细表（逐条索赔/故障事件）。每行代表一次进入系统的 claim/incident，用于：

* 从 IFIR ROW 的 KPI 结果下钻到事件明细
* 解释原因：Top Issue、Top Part、Top Plant、Top Station
* 为 AI 总结提供文本与追溯字段（Problem/LastSln/Part 等）

---

## 2) 数据粒度与口径

* **粒度**：事件级（claim）
* **核心时间轴（下钻口径）**：`Delivery_Month`（出货月）
* **事件识别号**：`Claim_Nbr`

> 你已明确：入库前你会去重，因此本表以 `Claim_Nbr` 作为主键是可行的。

---

## 3) 主键与唯一性策略

### 3.1 主键（PK）

* **`Claim_Nbr` 作为 PRIMARY KEY**

### 3.2 入库前去重规则（建议写进 ETL 规范）

当同一个 `Claim_Nbr` 出现多行时，建议保留策略固定化，避免每次结果不同：

* 优先保留 `Claim_Date` 更晚的一行（如果存在）
* 若 `Claim_Date` 相同或为空：

  * 优先保留 `LastSln` 非空、文本更完整的一行
  * 再不行按源文件顺序取第一行

---

## 4) 源字段全量落库（Excel 全部字段，共 36 列）

以下字段来自 IFIR DETAIL.xlsx，全部落库（字段名建议转为 snake_case；括号内为源列名）：

---

## 5) 字段设计：字段名、类型、解释（匹配 Excel 数据形态）

> 说明：
>
> * 日期类字段落 `DATE`
> * 类似 `Station_ID`、`Delivery_Day` 在 Excel 常读成 float，但实际应为整数，落库用 `INT/TINYINT`
> * 长文本 `LastSln` 落 `TEXT`

### A. 主键与时间维度

| 字段名（入库）        | 源列名            | 类型(MySQL)            | 解释                      |
| -------------- | -------------- | -------------------- | ----------------------- |
| claim_nbr      | Claim_Nbr      | VARCHAR(64) NOT NULL | **主键**：索赔单号/事件号         |
| claim_month    | Claim_Month    | DATE NULL            | 索赔归属月（月首日）              |
| claim_date     | Claim_Date     | DATE NULL            | 索赔/事件日期                 |
| delivery_month | Delivery_Month | DATE NULL            | 出货/交付月（月首日），IFIR 下钻主时间轴 |
| delivery_day   | Delivery_Day   | TINYINT NULL         | 出货日（1–31）               |

---

### B. 区域与组织维度

| 字段名              | 源列名              | 类型               | 解释      |
| ---------------- | ---------------- | ---------------- | ------- |
| geo_2012         | Geo_2012         | VARCHAR(32) NULL | 地理大区口径  |
| financial_region | Financial Region | VARCHAR(64) NULL | 财务口径区域  |
| plant            | PLANT            | VARCHAR(64) NULL | 工厂/生产基地 |

---

### C. 产品归属维度

| 字段名        | 源列名        | 类型                | 解释                   |
| ---------- | ---------- | ----------------- | -------------------- |
| brand      | Brand      | VARCHAR(64) NULL  | 品牌                   |
| segment    | Segment    | VARCHAR(64) NULL  | 业务段                  |
| segment2   | Segment2   | VARCHAR(64) NULL  | 子业务段                 |
| style      | Style      | VARCHAR(64) NULL  | 产品大类                 |
| series     | Series     | VARCHAR(128) NULL | 系列                   |
| model      | Model      | VARCHAR(128) NULL | 型号                   |
| mtm        | MTM        | VARCHAR(64) NULL  | MTM 机型编码             |
| serial_nbr | Serial_Nbr | VARCHAR(64) NULL  | 序列号（同一 SN 可多次 claim） |

---

### D. 制造/服务追溯维度

| 字段名         | 源列名         | 类型                | 解释             |
| ----------- | ----------- | ----------------- | -------------- |
| stationname | StationName | VARCHAR(255) NULL | 服务站名称          |
| station_id  | Station_ID  | INT NULL          | 服务站 ID（数值型）    |
| data_source | Data_Source | VARCHAR(32) NULL  | 数据来源系统         |
| lastsln     | LastSln     | TEXT NULL         | 最后处理/解决信息（长文本） |

---

### E. 失效与问题描述维度（Issue）

| 字段名                   | 源列名                   | 类型                | 解释        |
| --------------------- | --------------------- | ----------------- | --------- |
| failure_code          | Failure_Code          | VARCHAR(32) NULL  | 标准失效代码    |
| fault_category        | Fault_Category        | VARCHAR(128) NULL | 故障大类      |
| mach_desc             | Mach_Desc             | VARCHAR(255) NULL | 机型描述（更详细） |
| problem_descr         | Problem_Descr         | VARCHAR(255) NULL | 问题描述（报修侧） |
| problem_descr_by_tech | Problem_Descr_by_Tech | VARCHAR(255) NULL | 技术员侧问题描述  |

---

### F. 零部件与供应链维度

| 字段名            | 源列名            | 类型                | 解释        |
| -------------- | -------------- | ----------------- | --------- |
| commodity      | Commodity      | VARCHAR(64) NULL  | 物料/系统归类   |
| down_part_code | Down_Part_Code | VARCHAR(64) NULL  | 下阶/失效部件代码 |
| part_nbr       | Part_Nbr       | VARCHAR(64) NULL  | 部件号       |
| part_desc      | Part_desc      | VARCHAR(255) NULL | 部件描述      |
| part_supplier  | Part_Supplier  | VARCHAR(128) NULL | 供应商       |
| part_barcode   | Part_Barcode   | VARCHAR(64) NULL  | 部件条码      |
| packing_lot_no | Packing_Lot_No | VARCHAR(64) NULL  | 批次/包装批号   |

---

### G. 索赔单与客户维度

| 字段名            | 源列名            | 类型               | 解释   |
| -------------- | -------------- | ---------------- | ---- |
| claim_item_nbr | Claim_Item_Nbr | VARCHAR(64) NULL | 索赔行号 |
| claim_status   | Claim_Status   | VARCHAR(32) NULL | 索赔状态 |
| channel        | Channel        | VARCHAR(32) NULL | 渠道   |
| cust_nbr       | Cust_Nbr       | VARCHAR(64) NULL | 客户编号 |

---

## 6) 建表 SQL（MySQL）

```sql
CREATE TABLE fact_ifir_detail (
  claim_nbr VARCHAR(64) NOT NULL,

  claim_month DATE NULL,
  claim_date DATE NULL,
  delivery_month DATE NULL,
  delivery_day TINYINT NULL,

  geo_2012 VARCHAR(32) NULL,
  financial_region VARCHAR(64) NULL,
  plant VARCHAR(64) NULL,

  brand VARCHAR(64) NULL,
  segment VARCHAR(64) NULL,
  segment2 VARCHAR(64) NULL,
  style VARCHAR(64) NULL,
  series VARCHAR(128) NULL,
  model VARCHAR(128) NULL,
  mtm VARCHAR(64) NULL,
  serial_nbr VARCHAR(64) NULL,

  stationname VARCHAR(255) NULL,
  station_id INT NULL,
  data_source VARCHAR(32) NULL,
  lastsln TEXT NULL,

  failure_code VARCHAR(32) NULL,
  fault_category VARCHAR(128) NULL,
  mach_desc VARCHAR(255) NULL,
  problem_descr VARCHAR(255) NULL,
  problem_descr_by_tech VARCHAR(255) NULL,

  commodity VARCHAR(64) NULL,
  down_part_code VARCHAR(64) NULL,
  part_nbr VARCHAR(64) NULL,
  part_desc VARCHAR(255) NULL,
  part_supplier VARCHAR(128) NULL,
  part_barcode VARCHAR(64) NULL,
  packing_lot_no VARCHAR(64) NULL,

  claim_item_nbr VARCHAR(64) NULL,
  claim_status VARCHAR(32) NULL,
  channel VARCHAR(32) NULL,
  cust_nbr VARCHAR(64) NULL,

  load_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (claim_nbr),

  KEY idx_delivery_month_plant (delivery_month, plant),
  KEY idx_delivery_month_model (delivery_month, model),
  KEY idx_segment_month (segment, delivery_month),
  KEY idx_issue (fault_category),
  KEY idx_part (part_nbr)
);
```

---

## 7) ETL 示意代码（去重后以 Claim_Nbr 写入）

```python
import pandas as pd

df = pd.read_excel("IFIR DETAIL.xlsx")

# 1) 统一字段名（示意）
df = df.rename(columns={
    "Claim_Nbr": "claim_nbr",
    "Claim_Month": "claim_month",
    "Claim_Date": "claim_date",
    "Delivery_Month": "delivery_month",
    "Delivery_Day": "delivery_day",
    "Geo_2012": "geo_2012",
    "Financial Region": "financial_region",
    "PLANT": "plant",
    "Brand": "brand",
    "Segment": "segment",
    "Segment2": "segment2",
    "Style": "style",
    "Series": "series",
    "Model": "model",
    "MTM": "mtm",
    "Serial_Nbr": "serial_nbr",
    "StationName": "stationname",
    "Station_ID": "station_id",
    "Data_Source": "data_source",
    "LastSln": "lastsln",
    "Failure_Code": "failure_code",
    "Fault_Category": "fault_category",
    "Mach_Desc": "mach_desc",
    "Problem_Descr": "problem_descr",
    "Problem_Descr_by_Tech": "problem_descr_by_tech",
    "Commodity": "commodity",
    "Down_Part_Code": "down_part_code",
    "Part_Nbr": "part_nbr",
    "Part_desc": "part_desc",
    "Part_Supplier": "part_supplier",
    "Part_Barcode": "part_barcode",
    "Packing_Lot_No": "packing_lot_no",
    "Claim_Item_Nbr": "claim_item_nbr",
    "Claim_Status": "claim_status",
    "Channel": "channel",
    "Cust_Nbr": "cust_nbr",
})

# 2) 类型处理（日期/整数）
for c in ["claim_month","claim_date","delivery_month"]:
    df[c] = pd.to_datetime(df[c], errors="coerce").dt.date

df["delivery_day"] = pd.to_numeric(df["delivery_day"], errors="coerce").astype("Int64")
df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce").astype("Int64")

# 3) 去掉 claim_nbr 为空的行（主键必需）
df = df[df["claim_nbr"].notna()].copy()
df["claim_nbr"] = df["claim_nbr"].astype(str).str.strip()

# 4) 入库前去重：按 claim_date 最新优先，其次 lastsln 非空优先
df["claim_date_sort"] = pd.to_datetime(df["claim_date"], errors="coerce")
df["lastsln_len"] = df["lastsln"].fillna("").astype(str).str.len()

df = (
    df.sort_values(["claim_nbr","claim_date_sort","lastsln_len"], ascending=[True, False, False])
      .drop_duplicates(subset=["claim_nbr"], keep="first")
      .drop(columns=["claim_date_sort","lastsln_len"])
)

# 5) 写入数据库：用 REPLACE 或 INSERT ... ON DUPLICATE KEY UPDATE
```

---

## 8) 这张表在你的系统里怎么用（对应你核心任务）

* IFIR KPI 趋势：从 `fact_ifir_row` 算
* IFIR 下钻解释：用 `delivery_month + plant (+ model/segment)` 在本表过滤
* Top Issue：按 `fault_category / problem_descr` 聚合
* AI 总结输入：`problem_descr / problem_descr_by_tech / lastsln / part_* / plant / station*`
