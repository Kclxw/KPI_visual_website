# IFIR Model分析页 - 报告导出设计

## 一、页面现状

**路径**: `frontend/src/pages/ifir/ModelAnalysisPage.vue`
**组件**: `frontend/src/components/kpi/ifir/model/ModelCard.vue`
**API**: `POST /ifir/model-analysis/analyze`

### 筛选参数
| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| time_range | {start_month, end_month} | 是 | 如 "2024-07" ~ "2025-06" |
| models | string[] | 是 | 如 ["ThinkPad X1 Carbon", "ThinkPad T14"] |
| segments | string[] | 否 | 如 ["Consumer"] |
| odms | string[] | 否 | 如 ["Wistron"] |
| tgt | number | 否 | 前端TGT目标值(DPPM)，默认1500 |

### 页面内容结构
- **Block D** (多Model时): 多Model趋势对比图 + 数据矩阵表 + 饼图
- **每个Model卡片**:
  - Block A: IFIR趋势折线图 (支持年度对比/完整趋势)
  - Block B: Top Issue表格 (汇总 + 月度)
  - Block C: AI分析总结

## 二、Excel报告结构

### Sheet 1: `报告信息`

| 单元格 | 内容 |
|--------|------|
| A1 | **IFIR Model分析报告** |
| A3 | 数据截至: {data_as_of} |
| A4 | 分析时间范围: {start_month} ~ {end_month} |
| A5 | 分析Model: {model1, model2, ...} |
| A6 | 筛选Segment: {全部 或 具体值} |
| A7 | 筛选ODM: {全部 或 具体值} |
| A8 | TGT目标: {tgt} DPPM |
| A9 | 报告生成时间: {now} |

### Sheet 2: `趋势数据`

**表头**: Month | {Model1} IFIR(DPPM) | {Model2} IFIR(DPPM) | ...

每行一个月份，每列一个Model的IFIR DPPM值。

| Month | ThinkPad X1 Carbon (DPPM) | ThinkPad T14 (DPPM) |
|-------|--------------------------|---------------------|
| 2024-07 | 1,234 | 2,345 |
| 2024-08 | 1,100 | 2,100 |
| ... | ... | ... |

**额外行**:
- 末行附加 TGT 参考值行（如用户设置了TGT）

**嵌入图表**: 在表格下方（约第20行起）嵌入matplotlib生成的趋势对比图PNG
- 图表内容：多Model折线图 + TGT目标线 + 图例
- 图表尺寸：约800×400px

### Sheet 3: `Top Issue汇总`

**每个Model一个子表**（通过空行分隔，并有Model标题行）：

| Model | Rank | Issue (fault_category) | Count | Share(%) |
|-------|------|------------------------|-------|----------|
| ThinkPad X1 Carbon | 1 | LCD Issue | 45 | 23.5% |
| ThinkPad X1 Carbon | 2 | Battery Issue | 30 | 15.7% |
| ... | ... | ... | ... | ... |

### Sheet 4: `月度Top Issue`

**表头**: Month | Model | Rank | Issue | Count | Share(%)

将所有Model的所有月份的Top Issue展开为flat表格：

| Month | Model | Rank | Issue | Count | Share(%) |
|-------|-------|------|-------|-------|----------|
| 2025-06 | ThinkPad X1 Carbon | 1 | LCD Issue | 12 | 28.6% |
| 2025-06 | ThinkPad X1 Carbon | 2 | Battery | 8 | 19.0% |
| 2025-05 | ThinkPad X1 Carbon | 1 | LCD Issue | 10 | 25.0% |
| ... | ... | ... | ... | ... | ... |

### Sheet 5: `Detail明细数据`

**数据来源**: `fact_ifir_detail` 表
**筛选条件**: 与当前分析页面完全一致（time_range + models + segments + odms→plant映射）

**不做 issue 过滤** — 导出所有选中Model在时间范围内的完整Detail数据。

| 列名 | 数据库字段 | 说明 |
|------|-----------|------|
| Claim_Nbr | claim_nbr | 索赔单号 |
| Claim_Month | claim_month | 索赔月份 |
| Delivery_Month | delivery_month | 出货月份（IFIR时间轴） |
| Model | model | 机型 |
| Segment | segment | 产品线段 |
| Plant | plant | 工厂 |
| Fault_Category | fault_category | 故障大类（Top Issue来源） |
| Problem_Descr_by_Tech | problem_descr_by_tech | 技术员问题描述 |
| Failure_Code | failure_code | 故障代码 |
| MTM | mtm | 机器类型号 |
| Serial_Nbr | serial_nbr | 序列号 |
| Geo | geo_2012 | 地理区域 |
| Commodity | commodity | 零件大类 |
| Part_Nbr | part_nbr | 零件号 |
| Part_Desc | part_desc | 零件描述 |
| Part_Supplier | part_supplier | 零件供应商 |

### Sheet 6: `多Model对比` (仅多Model时生成)

**汇总饼图数据**:

| Model | IFIR(DPPM) | Share(%) | BOX_CLAIM | BOX_MM |
|-------|-----------|----------|-----------|--------|
| ThinkPad X1 Carbon | 1,234 | 45.2% | 56 | 45,000 |
| ThinkPad T14 | 890 | 32.6% | 40 | 45,000 |

**嵌入图表**: 饼图（各Model的IFIR占比）

## 三、matplotlib 图表规格

### 3.1 趋势对比图

```
类型: 折线图
X轴: 月份 (YYYY-MM)
Y轴: DPPM (值 = ifir × 1,000,000)
线条: 每个Model一条线 + TGT目标线(红色虚线)
颜色: 使用与前端一致的配色 ['#5470c6', '#91cc75', '#fac858', '#ee6666', ...]
样式: 平滑曲线, 圆形数据点
图例: 右上角
DPI: 150
尺寸: 10×5 英寸
```

### 3.2 饼图 (多Model时)

```
类型: 环形图 (donut)
数据: 各Model的IFIR DPPM值
标签: Model名称 + 占比%
颜色: 同上配色方案
DPI: 150
尺寸: 8×6 英寸
```

## 四、后端新增接口

```
POST /ifir/report/model
```

**请求体**: 复用现有 `IfirModelAnalyzeRequest` 结构 + 额外参数

```python
class IfirModelReportRequest(BaseModel):
    time_range: TimeRange
    filters: IfirModelFilters   # models(必选) + segments + odms
    tgt: Optional[int] = 1500   # TGT目标值(DPPM)

# 响应: Excel文件流 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
```

**后端处理流程**:
1. 复用 `IfirService.analyze_model()` 获取分析数据（趋势 + Top Issue + 月度明细）
2. 新增 `IfirService.get_model_details_for_report()` 获取全量Detail数据（无分页，按models + time_range + segments + odms过滤）
3. matplotlib 生成趋势图 + 饼图 → 临时PNG
4. openpyxl 构建Excel（6个Sheet + 嵌入图表）
5. StreamingResponse 返回文件

## 五、前端改动

在 `ModelAnalysisPage.vue` 的结果区域底部添加按钮：

```vue
<el-button 
  type="success" 
  :icon="Download"
  :loading="exporting"
  :disabled="!showResult"
  @click="handleExport"
>
  生成报告
</el-button>
```

点击后调用 `POST /ifir/report/model`，接收Blob并触发下载。
